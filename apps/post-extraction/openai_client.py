"""
OpenAI GPT-5-nano client for post feature extraction (replaces Claude/GLM).

Cost comparison (per 1M tokens):
- Claude Sonnet 4: $3.00 / $15.00
- GPT-5-nano:      $0.05 / $0.40

GPT-5-nano is a reasoning model, so it does NOT accept sampling parameters
(temperature, top_p, etc.) — sending them returns a 400. Deterministic-ish,
low-latency extraction is achieved via reasoning_effort="minimal" plus JSON
response formatting.

Docs: https://developers.openai.com/api/docs/models/gpt-5-nano
"""

import os
import json
import time
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from schema import ExtractedFeatures
from shared.config import get_logger

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

logger = get_logger(__name__)

# OpenAI model pricing (USD per million tokens)
MODEL_PRICING = {
    "gpt-5-nano": {"input": 0.05, "output": 0.40},
}

DEFAULT_MODEL = "gpt-5-nano"
# GPT-5-nano is a reasoning model; "minimal" keeps latency and cost low for
# straightforward extraction/classification tasks.
DEFAULT_REASONING_EFFORT = "minimal"

class OpenAIClient:
    """OpenAI GPT-5-nano client for extracting features from Reddit posts."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        self.client = OpenAI(api_key=self.api_key)
        logger.info("OpenAI client initialized")

    def calculate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        pricing = MODEL_PRICING.get(model, MODEL_PRICING[DEFAULT_MODEL])
        return (tokens_input / 1_000_000) * pricing["input"] + (tokens_output / 1_000_000) * pricing["output"]

    def extract_features(self, prompts: tuple[str, str] | str, model: Optional[str] = None, max_retries: int = 3) -> Tuple[ExtractedFeatures, Dict[str, Any]]:
        """
        Extract features using GPT-5-nano.

        Args:
            prompts: Either a tuple of (system_prompt, user_prompt) or just user_prompt string
            model: OpenAI model to use (defaults to gpt-5-nano)
            max_retries: Number of retry attempts on failure

        Returns:
            Tuple of (ExtractedFeatures, metadata_dict)
        """
        if model is None:
            model = DEFAULT_MODEL

        # Handle both old format (single string) and new format (tuple)
        if isinstance(prompts, tuple):
            system_prompt, user_prompt = prompts
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        else:
            user_prompt = prompts
            messages = [{"role": "user", "content": user_prompt}]

        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    reasoning_effort=DEFAULT_REASONING_EFFORT,
                    response_format={"type": "json_object"},
                )
                processing_time_ms = int((time.time() - start_time) * 1000)

                response_text = response.choices[0].message.content
                if not response_text:
                    # Empty/None content (e.g. content filter or length cutoff);
                    # treat as a transient failure and let the retry loop handle it.
                    raise ValueError("Empty response content from model")

                # Parse JSON
                try:
                    extracted_data = json.loads(response_text)
                except json.JSONDecodeError:
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        extracted_data = json.loads(response_text[json_start:json_end].strip())
                    elif "{" in response_text:
                        json_start = response_text.find("{")
                        json_end = response_text.rfind("}") + 1
                        extracted_data = json.loads(response_text[json_start:json_end])
                    else:
                        raise

                features = ExtractedFeatures(**extracted_data)

                tokens_input = response.usage.prompt_tokens
                tokens_output = response.usage.completion_tokens
                cost_usd = self.calculate_cost(model, tokens_input, tokens_output)

                metadata = {
                    "model": model,
                    "cost_usd": cost_usd,
                    "tokens_input": tokens_input,
                    "tokens_output": tokens_output,
                    "processing_time_ms": processing_time_ms,
                    "raw_response": {
                        "id": response.id,
                        "content": response_text,
                        "finish_reason": response.choices[0].finish_reason,
                        "usage": {"prompt_tokens": tokens_input, "completion_tokens": tokens_output}
                    }
                }

                logger.info(f"Extraction successful - Cost: ${cost_usd:.6f}, Tokens: {tokens_input}/{tokens_output}")
                return features, metadata

            except Exception as e:
                is_rate_limit = "429" in str(e) or "rate limit" in str(e).lower()
                if is_rate_limit:
                    wait_time = 30 * (attempt + 1)
                    logger.warning(f"Rate limited (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s...")
                else:
                    wait_time = 5 * (attempt + 1)
                    logger.error(f"OpenAI error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    raise

_client_instance: Optional[OpenAIClient] = None

def get_client() -> OpenAIClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = OpenAIClient()
    return _client_instance
