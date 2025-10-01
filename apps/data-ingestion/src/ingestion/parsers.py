"""
Safe parsing and extraction of Reddit post and comment data

This module provides robust functions to extract data from PRAW objects,
handling all edge cases including:
- Deleted/removed authors
- Missing/None attributes
- Empty strings vs None
- Different data structures for posts vs comments
- Depth calculation for nested comments
"""

from datetime import datetime, timezone
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Constants
MAX_COMMENT_DEPTH = 50  # Prevent infinite loops in depth calculation
DELETED_AUTHOR_PLACEHOLDER = "[deleted]"


class DataParsingError(Exception):
    """Raised when parsing Reddit post or comment data fails"""
    pass


class DataValidationError(Exception):
    """Raised when parsed data fails validation checks"""
    pass


def safe_get_author(obj: Any) -> str:
    """
    Safely extract author name from PRAW object

    Args:
        obj: PRAW post or comment object

    Returns:
        Author username or "[deleted]" if author is None
    """
    try:
        author = getattr(obj, 'author', None)
        if author is None:
            return DELETED_AUTHOR_PLACEHOLDER
        return str(author)
    except Exception as e:
        logger.warning(f"Error extracting author from {getattr(obj, 'id', 'unknown')}: {e}")
        return DELETED_AUTHOR_PLACEHOLDER


def safe_get_text(obj: Any, attr: str) -> Optional[str]:
    """
    Safely extract text attribute, converting empty strings to None

    Args:
        obj: PRAW object
        attr: Attribute name to extract

    Returns:
        Text content or None if missing/empty
    """
    try:
        val = getattr(obj, attr, None)
        # Convert empty strings to None for consistency
        if val == "":
            return None
        return val
    except Exception as e:
        logger.warning(f"Error extracting {attr}: {e}")
        return None


def safe_get_numeric(obj: Any, attr: str, default: Any = None) -> Optional[Any]:
    """
    Safely extract numeric attribute with default fallback

    Args:
        obj: PRAW object
        attr: Attribute name
        default: Default value if attribute missing

    Returns:
        Numeric value or default
    """
    try:
        return getattr(obj, attr, default)
    except Exception as e:
        logger.warning(f"Error extracting {attr}: {e}")
        return default


def safe_get_bool(obj: Any, attr: str, default: bool = False) -> bool:
    """
    Safely extract boolean attribute with default fallback

    Args:
        obj: PRAW object
        attr: Attribute name
        default: Default value if attribute missing

    Returns:
        Boolean value or default
    """
    try:
        return getattr(obj, attr, default)
    except Exception as e:
        logger.warning(f"Error extracting {attr}: {e}")
        return default


def timestamp_to_datetime(unix_timestamp: float) -> datetime:
    """
    Convert Unix timestamp to timezone-aware datetime

    Args:
        unix_timestamp: Unix timestamp from Reddit API

    Returns:
        Timezone-aware datetime in UTC
    """
    return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)


def calculate_comment_depth(comment: Any) -> int:
    """
    Calculate the nesting depth of a comment

    Depth levels:
    - 1: Top-level comment (parent is post)
    - 2+: Nested replies to other comments

    Args:
        comment: PRAW comment object

    Returns:
        Integer depth (1 = top-level, 2+ = nested)
    """
    depth = 1
    iterations = 0

    try:
        parent = comment.parent()

        while hasattr(parent, 'parent') and not parent.is_root:
            depth += 1
            iterations += 1

            # Prevent infinite loops
            if iterations > MAX_COMMENT_DEPTH:
                logger.warning(
                    f"Max depth ({MAX_COMMENT_DEPTH}) reached for comment {comment.id}"
                )
                break

            parent = parent.parent()

    except Exception as e:
        logger.error(f"Error calculating depth for comment {comment.id}: {e}")
        # Default to depth 1 if calculation fails
        depth = 1

    return depth


def extract_parent_comment_id(comment: Any) -> Optional[str]:
    """
    Extract parent comment ID if parent is another comment (not a post)

    Args:
        comment: PRAW comment object

    Returns:
        Parent comment ID without prefix, or None if parent is post
    """
    try:
        # Check if comment is top-level (parent is post)
        if comment.is_root:
            return None

        parent_id = comment.parent_id

        # Parent ID format: "t1_abc123" (comment) or "t3_xyz789" (post)
        if parent_id.startswith('t1_'):
            # Parent is a comment, strip t1_ prefix
            return parent_id[3:]
        else:
            # Parent is a post
            return None

    except Exception as e:
        logger.error(f"Error extracting parent for comment {comment.id}: {e}")
        return None


def serialize_to_json(obj: Any) -> Dict:
    """
    Serialize PRAW object to JSON-compatible dict

    Filters out PRAW internal attributes and non-serializable objects

    Args:
        obj: PRAW post or comment object

    Returns:
        Dictionary of serializable attributes
    """
    try:
        # Use PRAW's __dict__ but filter out private attributes and PRAW objects
        data = {}
        for key, value in obj.__dict__.items():
            # Skip private attributes
            if key.startswith('_'):
                continue

            # Skip PRAW internal objects
            if hasattr(value, '_reddit'):
                continue

            # Handle basic types
            if isinstance(value, (str, int, float, bool, type(None))):
                data[key] = value
            elif isinstance(value, dict):
                data[key] = value
            elif isinstance(value, (list, tuple)):
                # Only include if items are basic types
                if all(isinstance(item, (str, int, float, bool, type(None))) for item in value):
                    data[key] = list(value)

        return data

    except Exception as e:
        logger.error(f"Error serializing object: {e}")
        return {}


def parse_post(post: Any) -> Dict[str, Any]:
    """
    Extract all relevant data from a Reddit post with null safety

    Args:
        post: PRAW Submission object

    Returns:
        Dictionary with all post fields ready for database insertion

    Raises:
        DataParsingError: If critical post data cannot be extracted
    """
    try:
        # Safely extract subreddit info
        subreddit = getattr(post, 'subreddit', None)
        subreddit_name = subreddit.display_name if subreddit else "unknown"
        subreddit_id = subreddit.id if subreddit else "unknown"

        return {
            'post_id': post.id,
            'created_at': timestamp_to_datetime(post.created_utc),
            'subreddit': subreddit_name,
            'subreddit_id': subreddit_id,
            'author': safe_get_author(post),
            'author_flair_text': safe_get_text(post, 'author_flair_text'),
            'title': post.title,
            'body': safe_get_text(post, 'selftext'),
            'body_html': safe_get_text(post, 'selftext_html'),
            'is_nsfw': safe_get_bool(post, 'over_18', False),
            'score': safe_get_numeric(post, 'score', 0),
            'upvote_ratio': safe_get_numeric(post, 'upvote_ratio', None),
            'num_comments': safe_get_numeric(post, 'num_comments', 0),
            'permalink': post.permalink,
            'url': safe_get_text(post, 'url'),
            'raw_json': serialize_to_json(post)
        }
    except Exception as e:
        post_id = getattr(post, 'id', 'unknown')
        logger.error(f"Failed to parse post {post_id}: {e}")
        raise DataParsingError(
            f"Unable to parse Reddit post data for post ID {post_id}: {e}\n"
            f"The post object may be malformed or missing required attributes."
        ) from e


def parse_comment(comment: Any, post_id: str) -> Dict[str, Any]:
    """
    Extract all relevant data from a Reddit comment with null safety

    Args:
        comment: PRAW Comment object
        post_id: ID of the parent post (without t3_ prefix)

    Returns:
        Dictionary with all comment fields ready for database insertion

    Raises:
        DataParsingError: If critical comment data cannot be extracted
    """
    try:
        # Safely extract subreddit info
        subreddit = getattr(comment, 'subreddit', None)
        subreddit_name = subreddit.display_name if subreddit else "unknown"
        subreddit_id = subreddit.id if subreddit else "unknown"

        return {
            'comment_id': comment.id,
            'created_at': timestamp_to_datetime(comment.created_utc),
            'post_id': post_id,
            'parent_comment_id': extract_parent_comment_id(comment),
            'depth': calculate_comment_depth(comment),
            'subreddit': subreddit_name,
            'subreddit_id': subreddit_id,
            'author': safe_get_author(comment),
            'author_flair_text': safe_get_text(comment, 'author_flair_text'),
            'body': comment.body,
            'body_html': safe_get_text(comment, 'body_html'),
            'is_nsfw': safe_get_bool(comment, 'over_18', False),
            'score': safe_get_numeric(comment, 'score', 0),
            'permalink': comment.permalink,
            'raw_json': serialize_to_json(comment)
        }
    except Exception as e:
        comment_id = getattr(comment, 'id', 'unknown')
        logger.error(f"Failed to parse comment {comment_id}: {e}")
        raise DataParsingError(
            f"Unable to parse Reddit comment data for comment ID {comment_id} (post {post_id}): {e}\n"
            f"The comment object may be malformed or missing required attributes."
        ) from e


def validate_post_data(post_data: Dict[str, Any]) -> bool:
    """
    Validate that post data has all required fields

    Args:
        post_data: Parsed post dictionary

    Returns:
        True if valid, False otherwise

    Raises:
        DataValidationError: If validation fails with detailed error message
    """
    required_fields = ['post_id', 'created_at', 'subreddit', 'subreddit_id',
                      'author', 'title', 'permalink']

    missing_fields = []
    for field in required_fields:
        if field not in post_data or post_data[field] is None:
            missing_fields.append(field)

    if missing_fields:
        post_id = post_data.get('post_id', 'unknown')
        error_msg = (
            f"Post data validation failed for post {post_id}: "
            f"Missing required fields: {', '.join(missing_fields)}\n"
            f"All posts must have: {', '.join(required_fields)}"
        )
        logger.error(error_msg)
        return False

    return True


def validate_comment_data(comment_data: Dict[str, Any]) -> bool:
    """
    Validate that comment data has all required fields

    Args:
        comment_data: Parsed comment dictionary

    Returns:
        True if valid, False otherwise

    Raises:
        DataValidationError: If validation fails with detailed error message
    """
    required_fields = ['comment_id', 'created_at', 'post_id', 'subreddit',
                      'subreddit_id', 'author', 'body', 'depth', 'permalink']

    missing_fields = []
    for field in required_fields:
        if field not in comment_data or comment_data[field] is None:
            missing_fields.append(field)

    if missing_fields:
        comment_id = comment_data.get('comment_id', 'unknown')
        post_id = comment_data.get('post_id', 'unknown')
        error_msg = (
            f"Comment data validation failed for comment {comment_id} (post {post_id}): "
            f"Missing required fields: {', '.join(missing_fields)}\n"
            f"All comments must have: {', '.join(required_fields)}"
        )
        logger.error(error_msg)
        return False

    return True
