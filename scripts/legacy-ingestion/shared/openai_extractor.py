"""
Shared extraction client: Muse Spark 1.3 Contributor through OpenRouter.

This base class owns everything the three extraction services have in common:
the LLM call, the JSON-extraction fallbacks, retry/backoff, cost tracking,
validation repair, and metadata assembly. Subclasses supply the target Pydantic
model through a thin domain method, and may override PROMPT_CACHE_KEY,
REASONING_EFFORT, STRUCTURED_OUTPUT, and VALIDATION_REPAIRS (each also settable per
instance through the constructor).

OpenRouter speaks the OpenAI Chat Completions API, so the `openai` SDK is used
with OpenRouter's base URL. OpenRouter-only fields go through `extra_body`.

Reasoning is mandatory on Muse Spark: OpenRouter rejects effort "none" and
defaults to "medium", so each client sends its REASONING_EFFORT explicitly
(default "minimal", the lowest accepted). Muse Spark has no implicit prompt caching, so the system prompt
carries an explicit `cache_control` breakpoint (see _build_messages).

The Contributor tier trains on prompts. The OpenRouter account's privacy
settings must allow training providers for paid models, or every request fails
with "No endpoints found matching your data policy".

Billed cost is read from OpenRouter's `usage.cost`; MODEL_PRICING is the
fallback when a response omits it.
Docs: https://openrouter.ai/meta/muse-spark-1.3-contributor
      https://openrouter.ai/docs/guides/best-practices/prompt-caching
      https://openrouter.ai/docs/guides/best-practices/reasoning-tokens
"""

import copy
import os
import json
import math
import time
from typing import Any, Dict, NamedTuple, Optional, Tuple, Type
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

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model pricing (USD per million tokens), from OpenRouter's model catalog.
# "input_cached" is the rate for prompt-cache hits; "input_cache_write", where a
# model bills cache writes separately, is the rate for tokens written to the
# cache (absent here: Muse Spark lists no write rate, so writes bill as input).
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "meta/muse-spark-1.3-contributor": {
        "input": 0.10,
        "input_cached": 0.002,
        "output": 0.20,
    },
}

DEFAULT_MODEL = "meta/muse-spark-1.3-contributor"
# "minimal" is the lowest effort Muse Spark accepts (reasoning is mandatory, so
# "none" is rejected); it keeps latency and cost low for extraction.
DEFAULT_REASONING_EFFORT = "minimal"

# Most validation errors listed in one repair request; the rest are left out to keep
# the follow-up message short.
MAX_VALIDATION_ERRORS_SHOWN = 20

# Retry backoff: wait grows linearly with each attempt (K * (attempt + 1)).
RATE_LIMIT_BACKOFF_SECONDS = 30
ERROR_BACKOFF_SECONDS = 5


class UsageTokens(NamedTuple):
    """Token counts for one response; cached and written are clamped to the prompt total."""

    input: int
    cached: int
    written: int
    output: int


class OpenAIExtractionError(Exception):
    """Raised when extraction fails (after retries, or on invalid model output)."""


class BaseOpenAIExtractor:
    """
    Base Muse Spark (OpenRouter) extraction client.

    Subclasses expose a domain method (e.g. extract_features / extract_demographics)
    that calls self.extract(prompts, TheirPydanticModel).

    Prompt caching: prompts must keep the static system prompt as a byte-stable
    prefix (volatile content only in the user message). The system message is
    sent with a `cache_control` breakpoint, since Muse Spark caches only
    explicitly. Subclasses should set PROMPT_CACHE_KEY to a per-service
    constant: OpenRouter uses it as the sticky-routing key (when no session_id
    is sent), keeping same-prefix traffic on the provider that holds the cache.
    """

    # Per-service sticky-routing key (override in subclasses).
    PROMPT_CACHE_KEY: Optional[str] = None
    # Reasoning effort sent to OpenRouter; subclasses raise it when accuracy is worth
    # the extra (billed) reasoning tokens.
    REASONING_EFFORT: str = DEFAULT_REASONING_EFFORT
    # When True, response_model is sent as a strict JSON schema, so enums, required
    # fields, and types are enforced while the model decodes. The model must be
    # strict-compatible: no defaults, no free-form dicts, extra="forbid".
    STRUCTURED_OUTPUT: bool = False
    # Validation failures answered with the errors and a request for corrected JSON.
    # 0 fails fast on the first ValidationError. Each repair uses one of max_retries'
    # attempts.
    VALIDATION_REPAIRS: int = 0

    def __init__(
        self,
        api_key: Optional[str] = None,
        prompt_cache_key: Optional[str] = None,
        *,
        reasoning_effort: Optional[str] = None,
        structured_output: Optional[bool] = None,
        validation_repairs: Optional[int] = None,
    ):
        """
        Args:
            api_key: OpenRouter API key (defaults to the OPENROUTER_API_KEY env var).
            prompt_cache_key: cache-routing key (defaults to the class's
                PROMPT_CACHE_KEY).
            reasoning_effort, structured_output, validation_repairs: per-instance
                overrides of the class attributes of the same (uppercase) name.

        Raises:
            ValueError: if no API key is available.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found. Set it in your .env file. "
                "Get a key at: https://openrouter.ai/settings/keys"
            )
        # `is None` (not `or`) so an explicit "" can disable a subclass's key
        self.prompt_cache_key = (
            prompt_cache_key if prompt_cache_key is not None else self.PROMPT_CACHE_KEY
        )
        self.reasoning_effort = reasoning_effort if reasoning_effort is not None else self.REASONING_EFFORT
        self.structured_output = structured_output if structured_output is not None else self.STRUCTURED_OUTPUT
        self.validation_repairs = validation_repairs if validation_repairs is not None else self.VALIDATION_REPAIRS
        self.client = OpenAI(api_key=self.api_key, base_url=OPENROUTER_BASE_URL)
        logger.info("OpenRouter client initialized")

    def calculate_cost(
        self,
        model: str,
        tokens_input: int,
        tokens_output: int,
        tokens_input_cached: int = 0,
        tokens_input_cache_write: int = 0,
    ) -> float:
        """
        Return the USD cost of a call given token counts.

        `tokens_input` is the TOTAL prompt tokens (cache hits and writes included);
        `tokens_input_cached` is the cache-hit subset and `tokens_input_cache_write`
        the cache-write subset, each billed at its own rate.
        """
        pricing = MODEL_PRICING.get(model, MODEL_PRICING[DEFAULT_MODEL])
        tokens_input_cached = min(tokens_input_cached or 0, tokens_input)
        tokens_input_cache_write = min(
            tokens_input_cache_write or 0, tokens_input - tokens_input_cached
        )
        tokens_input_plain = tokens_input - tokens_input_cached - tokens_input_cache_write
        return (
            (tokens_input_plain / 1_000_000) * pricing["input"]
            + (tokens_input_cached / 1_000_000) * pricing.get("input_cached", pricing["input"])
            + (tokens_input_cache_write / 1_000_000)
            * pricing.get("input_cache_write", pricing["input"])
            + (tokens_output / 1_000_000) * pricing["output"]
        )

    def extract(
        self,
        prompts: "tuple[str, str] | str",
        response_model: Type[BaseModel],
        *,
        default_system_prompt: Optional[str] = None,
        max_retries: int = 3,
    ) -> Tuple[BaseModel, Dict[str, Any]]:
        """
        Run a structured extraction and validate it against `response_model`.

        Args:
            prompts: either (system_prompt, user_prompt) or just the user prompt.
            response_model: the Pydantic model to validate the JSON output into.
            default_system_prompt: system prompt to use when `prompts` is a bare
                string (ignored when `prompts` is a tuple).
            max_retries: attempts before giving up.

        Returns:
            (validated model instance, metadata dict).

        Raises:
            OpenAIExtractionError: on invalid output or after exhausting retries.
        """
        # One model only: supported reasoning efforts differ per model, so the
        # model is not a per-call choice.
        model = DEFAULT_MODEL

        base_messages = self._build_messages(prompts, default_system_prompt)
        messages = base_messages

        # Keep same-prefix requests on the provider holding the cache when a key is set.
        cache_kwargs: Dict[str, Any] = (
            {"prompt_cache_key": self.prompt_cache_key} if self.prompt_cache_key else {}
        )
        response_format: Dict[str, Any] = (
            {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "strict": True,
                    "schema": build_strict_json_schema(response_model),
                },
            }
            if self.structured_output
            else {"type": "json_object"}
        )
        repairs_left = self.validation_repairs
        # Earlier calls in this extraction whose output was not used (sent back for
        # repair, unparseable, or empty): billed, so their cost, tokens, and time are
        # added to the successful call's.
        unused_cost_usd = 0.0
        unused_tokens = UsageTokens(0, 0, 0, 0)
        unused_time_ms = 0

        def count_unused(response: Any, elapsed_ms: int) -> None:
            nonlocal unused_cost_usd, unused_tokens, unused_time_ms
            unused_cost_usd += self._compute_response_cost(model, response)[0]
            unused_tokens = UsageTokens(*(a + b for a, b in zip(unused_tokens, self._read_usage(response.usage))))
            unused_time_ms += elapsed_ms

        for attempt in range(max_retries):
            response = None
            processing_time_ms = 0
            try:
                start_time = time.time()
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_format=response_format,
                    # OpenRouter's unified reasoning control. exclude=True drops the
                    # reasoning text from the response; its tokens are still billed.
                    extra_body={
                        "reasoning": {"effort": self.reasoning_effort, "exclude": True}
                    },
                    **cache_kwargs,
                )
                processing_time_ms = int((time.time() - start_time) * 1000)

                response_text = response.choices[0].message.content
                if not response_text:
                    # Empty/None content (e.g. content filter or length cutoff);
                    # treat as transient and let the retry loop handle it.
                    raise ValueError("Empty response content from model")

                extracted_data = self._parse_json(response_text)
                try:
                    result = response_model(**extracted_data)
                except ValidationError as e:
                    if repairs_left <= 0 or attempt == max_retries - 1:
                        raise
                    repairs_left -= 1
                    count_unused(response, processing_time_ms)
                    logger.warning(f"Validation failed, asking the model to repair: {e.error_count()} error(s)")
                    messages = self._build_repair_messages(base_messages, response_text, e)
                    continue

                final = self._read_usage(response.usage)
                cost_usd, cost_source = self._compute_response_cost(model, response)
                cost_usd += unused_cost_usd
                tokens_input, tokens_input_cached, tokens_input_cache_write, tokens_output = (
                    a + b for a, b in zip(final, unused_tokens)
                )
                processing_time_ms += unused_time_ms
                cache_hit_rate = (final.cached / final.input) if final.input else 0.0

                metadata = {
                    "model": model,
                    "cost_usd": cost_usd,
                    "cost_source": cost_source,
                    "tokens_input": tokens_input,
                    "tokens_input_cached": tokens_input_cached,
                    "tokens_input_cache_write": tokens_input_cache_write,
                    "tokens_output": tokens_output,
                    "processing_time_ms": processing_time_ms,
                    "validation_repairs": self.validation_repairs - repairs_left,
                    "raw_response": {
                        "id": response.id,
                        "model": response.model,
                        "content": response_text,
                        "finish_reason": response.choices[0].finish_reason,
                        # This response's own usage; the top-level cost and token
                        # counts also include earlier calls whose output went unused.
                        "usage": {
                            "prompt_tokens": final.input,
                            "cached_tokens": final.cached,
                            "cache_write_tokens": final.written,
                            "completion_tokens": final.output,
                            "total_tokens": getattr(
                                response.usage, "total_tokens", final.input + final.output
                            ),
                        },
                    },
                }

                logger.info(
                    f"Extraction successful - Model: {model}, Cost: ${cost_usd:.6f} ({cost_source}), "
                    f"Tokens: {tokens_input}/{tokens_output} "
                    f"(cached: {tokens_input_cached}, written: {tokens_input_cache_write}, "
                    f"hit rate: {cache_hit_rate:.0%}), "
                    f"Time: {processing_time_ms}ms"
                )
                return result, metadata

            except ValidationError as e:
                # Out of validation repairs (or none configured): a plain retry would
                # resend the same request, so fail fast.
                raise OpenAIExtractionError(f"Pydantic validation failed: {e}") from e

            except Exception as e:
                if response is not None and getattr(response, "usage", None) is not None:
                    count_unused(response, processing_time_ms)
                is_rate_limit = "429" in str(e) or "rate limit" in str(e).lower()
                wait_time = (RATE_LIMIT_BACKOFF_SECONDS if is_rate_limit else ERROR_BACKOFF_SECONDS) * (attempt + 1)
                if is_rate_limit:
                    logger.warning(f"Rate limited (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s...")
                else:
                    logger.error(f"OpenRouter error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    raise OpenAIExtractionError(f"Extraction failed after {max_retries} retries: {e}") from e

        # Unreachable: the loop above always returns or raises on the last attempt.
        raise OpenAIExtractionError(f"Extraction failed after {max_retries} retries")

    @staticmethod
    def _read_usage(usage: Any) -> UsageTokens:
        """
        Token counts from a response's usage.

        cached (prompt_tokens_details.cached_tokens) is clamped to the prompt total, and
        written (cache_write_tokens, None or absent on models that bill writes as plain
        input) to the uncached remainder, so cost and hit rate stay consistent.
        """
        details = getattr(usage, "prompt_tokens_details", None)
        prompt = usage.prompt_tokens
        cached = min(getattr(details, "cached_tokens", 0) or 0, prompt)
        written = min(getattr(details, "cache_write_tokens", 0) or 0, prompt - cached)
        return UsageTokens(prompt, cached, written, usage.completion_tokens)

    def _compute_response_cost(self, model: str, response: Any) -> Tuple[float, str]:
        """
        Return (USD cost, source) for one response.

        OpenRouter reports the amount actually charged in usage.cost (USD credits); the
        SDK keeps it as an extra field. Falls back to the price table when it is missing
        or not a usable amount.
        """
        usage = response.usage
        reported_cost = getattr(usage, "cost", None)
        if self._is_billable_amount(reported_cost):
            return float(reported_cost), "openrouter"
        tokens = self._read_usage(usage)
        return (
            self.calculate_cost(model, tokens.input, tokens.output, tokens.cached, tokens.written),
            "estimated",
        )

    @staticmethod
    def _build_repair_messages(base_messages: list, response_text: str, error: ValidationError) -> list:
        """The original conversation plus the invalid answer and its validation errors."""
        errors = "\n".join(
            f"- {'.'.join(str(p) for p in err['loc']) or '(root)'}: {err['msg']}"
            for err in error.errors()[:MAX_VALIDATION_ERRORS_SHOWN]
        )
        return base_messages + [
            {"role": "assistant", "content": response_text},
            {
                "role": "user",
                "content": (
                    "That JSON failed validation:\n"
                    f"{errors}\n"
                    "Return the complete corrected JSON object, changing only what the errors require."
                ),
            },
        ]

    @staticmethod
    def _is_billable_amount(value: Any) -> bool:
        """True for a finite, non-negative number (bool excluded, since bool is an int)."""
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            and value >= 0
        )

    @staticmethod
    def _build_messages(
        prompts: "tuple[str, str] | str", default_system_prompt: Optional[str]
    ) -> list:
        """
        Build the chat messages from a (system, user) tuple or a bare user prompt.

        The system prompt is the static, byte-stable prefix, so it is sent as a
        content block carrying a `cache_control` breakpoint: Muse Spark caches
        only explicitly marked prefixes. The volatile user prompt stays after it.
        """
        if isinstance(prompts, tuple):
            system_prompt, user_prompt = prompts
        else:
            system_prompt, user_prompt = default_system_prompt, prompts
        if not system_prompt:
            return [{"role": "user", "content": user_prompt}]
        return [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}
                ],
            },
            {"role": "user", "content": user_prompt},
        ]

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


def build_strict_json_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """
    Return `model`'s JSON schema with every $ref inlined, for a strict response_format.

    Pydantic already emits what strict mode needs when the model has no defaults and
    forbids extra keys (every property required, additionalProperties false); this only
    removes the $defs indirection, which not every OpenRouter provider resolves.
    """
    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})

    def inline(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                target = copy.deepcopy(defs[node["$ref"].split("/")[-1]])
                extra = {k: v for k, v in node.items() if k != "$ref"}
                return inline({**target, **extra})
            return {k: inline(v) for k, v in node.items()}
        if isinstance(node, list):
            return [inline(v) for v in node]
        return node

    return inline(schema)
