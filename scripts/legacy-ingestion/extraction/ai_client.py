"""
OpenAI GPT-5-nano client for the (deprecated) legacy ingestion pipeline.

Thin wrapper over the shared BaseOpenAIExtractor — the OpenAI call, JSON parsing,
retry/backoff, cost tracking, and metadata all live in shared/openai_extractor.py.
When given a bare user prompt, the default SYSTEM_PROMPT is used.
"""

from typing import Any, Dict, Optional, Tuple

from extraction.schema import ExtractedFeatures
from extraction.prompts import SYSTEM_PROMPT
from shared.openai_extractor import BaseOpenAIExtractor, OpenAIExtractionError  # noqa: F401 (re-exported)


class OpenAIClient(BaseOpenAIExtractor):
    """Extracts ExtractedFeatures from Reddit posts/comments via GPT-5-nano."""

    def extract_features(
        self,
        prompts: "tuple[str, str] | str",
        model: Optional[str] = None,
        max_retries: int = 3,
    ) -> Tuple[ExtractedFeatures, Dict[str, Any]]:
        return self.extract(
            prompts,
            ExtractedFeatures,
            default_system_prompt=SYSTEM_PROMPT,
            model=model,
            max_retries=max_retries,
        )


_client_instance: Optional[OpenAIClient] = None


def get_client() -> OpenAIClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = OpenAIClient()
    return _client_instance
