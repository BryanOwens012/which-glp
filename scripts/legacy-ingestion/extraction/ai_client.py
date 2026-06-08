"""
OpenAI GPT-5-nano client for extracting structured data from Reddit posts/comments.

This module provides a wrapper around the OpenAI SDK with:
- Cost tracking per API call
- Automatic JSON parsing and validation
- Error handling and retries

GPT-5-nano is a reasoning model, so it does NOT accept sampling parameters
(temperature, top_p, etc.) — sending them returns a 400. Deterministic-ish,
low-latency extraction is achieved via reasoning_effort="minimal" plus JSON
response formatting.

Docs: https://developers.openai.com/api/docs/models/gpt-5-nano
"""

import os
import json
import time
from typing import Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

from extraction.schema import ExtractedFeatures
from extraction.prompts import SYSTEM_PROMPT
from shared.config import get_logger

# Load environment variables
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)

# Initialize logger
logger = get_logger(__name__)

# OpenAI model pricing (per million tokens)
MODEL_PRICING = {
    "gpt-5-nano": {
        "input": 0.05,   # $0.05 per MTok
        "output": 0.40,  # $0.40 per MTok
    },
}

# Default model
DEFAULT_MODEL = "gpt-5-nano"
# GPT-5-nano is a reasoning model; "minimal" keeps latency and cost low for
# straightforward extraction/classification tasks.
DEFAULT_REASONING_EFFORT = "minimal"


class AIClientConfigurationError(Exception):
    """Raised when AI client configuration is invalid"""
    pass


class AIExtractionError(Exception):
    """Raised when AI extraction fails"""
    pass


class OpenAIClient:
    """
    Client for the OpenAI GPT-5-nano API with structured data extraction.

    Handles API calls, cost tracking, JSON parsing, and Pydantic validation.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)

        Raises:
            AIClientConfigurationError: If API key is missing
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise AIClientConfigurationError(
                "OpenAI API key not found.\n"
                "Please set OPENAI_API_KEY in your .env file.\n"
                "Get your API key at: https://platform.openai.com/api-keys"
            )

        self.client = OpenAI(api_key=self.api_key)
        logger.info("OpenAI client initialized")

    def calculate_cost(
        self,
        model: str,
        tokens_input: int,
        tokens_output: int
    ) -> float:
        """
        Calculate cost in USD for an API call.

        Args:
            model: Model identifier
            tokens_input: Number of input tokens
            tokens_output: Number of output tokens

        Returns:
            Cost in USD
        """
        if model not in MODEL_PRICING:
            logger.warning(f"Unknown model {model}, using gpt-5-nano pricing")
            pricing = MODEL_PRICING[DEFAULT_MODEL]
        else:
            pricing = MODEL_PRICING[model]

        cost_input = (tokens_input / 1_000_000) * pricing["input"]
        cost_output = (tokens_output / 1_000_000) * pricing["output"]

        return cost_input + cost_output

    def extract_features(
        self,
        prompts: tuple[str, str] | str,
        model: Optional[str] = None,
        max_retries: int = 3
    ) -> Tuple[ExtractedFeatures, dict]:
        """
        Extract structured features from a Reddit post/comment.

        Args:
            prompts: Either a tuple of (system_prompt, user_prompt) or just user_prompt string
            model: OpenAI model to use (defaults to gpt-5-nano)
            max_retries: Number of retries on failure

        Returns:
            Tuple of (ExtractedFeatures, metadata_dict)
            metadata includes: model, cost, tokens, processing_time_ms

        Raises:
            AIExtractionError: If extraction fails after retries
        """
        # Handle both tuple and string inputs
        if isinstance(prompts, tuple):
            system_prompt, user_prompt = prompts
        else:
            system_prompt = SYSTEM_PROMPT
            user_prompt = prompts

        # Use default model if not specified
        if model is None:
            model = DEFAULT_MODEL

        logger.debug(f"Using model: {model}")

        # Retry loop
        for attempt in range(max_retries):
            try:
                start_time = time.time()

                # Call OpenAI API. GPT-5-nano is a reasoning model: no sampling
                # params (temperature/top_p); use reasoning_effort + JSON output.
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    reasoning_effort=DEFAULT_REASONING_EFFORT,
                    response_format={"type": "json_object"},
                )

                processing_time_ms = int((time.time() - start_time) * 1000)

                # Extract text from response
                response_text = response.choices[0].message.content

                # Parse JSON
                try:
                    extracted_data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    # Try to extract JSON from markdown code block
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        json_str = response_text[json_start:json_end].strip()
                        extracted_data = json.loads(json_str)
                    # Try to extract JSON from anywhere in the response
                    elif "{" in response_text and "}" in response_text:
                        # Find the first { and last }
                        json_start = response_text.find("{")
                        json_end = response_text.rfind("}") + 1
                        json_str = response_text[json_start:json_end]
                        try:
                            extracted_data = json.loads(json_str)
                        except json.JSONDecodeError:
                            raise AIExtractionError(
                                f"Failed to parse JSON response: {e}\n"
                                f"Response: {response_text[:200]}..."
                            ) from e
                    else:
                        raise AIExtractionError(
                            f"Failed to parse JSON response: {e}\n"
                            f"Response: {response_text[:200]}..."
                        ) from e

                # Validate with Pydantic
                features = ExtractedFeatures(**extracted_data)

                # Calculate cost
                tokens_input = response.usage.prompt_tokens
                tokens_output = response.usage.completion_tokens
                cost_usd = self.calculate_cost(model, tokens_input, tokens_output)

                # Build metadata with full API response
                metadata = {
                    "model": model,
                    "cost_usd": cost_usd,
                    "tokens_input": tokens_input,
                    "tokens_output": tokens_output,
                    "processing_time_ms": processing_time_ms,
                    "raw_response": {
                        "id": response.id,
                        "model": response.model,
                        "content": response_text,
                        "finish_reason": response.choices[0].finish_reason,
                        "usage": {
                            "prompt_tokens": tokens_input,
                            "completion_tokens": tokens_output,
                            "total_tokens": response.usage.total_tokens,
                        }
                    },
                }

                logger.info(
                    f"Extraction successful - Model: {model}, "
                    f"Cost: ${cost_usd:.6f}, "
                    f"Tokens: {tokens_input}/{tokens_output}, "
                    f"Time: {processing_time_ms}ms"
                )

                return features, metadata

            except ValidationError as e:
                raise AIExtractionError(
                    f"Pydantic validation failed for extracted data: {e}\n"
                    f"Extracted data: {extracted_data}"
                )

            except Exception as e:
                is_rate_limit = "429" in str(e) or "rate limit" in str(e).lower()
                if is_rate_limit:
                    wait_time = 60 * (attempt + 1)  # Exponential backoff
                    logger.warning(
                        f"Rate limit hit (attempt {attempt + 1}/{max_retries}). "
                        f"Waiting {wait_time}s..."
                    )
                else:
                    wait_time = 5 * (attempt + 1)  # Short backoff
                    logger.error(f"OpenAI API error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    raise AIExtractionError(
                        f"API error after {max_retries} retries: {e}"
                    )

        # Should never reach here, but just in case
        raise AIExtractionError(f"Extraction failed after {max_retries} retries")


# Module-level client instance (lazy initialization)
_client_instance: Optional[OpenAIClient] = None


def get_client() -> OpenAIClient:
    """
    Get or create the global OpenAI client instance.

    Returns:
        OpenAIClient instance
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = OpenAIClient()
    return _client_instance
