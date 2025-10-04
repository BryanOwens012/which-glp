"""
Content filters for AI extraction pipeline.

Filters posts/comments to reduce unnecessary API costs by skipping
irrelevant content in non-drug-specific subreddits.
"""

import re
from typing import Set, Pattern

# Drug brand names and generic names
DRUG_KEYWORDS: Set[str] = {
    # GLP-1 Agonists - Brand Names
    "ozempic", "wegovy", "rybelsus",  # semaglutide
    "mounjaro", "zepbound",  # tirzepatide
    "victoza", "saxenda",  # liraglutide
    "trulicity",  # dulaglutide
    "byetta", "bydureon",  # exenatide
    "adlyxin",  # lixisenatide

    # Generic drug names
    "semaglutide", "tirzepatide", "liraglutide",
    "dulaglutide", "exenatide", "lixisenatide",

    # Common variations/nicknames
    "sema", "tirz", "lira",
    "glp-1", "glp1", "glp 1",
    "glp-1 agonist", "glp1 agonist", "glp-1 agonists", "glp1 agonists",

    # Compound/compounded versions
    "compound", "compounded", "compounding",
    "peptide", "peptides",

    # General medication terms
    "drug", "drugs",
    "medication", "medications", "meds",
    "medicine", "medicines",

    # Weight loss terms
    "weight loss", "weight-loss", "weightloss",
    "weight loss drug", "weight loss drugs",
    "weight-loss drug", "weight-loss drugs",
    "weight loss medication", "weight loss medications",
    "weight-loss medication", "weight-loss medications",
    "weight loss medicine", "weight loss medicines",
    "weight-loss medicine", "weight-loss medicines",
    "weight loss injection", "weight loss injections",
    "weight-loss injection", "weight-loss injections",
    "appetite suppressant", "appetite suppressants",

    # Medical terms related to GLP-1s
    "injection", "injections", "injectable", "injectables",
    "pen", "pens",  # injection pens
    "dose", "doses", "dosage", "dosages", "mg",
    "prescription", "prescriptions", "prescribe", "prescribed", "prescribing",
    "doctor", "doctors", "endocrinologist", "endocrinologists",
    "diabetes", "diabetic", "diabetics", "t2d", "type 2", "type 2 diabetes",
    "a1c", "hba1c", "blood sugar", "glucose",

    # Side effects commonly discussed
    "nausea", "vomiting", "constipation", "diarrhea",
    "sulfur burp", "sulfur burps",
    "gastroparesis",
    "thyroid", "pancreatitis",
    "food noise",  # common term in GLP-1 communities
}

# Non-drug-specific subreddits that need filtering
# (drug-specific subs don't need filtering since all posts are relevant)
NON_DRUG_SUBREDDITS: Set[str] = {
    "loseit", "progresspics", "intermittentfasting",
    "1200isplenty", "fasting", "CICO", "1500isplenty",
    "PCOS", "Brogress", "diabetes", "obesity",
    "SuperMorbidlyObese", "diabetes_t2",
}

# Pre-compiled regex patterns for efficient keyword matching
# Compiled at module level to avoid re-compilation in loops
_COMPILED_PATTERNS: Set[Pattern] = {
    re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
    for keyword in DRUG_KEYWORDS
}


def should_process_content(content: str, subreddit: str) -> bool:
    """
    Check if content should be processed based on keyword filtering.

    Drug-specific subreddits: always process (no filtering)
    Non-drug subreddits: only process if contains drug/medical keywords

    Args:
        content: Post title + selftext or comment body
        subreddit: Subreddit name (e.g., 'loseit', 'Ozempic')

    Returns:
        True if should process with AI, False to skip
    """
    # Drug-specific subreddits: always process
    if subreddit.lower() not in NON_DRUG_SUBREDDITS:
        return True

    # Non-drug subreddits: check for keywords using pre-compiled patterns
    # Check if any drug keyword appears in content
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(content):
            return True

    return False


def should_process_post(post_row: tuple, subreddit: str) -> bool:
    """
    Check if a post should be processed.

    Args:
        post_row: Database row from extraction query (post_id, title, body, subreddit, author_flair_text)
        subreddit: Subreddit name

    Returns:
        True if should process, False to skip
    """
    # post_row format from ai_extraction.py: (post_id, title, body, subreddit, author_flair_text)
    title = post_row[1] or ""
    body = post_row[2] or ""

    content = f"{title} {body}"
    return should_process_content(content, subreddit)


def should_process_comment(comment_row: tuple, subreddit: str) -> bool:
    """
    Check if a comment should be processed.

    Args:
        comment_row: Database row (comment_id, post_id, parent_comment_id, body, ...)
        subreddit: Subreddit name

    Returns:
        True if should process, False to skip
    """
    # comment_row format: (comment_id, post_id, parent_comment_id, body, author, depth, author_flair_text)
    body = comment_row[3] or ""

    return should_process_content(body, subreddit)
