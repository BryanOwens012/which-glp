"""
Claude AI client for extracting structured data from Reddit posts/comments.

This module provides a wrapper around the Anthropic API with:
- Cost tracking per API call
- Automatic JSON parsing and validation
- Error handling and retries
- Model selection based on content complexity
"""

import os
import json
import time
from typing import Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic, APIError, RateLimitError
from pydantic import ValidationError

from extraction.schema import ExtractedFeatures
from extraction.prompts import SYSTEM_PROMPT
from shared.config import get_logger

# Load environment variables
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)

# Initialize logger
logger = get_logger(__name__)

# Claude model pricing (as of 2025, per million tokens)
MODEL_PRICING = {
    "claude-sonnet-4-20250514": {
        "input": 3.00,    # $3 per MTok
        "output": 15.00,  # $15 per MTok
    },
    "claude-3-5-haiku-20241022": {
        "input": 0.80,    # $0.80 per MTok
        "output": 4.00,   # $4 per MTok
    },
}

# Default models
DEFAULT_MODEL_SIMPLE = "claude-3-5-haiku-20241022"  # For simple posts
DEFAULT_MODEL_COMPLEX = "claude-sonnet-4-20250514"  # For complex comment chains


class AIClientConfigurationError(Exception):
    """Raised when AI client configuration is invalid"""
    pass


class AIExtractionError(Exception):
    """Raised when AI extraction fails"""
    pass


class ClaudeClient:
    """
    Client for Claude API with structured data extraction.

    Handles API calls, cost tracking, JSON parsing, and Pydantic validation.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)

        Raises:
            AIClientConfigurationError: If API key is missing
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise AIClientConfigurationError(
                "Anthropic API key not found.\n"
                "Please set ANTHROPIC_API_KEY in your .env file.\n"
                "Get your API key at: https://console.anthropic.com/settings/keys"
            )

        self.client = Anthropic(api_key=self.api_key)
        logger.info("Claude AI client initialized")

    def select_model(self, prompt: str, threshold_tokens: int = 500) -> str:
        """
        Select appropriate model based on prompt complexity.

        Uses Haiku for simple posts (<500 tokens) and Sonnet for complex ones.

        Args:
            prompt: User prompt text
            threshold_tokens: Token threshold for model selection

        Returns:
            Model identifier string
        """
        # Rough token estimation: ~4 characters per token
        estimated_tokens = len(prompt) // 4

        if estimated_tokens < threshold_tokens:
            return DEFAULT_MODEL_SIMPLE
        else:
            return DEFAULT_MODEL_COMPLEX

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
            logger.warning(f"Unknown model {model}, using Sonnet pricing")
            pricing = MODEL_PRICING[DEFAULT_MODEL_COMPLEX]
        else:
            pricing = MODEL_PRICING[model]

        cost_input = (tokens_input / 1_000_000) * pricing["input"]
        cost_output = (tokens_output / 1_000_000) * pricing["output"]

        return cost_input + cost_output

    def extract_features(
        self,
        user_prompt: str,
        model: Optional[str] = None,
        max_retries: int = 3
    ) -> Tuple[ExtractedFeatures, dict]:
        """
        Extract structured features from a Reddit post/comment.

        Args:
            user_prompt: Formatted prompt with post/comment text
            model: Claude model to use (auto-selected if None)
            max_retries: Number of retries on failure

        Returns:
            Tuple of (ExtractedFeatures, metadata_dict)
            metadata includes: model, cost, tokens, processing_time_ms

        Raises:
            AIExtractionError: If extraction fails after retries
        """
        # Auto-select model if not specified
        if model is None:
            model = self.select_model(user_prompt)

        logger.debug(f"Using model: {model}")

        # Retry loop
        for attempt in range(max_retries):
            try:
                start_time = time.time()

                # Call Claude API
                response = self.client.messages.create(
                    model=model,
                    max_tokens=2048,
                    temperature=0,  # Deterministic extraction
                    system=SYSTEM_PROMPT,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )

                processing_time_ms = int((time.time() - start_time) * 1000)

                # Extract text from response
                response_text = response.content[0].text

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
                tokens_input = response.usage.input_tokens
                tokens_output = response.usage.output_tokens
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
                        "role": response.role,
                        "content": [{"type": c.type, "text": c.text} for c in response.content],
                        "stop_reason": response.stop_reason,
                        "stop_sequence": response.stop_sequence,
                        "usage": {
                            "input_tokens": response.usage.input_tokens,
                            "output_tokens": response.usage.output_tokens,
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

            except RateLimitError as e:
                wait_time = 60 * (attempt + 1)  # Exponential backoff
                logger.warning(
                    f"Rate limit hit (attempt {attempt + 1}/{max_retries}). "
                    f"Waiting {wait_time}s..."
                )
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    raise AIExtractionError(
                        f"Rate limit exceeded after {max_retries} retries: {e}"
                    )

            except ValidationError as e:
                raise AIExtractionError(
                    f"Pydantic validation failed for extracted data: {e}\n"
                    f"Extracted data: {extracted_data}"
                )

            except APIError as e:
                logger.error(f"Anthropic API error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))  # Short backoff
                else:
                    raise AIExtractionError(
                        f"API error after {max_retries} retries: {e}"
                    )

            except Exception as e:
                raise AIExtractionError(
                    f"Unexpected error during extraction: {e}"
                )

        # Should never reach here, but just in case
        raise AIExtractionError(f"Extraction failed after {max_retries} retries")


# Module-level client instance (lazy initialization)
_client_instance: Optional[ClaudeClient] = None


def get_client() -> ClaudeClient:
    """
    Get or create the global Claude client instance.

    Returns:
        ClaudeClient instance
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = ClaudeClient()
    return _client_instance
