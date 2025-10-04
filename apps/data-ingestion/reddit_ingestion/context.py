"""
Context builder for Reddit posts and comments.

This module builds full conversation context by traversing comment chains,
which is essential for accurate AI extraction from nested comments.
"""

from typing import Optional, List, Dict, Any
from .config import get_logger

logger = get_logger(__name__)


class ContextBuilder:
    """
    Builds conversation context from in-memory Reddit data.

    For posts: returns just the post data
    For comments: builds the full chain from original post → target comment
    """

    def __init__(self, posts: Dict[str, dict], comments: Dict[str, dict]):
        """
        Initialize context builder with in-memory data lookups.

        Args:
            posts: Dict mapping post_id → post data
            comments: Dict mapping comment_id → comment data
        """
        self.posts = posts
        self.comments = comments
        logger.info(
            f"Context builder initialized with {len(posts)} posts, "
            f"{len(comments)} comments"
        )

    def get_post_context(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Get context for a post extraction.

        Args:
            post_id: Reddit post ID

        Returns:
            Dict with title and body, or None if not found
        """
        post = self.posts.get(post_id)
        if not post:
            logger.warning(f"Post not found: {post_id}")
            return None

        return {
            "type": "post",
            "post_id": post_id,
            "title": post.get("title", ""),
            "body": post.get("body") or "",
            "subreddit": post.get("subreddit", ""),
            "author_flair": post.get("author_flair", ""),
        }

    def build_comment_chain(self, comment_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Build full comment chain from post to target comment.

        This traverses up the parent chain to reconstruct the conversation context.

        Args:
            comment_id: Target comment ID

        Returns:
            List of comment dicts from top-level to target, or None if not found
            Each dict contains: comment_id, author, body, depth
        """
        comment = self.comments.get(comment_id)
        if not comment:
            logger.warning(f"Comment not found: {comment_id}")
            return None

        # Build chain by traversing up parents
        chain = []
        current = comment

        # Walk up the chain
        while current:
            chain.append({
                "comment_id": current["comment_id"],
                "author": current.get("author", "[deleted]"),
                "body": current.get("body", ""),
                "depth": current.get("depth", 1),
                "author_flair": current.get("author_flair", ""),
            })

            # Get parent comment
            parent_id = current.get("parent_comment_id")
            if parent_id:
                current = self.comments.get(parent_id)
            else:
                break

        # Reverse to get top-level → target order
        chain.reverse()

        return chain

    def get_comment_context(self, comment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full context for a comment extraction.

        Includes original post and full comment chain.

        Args:
            comment_id: Target comment ID

        Returns:
            Dict with post data and comment chain, or None if not found
        """
        comment = self.comments.get(comment_id)
        if not comment:
            logger.warning(f"Comment not found: {comment_id}")
            return None

        # Get original post
        post_id = comment.get("post_id")
        post = self.posts.get(post_id) if post_id else None

        if not post:
            logger.warning(f"Post not found for comment {comment_id}: {post_id}")
            return None

        # Build comment chain
        chain = self.build_comment_chain(comment_id)
        if not chain:
            logger.warning(f"Failed to build comment chain for {comment_id}")
            return None

        return {
            "type": "comment",
            "comment_id": comment_id,
            "post_id": post_id,
            "post_title": post.get("title", ""),
            "post_body": post.get("body") or "",
            "subreddit": post.get("subreddit", ""),
            "comment_chain": chain,
        }

    def get_context(
        self,
        post_id: Optional[str] = None,
        comment_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get context for either a post or comment.

        Exactly one of post_id or comment_id must be provided.

        Args:
            post_id: Post ID (if extracting from post)
            comment_id: Comment ID (if extracting from comment)

        Returns:
            Context dict or None if not found

        Raises:
            ValueError: If both or neither ID is provided
        """
        if post_id and comment_id:
            raise ValueError("Cannot specify both post_id and comment_id")
        if not post_id and not comment_id:
            raise ValueError("Must specify either post_id or comment_id")

        if post_id:
            return self.get_post_context(post_id)
        else:
            return self.get_comment_context(comment_id)


def build_context_from_db_rows(posts_rows: List[tuple], comments_rows: List[tuple]) -> ContextBuilder:
    """
    Build ContextBuilder from database query results.

    This is a convenience function for converting psycopg2 query results
    into the dict format expected by ContextBuilder.

    Args:
        posts_rows: List of post tuples from database query
                   Expected columns: post_id, title, body, subreddit, author_flair_text
        comments_rows: List of comment tuples from database query
                      Expected columns: comment_id, post_id, parent_comment_id, body, author, depth, author_flair_text

    Returns:
        ContextBuilder instance
    """
    # Convert posts to dict
    posts = {}
    for row in posts_rows:
        posts[row[0]] = {
            "post_id": row[0],
            "title": row[1],
            "body": row[2],
            "subreddit": row[3],
            "author_flair": row[4] if len(row) > 4 else "",
        }

    # Convert comments to dict
    comments = {}
    for row in comments_rows:
        comments[row[0]] = {
            "comment_id": row[0],
            "post_id": row[1],
            "parent_comment_id": row[2],
            "body": row[3],
            "author": row[4],
            "depth": row[5],
            "author_flair": row[6] if len(row) > 6 else "",
        }

    return ContextBuilder(posts, comments)
