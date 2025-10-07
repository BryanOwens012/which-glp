"""
GLM-4.5-Air client for extracting demographic data from Reddit user history.

This module provides a wrapper around the Z.AI SDK (GLM-4.5-Air) with:
- Cost tracking per API call
- Automatic JSON parsing and validation
- Error handling and retries
- Significantly cheaper than Claude ($0.20/$1.10 vs $3/$15 per 1M tokens)
"""

import os
import json
import time
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from zai import ZaiClient
from pydantic import ValidationError

from schema import UserDemographics
from shared.config import get_logger

# Load environment variables
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

# Initialize logger
logger = get_logger(__name__)

# GLM model pricing (as of 2025, per million tokens)
MODEL_PRICING = {
    "glm-4.5-air": {
        "input": 0.20,   # $0.20 per MTok
        "output": 1.10,  # $1.10 per MTok
    },
    "glm-4.5": {
        "input": 0.60,   # $0.60 per MTok
        "output": 2.20,  # $2.20 per MTok
    },
}

# Default model
DEFAULT_MODEL = "glm-4.5-air"


class GLMClientConfigurationError(Exception):
    """Raised when GLM client configuration is invalid"""
    pass


class GLMExtractionError(Exception):
    """Raised when GLM extraction fails"""
    pass


class GLMClient:
    """
    Client for GLM-4.5-Air API with demographic data extraction.

    Handles API calls, cost tracking, JSON parsing, and Pydantic validation.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize GLM client.

        Args:
            api_key: Z.AI API key (defaults to GLM_API_KEY env var)

        Raises:
            GLMClientConfigurationError: If API key is missing
        """
        self.api_key = api_key or os.getenv("GLM_API_KEY")

        if not self.api_key:
            raise GLMClientConfigurationError(
                "GLM API key not found.\n"
                "Please set GLM_API_KEY in your .env file.\n"
                "Get your API key at: https://z.ai/model-api"
            )

        self.client = ZaiClient(api_key=self.api_key)
        logger.info("GLM AI client initialized")

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
            logger.warning(f"Unknown model {model}, using glm-4.5-air pricing")
            pricing = MODEL_PRICING[DEFAULT_MODEL]
        else:
            pricing = MODEL_PRICING[model]

        cost_input = (tokens_input / 1_000_000) * pricing["input"]
        cost_output = (tokens_output / 1_000_000) * pricing["output"]

        return cost_input + cost_output

    def extract_demographics(
        self,
        user_prompt: str,
        model: Optional[str] = None,
        max_retries: int = 3
    ) -> Tuple[UserDemographics, Dict[str, Any]]:
        """
        Extract demographic data from Reddit user's post/comment history.

        Args:
            user_prompt: Formatted prompt with user's posts/comments
            model: GLM model to use (defaults to glm-4.5-air)
            max_retries: Number of retries on failure

        Returns:
            Tuple of (UserDemographics, metadata_dict)
            metadata includes: model, cost, tokens, processing_time_ms

        Raises:
            GLMExtractionError: If extraction fails after retries
        """
        # Use default model if not specified
        if model is None:
            model = DEFAULT_MODEL

        logger.debug(f"Using model: {model}")

        # Retry loop
        for attempt in range(max_retries):
            try:
                start_time = time.time()

                # Call GLM API (disable streaming to get usage stats)
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0,  # Deterministic extraction
                    stream=False,  # Disable streaming to get full response with usage
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
                        json_start = response_text.find("{")
                        json_end = response_text.rfind("}") + 1
                        json_str = response_text[json_start:json_end]
                        try:
                            extracted_data = json.loads(json_str)
                        except json.JSONDecodeError:
                            raise GLMExtractionError(
                                f"Failed to parse JSON response: {e}\n"
                                f"Response: {response_text[:200]}..."
                            ) from e
                    else:
                        raise GLMExtractionError(
                            f"Failed to parse JSON response: {e}\n"
                            f"Response: {response_text[:200]}..."
                        ) from e

                # Validate with Pydantic
                demographics = UserDemographics(**extracted_data)

                # Calculate cost
                tokens_input = response.usage.prompt_tokens
                tokens_output = response.usage.completion_tokens
                cost_usd = self.calculate_cost(model, tokens_input, tokens_output)

                # Build metadata
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

                return demographics, metadata

            except ValidationError as e:
                raise GLMExtractionError(
                    f"Pydantic validation failed for extracted data: {e}\n"
                    f"Extracted data: {extracted_data}"
                )

            except Exception as e:
                logger.error(f"GLM API error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)  # Exponential backoff
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise GLMExtractionError(
                        f"Extraction failed after {max_retries} retries: {e}"
                    )

        # Should never reach here
        raise GLMExtractionError(f"Extraction failed after {max_retries} retries")


# Module-level client instance (lazy initialization)
_client_instance: Optional[GLMClient] = None


def get_client() -> GLMClient:
    """
    Get or create the global GLM client instance.

    Returns:
        GLMClient instance
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = GLMClient()
    return _client_instance
