"""
Extraction client (Muse Spark via OpenRouter) for post feature extraction.

Thin wrapper over the shared BaseOpenAIExtractor — the OpenRouter call, JSON parsing,
retry/backoff, validation repair, cost tracking, and metadata all live in
shared/openai_extractor.py.
"""

from typing import Any, Dict, Optional, Tuple

from schema import PostExtraction
from shared.openai_extractor import BaseOpenAIExtractor


class OpenAIClient(BaseOpenAIExtractor):
    """Extracts PostExtraction from Reddit posts."""

    # OpenRouter sticky-routing key: keeps same-prefix requests on the cached provider
    PROMPT_CACHE_KEY = "whichglp-post-extraction"
    # Chosen with scripts/extraction-eval: "low" beat "minimal" on duration and drug
    # naming at $0.00038 vs $0.00024 per post; "medium" added little more at $0.00071.
    REASONING_EFFORT = "low"
    STRUCTURED_OUTPUT = True
    VALIDATION_REPAIRS = 1

    def extract_features(
        self,
        prompts: "tuple[str, str] | str",
        max_retries: int = 3,
    ) -> Tuple[PostExtraction, Dict[str, Any]]:
        return self.extract(prompts, PostExtraction, max_retries=max_retries)


_client_instance: Optional[OpenAIClient] = None


def get_client() -> OpenAIClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = OpenAIClient()
    return _client_instance
