"""
Shared OpenAI (GPT-5-nano) extraction client.

This base class owns everything the three extraction services have in common:
the OpenAI call, the JSON-extraction fallbacks, retry/backoff, cost tracking,
and metadata assembly. Subclasses only supply the target Pydantic model (and,
optionally, a default system prompt) via a thin domain-specific method.

GPT-5-nano is a reasoning model, so it does NOT accept sampling parameters
(temperature, top_p, etc.) — sending them returns a 400. Deterministic-ish,
low-latency extraction is achieved with reasoning_effort="minimal" plus JSON
response formatting.

Cost (USD per 1M tokens): GPT-5-nano $0.05 input ($0.005 cached) / $0.40 output.
Docs: https://developers.openai.com/api/docs/models/gpt-5-nano
"""

import os
import json
import time
from typing import Any, Dict, Optional, Tuple, Type
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ValidationError

from shared.config import get_logger

# Load environment from the monorepo root. __file__ resolves through the per-app
# `shared` symlink to scripts/legacy-ingestion/shared/openai_extractor.py, whose
# parents[3] is the repository root.
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

logger = get_logger(__name__)

# OpenAI model pricing (USD per million tokens). "input_cached" is the rate for
# prompt-cache hits (90% discount on the gpt-5 family).
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-5-nano": {"input": 0.05, "input_cached": 0.005, "output": 0.40},
}

DEFAULT_MODEL = "gpt-5-nano"
# GPT-5-nano is a reasoning model; "minimal" keeps latency and cost low for
# straightforward extraction/classification tasks.
DEFAULT_REASONING_EFFORT = "minimal"

# Retry backoff: wait grows linearly with each attempt (K * (attempt + 1)).
RATE_LIMIT_BACKOFF_SECONDS = 30
ERROR_BACKOFF_SECONDS = 5


class OpenAIExtractionError(Exception):
    """Raised when extraction fails (after retries, or on invalid model output)."""


class BaseOpenAIExtractor:
    """
    Base GPT-5-nano extraction client.

    Subclasses expose a domain method (e.g. extract_features / extract_demographics)
    that calls self.extract(prompts, TheirPydanticModel).

    Prompt caching: prompts must keep the static system prompt as a byte-stable
    prefix (volatile content only in the user message) so OpenAI's automatic
    prefix caching (≥1024 tokens) hits. Subclasses should set PROMPT_CACHE_KEY
    to a per-service constant — OpenAI combines it with the prefix hash to route
    same-prefix traffic to the same machine, improving hit rates.
    """

    # Per-service prompt-cache routing key (override in subclasses).
    PROMPT_CACHE_KEY: Optional[str] = None

    def __init__(self, api_key: Optional[str] = None, prompt_cache_key: Optional[str] = None):
        """
        Args:
            api_key: OpenAI API key (defaults to the OPENAI_API_KEY env var).
            prompt_cache_key: cache-routing key (defaults to the class's
                PROMPT_CACHE_KEY).

        Raises:
            ValueError: if no API key is available.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. Set it in your .env file. "
                "Get a key at: https://platform.openai.com/api-keys"
            )
        # `is None` (not `or`) so an explicit "" can disable a subclass's key
        self.prompt_cache_key = (
            prompt_cache_key if prompt_cache_key is not None else self.PROMPT_CACHE_KEY
        )
        self.client = OpenAI(api_key=self.api_key)
        logger.info("OpenAI client initialized")

    def calculate_cost(
        self, model: str, tokens_input: int, tokens_output: int, tokens_input_cached: int = 0
    ) -> float:
        """
        Return the USD cost of a call given token counts.

        `tokens_input` is the TOTAL prompt tokens (cache hits included);
        `tokens_input_cached` is the cached subset, billed at the discounted rate.
        """
        pricing = MODEL_PRICING.get(model, MODEL_PRICING[DEFAULT_MODEL])
        tokens_input_cached = min(tokens_input_cached or 0, tokens_input)
        tokens_input_uncached = tokens_input - tokens_input_cached
        return (
            (tokens_input_uncached / 1_000_000) * pricing["input"]
            + (tokens_input_cached / 1_000_000) * pricing.get("input_cached", pricing["input"])
            + (tokens_output / 1_000_000) * pricing["output"]
        )

    def extract(
        self,
        prompts: "tuple[str, str] | str",
        response_model: Type[BaseModel],
        *,
        default_system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
    ) -> Tuple[BaseModel, Dict[str, Any]]:
        """
        Run a structured extraction and validate it against `response_model`.

        Args:
            prompts: either (system_prompt, user_prompt) or just the user prompt.
            response_model: the Pydantic model to validate the JSON output into.
            default_system_prompt: system prompt to use when `prompts` is a bare
                string (ignored when `prompts` is a tuple).
            model: model id (defaults to gpt-5-nano).
            max_retries: attempts before giving up.

        Returns:
            (validated model instance, metadata dict).

        Raises:
            OpenAIExtractionError: on invalid output or after exhausting retries.
        """
        if model is None:
            model = DEFAULT_MODEL

        messages = self._build_messages(prompts, default_system_prompt)

        # Steer same-prefix requests to the same cache shard when a key is set.
        cache_kwargs: Dict[str, Any] = (
            {"prompt_cache_key": self.prompt_cache_key} if self.prompt_cache_key else {}
        )

        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    reasoning_effort=DEFAULT_REASONING_EFFORT,
                    response_format={"type": "json_object"},
                    **cache_kwargs,
                )
                processing_time_ms = int((time.time() - start_time) * 1000)

                response_text = response.choices[0].message.content
                if not response_text:
                    # Empty/None content (e.g. content filter or length cutoff);
                    # treat as transient and let the retry loop handle it.
                    raise ValueError("Empty response content from model")

                extracted_data = self._parse_json(response_text)
                result = response_model(**extracted_data)

                tokens_input = response.usage.prompt_tokens
                tokens_output = response.usage.completion_tokens
                # Prompt-cache hits (usage.prompt_tokens_details.cached_tokens);
                # tracked so cost is right and cache regressions are visible in logs.
                # Clamped to total prompt tokens so cost and hit rate stay consistent.
                prompt_details = getattr(response.usage, "prompt_tokens_details", None)
                tokens_input_cached = min(
                    getattr(prompt_details, "cached_tokens", 0) or 0, tokens_input
                )
                cost_usd = self.calculate_cost(model, tokens_input, tokens_output, tokens_input_cached)
                cache_hit_rate = (tokens_input_cached / tokens_input) if tokens_input else 0.0

                metadata = {
                    "model": model,
                    "cost_usd": cost_usd,
                    "tokens_input": tokens_input,
                    "tokens_input_cached": tokens_input_cached,
                    "tokens_output": tokens_output,
                    "processing_time_ms": processing_time_ms,
                    "raw_response": {
                        "id": response.id,
                        "model": response.model,
                        "content": response_text,
                        "finish_reason": response.choices[0].finish_reason,
                        "usage": {
                            "prompt_tokens": tokens_input,
                            "cached_tokens": tokens_input_cached,
                            "completion_tokens": tokens_output,
                            "total_tokens": getattr(
                                response.usage, "total_tokens", tokens_input + tokens_output
                            ),
                        },
                    },
                }

                logger.info(
                    f"Extraction successful - Model: {model}, Cost: ${cost_usd:.6f}, "
                    f"Tokens: {tokens_input}/{tokens_output} "
                    f"(cached: {tokens_input_cached}, hit rate: {cache_hit_rate:.0%}), "
                    f"Time: {processing_time_ms}ms"
                )
                return result, metadata

            except ValidationError as e:
                # Schema mismatch won't fix itself on retry — fail fast.
                raise OpenAIExtractionError(f"Pydantic validation failed: {e}") from e

            except Exception as e:
                is_rate_limit = "429" in str(e) or "rate limit" in str(e).lower()
                wait_time = (RATE_LIMIT_BACKOFF_SECONDS if is_rate_limit else ERROR_BACKOFF_SECONDS) * (attempt + 1)
                if is_rate_limit:
                    logger.warning(f"Rate limited (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s...")
                else:
                    logger.error(f"OpenAI error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    raise OpenAIExtractionError(f"Extraction failed after {max_retries} retries: {e}") from e

        # Unreachable: the loop above always returns or raises on the last attempt.
        raise OpenAIExtractionError(f"Extraction failed after {max_retries} retries")

    @staticmethod
    def _build_messages(
        prompts: "tuple[str, str] | str", default_system_prompt: Optional[str]
    ) -> list:
        """Build the chat messages from a (system, user) tuple or a bare user prompt."""
        if isinstance(prompts, tuple):
            system_prompt, user_prompt = prompts
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        if default_system_prompt:
            return [
                {"role": "system", "content": default_system_prompt},
                {"role": "user", "content": prompts},
            ]
        return [{"role": "user", "content": prompts}]

    @staticmethod
    def _parse_json(response_text: str) -> Dict[str, Any]:
        """Parse JSON from the model, tolerating ```json fences and surrounding prose."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            # Markdown code fence: ```json ... ```
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                snippet = (response_text[start:end] if end != -1 else response_text[start:]).strip()
                return json.loads(snippet)
            # First "{" .. last "}" anywhere in the text.
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                return json.loads(response_text[start:end])
            raise OpenAIExtractionError(
                f"Failed to parse JSON response: {e}\nResponse: {response_text[:200]}..."
            ) from e
