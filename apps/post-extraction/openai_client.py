"""
OpenAI GPT-5-nano client for post feature extraction (replaces Claude/GLM).

Thin wrapper over the shared BaseOpenAIExtractor — the OpenAI call, JSON parsing,
retry/backoff, cost tracking, and metadata all live in shared/openai_extractor.py.
"""

from typing import Any, Dict, Optional, Tuple

from schema import ExtractedFeatures
from shared.openai_extractor import BaseOpenAIExtractor


class OpenAIClient(BaseOpenAIExtractor):
    """Extracts ExtractedFeatures from Reddit posts via GPT-5-nano."""

    def extract_features(
        self,
        prompts: "tuple[str, str] | str",
        model: Optional[str] = None,
        max_retries: int = 3,
    ) -> Tuple[ExtractedFeatures, Dict[str, Any]]:
        return self.extract(prompts, ExtractedFeatures, model=model, max_retries=max_retries)


_client_instance: Optional[OpenAIClient] = None


def get_client() -> OpenAIClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = OpenAIClient()
    return _client_instance
