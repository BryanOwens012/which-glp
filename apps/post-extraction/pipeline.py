"""
One post through extraction: prompt, model call, grounding, and row mapping.

The service (api.py) and the extraction eval (scripts/extraction-eval/run.py) both call
extract_post_row, so the eval measures exactly what production runs.
"""

from typing import Any, Dict, List, NamedTuple, Optional

from openai_client import OpenAIClient
from prompts import build_post_prompt
from rows import build_source_text, ground_extraction, has_weight_conflict, to_feature_row


class PostRowResult(NamedTuple):
    row: Dict[str, Any]
    metadata: Dict[str, Any]
    # Fields grounding nulled; None when grounding was switched off.
    dropped: Optional[List[str]]
    has_weight_conflict: bool


def extract_post_row(
    client: OpenAIClient,
    *,
    subreddit: Optional[str],
    title: Optional[str],
    body: Optional[str],
    flair: Optional[str],
    created_at: Optional[str],
    is_grounded: bool = True,
) -> PostRowResult:
    """
    Extract one post into its model-produced extracted_features columns.

    Args:
        client: The extraction client.
        subreddit, title, body, flair, created_at: The post, as reddit_posts stores it.
        is_grounded: Null quoted values the post does not contain. Off only to measure
            what grounding changes.

    Returns:
        The row (without identifiers or processing metadata), the call's metadata, the
        grounded-away fields, and whether a stated weight loss contradicts the weights.
    """
    prompts = build_post_prompt(subreddit or "", title or "", body or "", flair or "", created_at or "")
    extraction, metadata = client.extract_features(prompts)
    dropped = ground_extraction(extraction, build_source_text(title, flair, body)) if is_grounded else None
    return PostRowResult(to_feature_row(extraction), metadata, dropped, has_weight_conflict(extraction))
