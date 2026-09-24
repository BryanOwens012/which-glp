"""
Prompts for Muse Spark to extract demographic data from a Reddit user's history.

SYSTEM_PROMPT is byte-stable across requests so OpenRouter can serve it from the prompt
cache; the user's history goes in the user message built by build_user_prompt. Never
interpolate a date, username, or other per-user value into SYSTEM_PROMPT.
"""

SYSTEM_PROMPT = """You extract a demographic profile of one Reddit user from their recent posts and comments. The profile personalizes WhichGLP, a site that compares GLP-1 weight-loss medications (Ozempic, Wegovy, Mounjaro, Zepbound, and compounded semaglutide and tirzepatide) using real-world experiences.

# How the data is used, and why nulls matter

These values are grouped and averaged across many users. A null is left out; a wrong value silently skews every statistic it lands in. Record a value only when the history supports it: explicit statements, flair, or an unmistakable self-reference. Never guess, average, or fill a default. Lists are [] when empty.

# Input

The history lists the user's posts, then their comments, each NEWEST FIRST, with the subreddit, the date it was written, and the user's flair in that subreddit when they have one. Flair often carries stats: "35F" (age and sex), "5'4\\"" (height), SW / CW / GW / HW (starting, current, goal, and highest weight).

Only the user's statements about themselves count. Ignore weights, ages, and conditions they describe for someone else (a partner, a parent, a child, a hypothetical), and ignore numbers that are not body weight.

# Fields

- height_inches: number. Convert: 5'4" = 64; 170 cm = 66.9.
- start_weight_lbs: weight when they started their GLP-1, in lbs (1 kg = 2.20462 lbs, 1 st = 14 lbs). Prefer flair SW or "started at ..."; if several differ, use the one tied to the start of GLP-1 treatment, not a lifetime high (HW) unless they say they started there.
- end_weight_lbs: their most recent weight, in lbs: the newest item that states one (flair CW or "now 180"). Goal weight is never end_weight_lbs.
- age: integer, their current age. If an older item states an age, it still applies; do not adjust it.
- sex: "male" or "female" from flair ("35F"), explicit statements, or unmistakable self-references (pregnancy, postpartum, menopause, "as a guy"); "other" for trans or non-binary users; null otherwise. Never infer it from a partner, username, or writing style.
- state: the US state they live in, full name ("NYC" = New York, "TX" = Texas). Null outside the US or when not said. A place they visited or asked about is not where they live.
- country: where they live: USA, Canada, UK, Australia, etc. Implied by a US state they live in, "NHS" (UK), or paying in £ (UK) or CAD (Canada). Null when nothing says or implies it.
- comorbidities: their own medical conditions, lowercase and normalized: "high blood pressure" = hypertension, "T2D" = type 2 diabetes, "PCOS" = pcos, "fatty liver" = nafld.
- has_insurance: true when insurance covers their GLP-1 (copay, approved prior authorization, "covered"); false when it does not (denied, not covered, paying cash or out of pocket); null when they do not say. A price alone says nothing about coverage.
- insurance_provider: the named insurer, expanded ("BCBS" = Blue Cross Blue Shield, "UHC" = UnitedHealthcare); null if not named.
- confidence_score: 0-1, how much of the profile rests on explicit statements (0.9+ mostly flair or explicit, 0.5-0.7 partly inferred, below 0.5 thin).

# Example

Input:
===== USER HISTORY FOR u/example =====

### Recent Posts (newest first):

## Post 1 | r/Mounjaro | 2026-04-02 | FLAIR: 35F 5'4" SW:220 CW:195 GW:150
3 month update
Down 25 lbs! I'm in Dallas and BCBS finally approved it, $25 copay.

## Post 2 | r/PCOS | 2026-01-10
Anyone with PCOS start Mounjaro?
My mom has type 2 diabetes and I'm worried about it. I'm 220 right now.

### Recent Comments (newest first):

## Comment 1 | r/Mounjaro | 2026-04-05 | FLAIR: 35F 5'4" SW:220 CW:193 GW:150
Weighed in at 193 this morning!

===== END OF USER HISTORY =====

Output:
{"height_inches": 64, "start_weight_lbs": 220, "end_weight_lbs": 193, "age": 35, "sex": "female", "state": "Texas", "country": "USA", "comorbidities": ["pcos"], "has_insurance": true, "insurance_provider": "Blue Cross Blue Shield", "confidence_score": 0.95}

Type 2 diabetes is the mother's, so it is not a comorbidity. The newest weight (193, from the comment) is end_weight_lbs, not the post's CW:195.

Return only the JSON object."""

from datetime import datetime, timezone
from typing import Any, Dict

MAX_ITEMS = 20


def build_item_context(item: Any) -> Dict[str, str]:
    """
    Subreddit, UTC date, and the author's flair in that subreddit, from a PRAW
    Submission or Comment, in the shape build_user_prompt reads.
    """
    created = getattr(item, "created_utc", None)
    return {
        "subreddit": str(getattr(item, "subreddit", "") or ""),
        "created": datetime.fromtimestamp(created, tz=timezone.utc).date().isoformat() if created else "",
        "flair": getattr(item, "author_flair_text", None) or "",
    }


def _build_item_header(kind: str, index: int, item: dict) -> str:
    """'## Post 1 | r/Mounjaro | 2026-04-02 | FLAIR: 35F', leaving out any part that is missing."""
    parts = [f"## {kind} {index}"]
    if (item.get("subreddit") or "").strip():
        parts.append(f"r/{item['subreddit'].strip()}")
    if (item.get("created") or "").strip():
        parts.append(item["created"].strip()[:10])
    if (item.get("flair") or "").strip():
        parts.append(f"FLAIR: {item['flair'].strip()}")
    return " | ".join(parts)


def build_user_prompt(username: str, posts: list, comments: list) -> tuple[str, str]:
    """
    Build prompts for demographic extraction from a user's post and comment history.

    Args:
        username: Reddit username (without u/ prefix).
        posts: Newest-first post dicts with 'title' and 'body', and optionally
            'subreddit', 'created' (ISO date), and 'flair'.
        comments: Newest-first comment dicts with 'body', and optionally 'subreddit',
            'created', and 'flair'.

    Returns:
        (SYSTEM_PROMPT, user prompt).
    """
    post_blocks = []
    for i, post in enumerate((posts or [])[:MAX_ITEMS], 1):
        title = (post.get("title") or "").strip()
        body = (post.get("body") or "").strip()
        if not title and not body:
            continue
        post_blocks.append("\n".join(filter(None, [_build_item_header("Post", i, post), title, body])))

    comment_blocks = []
    for i, comment in enumerate((comments or [])[:MAX_ITEMS], 1):
        body = (comment.get("body") or "").strip()
        if not body:
            continue
        comment_blocks.append(f"{_build_item_header('Comment', i, comment)}\n{body}")

    posts_text = "\n\n".join(post_blocks) or "(No posts)"
    comments_text = "\n\n".join(comment_blocks) or "(No comments)"
    user_prompt = f"""===== USER HISTORY FOR u/{username} =====

### Recent Posts (newest first):

{posts_text}

### Recent Comments (newest first):

{comments_text}

===== END OF USER HISTORY ====="""

    return SYSTEM_PROMPT, user_prompt
