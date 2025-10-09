"""
GLM-4.5-Air client for post feature extraction (replaces Claude).

Cost comparison:
- Claude Sonnet 4: $3/$15 per 1M tokens
- GLM-4.5-Air: $0.20/$1.10 per 1M tokens
- Savings: ~15x cheaper
"""

import os
import json
import time
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from zai import ZaiClient
from pydantic import ValidationError

from schema import ExtractedFeatures
from shared.config import get_logger

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

logger = get_logger(__name__)

MODEL_PRICING = {
    "glm-4.5-air": {"input": 0.20, "output": 1.10},
    "glm-4.5": {"input": 0.60, "output": 2.20},
}

DEFAULT_MODEL = "glm-4.5-air"

class GLMClient:
    """GLM-4.5-Air client for extracting features from Reddit posts."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GLM_API_KEY")
        if not self.api_key:
            raise ValueError("GLM_API_KEY not found in environment")
        self.client = ZaiClient(api_key=self.api_key)
        logger.info("GLM client initialized")

    def calculate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        pricing = MODEL_PRICING.get(model, MODEL_PRICING[DEFAULT_MODEL])
        return (tokens_input / 1_000_000) * pricing["input"] + (tokens_output / 1_000_000) * pricing["output"]

    def extract_features(self, prompts: tuple[str, str] | str, model: Optional[str] = None, max_retries: int = 3) -> Tuple[ExtractedFeatures, Dict[str, Any]]:
        """
        Extract features using GLM-4.5-Air.

        Args:
            prompts: Either a tuple of (system_prompt, user_prompt) or just user_prompt string
            model: GLM model to use (defaults to glm-4.5-air)
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
                    temperature=0,
                    stream=False  # Disable streaming to get full response with usage
                )
                processing_time_ms = int((time.time() - start_time) * 1000)

                response_text = response.choices[0].message.content

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
                logger.error(f"GLM error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                else:
                    raise

_client_instance: Optional[GLMClient] = None

def get_client() -> GLMClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = GLMClient()
    return _client_instance
