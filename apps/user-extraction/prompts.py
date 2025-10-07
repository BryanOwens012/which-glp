"""
Prompts for GLM-4.5-Air to extract demographic data from Reddit user history.
"""

SYSTEM_PROMPT = """You are a demographic data extraction assistant. Your job is to analyze a Reddit user's post and comment history to extract their demographic information.

Extract the following information if mentioned:
- Height (convert to inches)
- Starting weight before GLP-1 medication (convert to pounds)
- Current weight (convert to pounds)
- Age (in years)
- Sex/gender (male, female, other, or unknown)
- US state of residence
- Country (default to USA if not mentioned)
- Medical comorbidities (diabetes, PCOS, hypothyroidism, etc.)

IMPORTANT INSTRUCTIONS:
1. Only extract information that is explicitly stated or strongly implied
2. Convert all weights to pounds (1 kg = 2.20462 lbs)
3. Convert all heights to inches (1 cm = 0.393701 inches, 1 foot = 12 inches)
4. For sex, look for indicators like "35M", "42F", "I'm a woman", "I'm a guy", etc.
5. For state, look for mentions like "here in California", "I live in TX", "from New York", etc.
6. For comorbidities, extract disease names mentioned (diabetes, PCOS, hypothyroidism, high blood pressure, etc.)
7. Provide a confidence_score (0.0-1.0) based on how explicit the mentions are

CRITICAL: Return ONLY valid JSON matching this exact schema:
{
  "height_inches": null or number,
  "starting_weight_lbs": null or number,
  "current_weight_lbs": null or number,
  "age": null or integer,
  "sex": null or "male" or "female" or "other" or "unknown",
  "state": null or string,
  "country": "USA" or string,
  "comorbidities": [],
  "confidence_score": number between 0.0 and 1.0
}

Do NOT include any explanations, markdown formatting, or text outside the JSON object."""


def build_user_prompt(username: str, posts: list, comments: list) -> str:
    """
    Build prompt for demographic extraction from user's post/comment history.

    Args:
        username: Reddit username (without u/ prefix)
        posts: List of post dictionaries with 'title' and 'body' keys
        comments: List of comment dictionaries with 'body' key

    Returns:
        Formatted prompt string
    """
    # Format posts
    posts_text = ""
    for i, post in enumerate(posts[:20], 1):  # Limit to 20 posts
        title = post.get('title', '')
        body = post.get('body', '')
        posts_text += f"\n## Post {i}: {title}\n{body}\n"

    # Format comments
    comments_text = ""
    for i, comment in enumerate(comments[:20], 1):  # Limit to 20 comments
        body = comment.get('body', '')
        comments_text += f"\n## Comment {i}:\n{body}\n"

    # Build full prompt
    prompt = f"""{SYSTEM_PROMPT}

===== USER HISTORY FOR u/{username} =====

### Recent Posts:
{posts_text if posts_text else "(No posts)"}

### Recent Comments:
{comments_text if comments_text else "(No comments)"}

===== END OF USER HISTORY =====

Analyze the above posts and comments to extract demographic information. Return ONLY the JSON object."""

    return prompt
