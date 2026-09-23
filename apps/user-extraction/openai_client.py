"""
Extraction client (Muse Spark via OpenRouter) for extracting demographic data from Reddit user history.

Thin wrapper over the shared BaseOpenAIExtractor — the OpenRouter call, JSON parsing,
retry/backoff, cost tracking, and metadata all live in shared/openai_extractor.py.
"""

from typing import Any, Dict, Optional, Tuple

from schema import UserDemographics
from shared.openai_extractor import BaseOpenAIExtractor, OpenAIExtractionError  # noqa: F401 (re-exported)


class OpenAIClient(BaseOpenAIExtractor):
    """Extracts UserDemographics from a Reddit user's post/comment history."""

    # OpenRouter sticky-routing key: keeps same-prefix requests on the cached provider
    PROMPT_CACHE_KEY = "whichglp-user-extraction"

    def extract_demographics(
        self,
        prompts: "tuple[str, str] | str",
        max_retries: int = 3,
    ) -> Tuple[UserDemographics, Dict[str, Any]]:
        return self.extract(prompts, UserDemographics, max_retries=max_retries)


_client_instance: Optional[OpenAIClient] = None


def get_client() -> OpenAIClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = OpenAIClient()
    return _client_instance
