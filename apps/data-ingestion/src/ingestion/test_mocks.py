"""
Mock PRAW object factory for testing

Provides factory functions to create mock Reddit posts and comments
with all possible combinations of valid attributes for comprehensive testing.
"""

from unittest.mock import Mock, MagicMock
from datetime import datetime
from typing import Optional, List, Any


class MockSubreddit:
    """Mock PRAW Subreddit object"""

    def __init__(self, display_name: str = "test_subreddit", id: str = "t5_test"):
        self.display_name = display_name
        self.id = id


class MockAuthor:
    """Mock PRAW Redditor object"""

    def __init__(self, name: str = "test_user"):
        self.name = name

    def __str__(self):
        return self.name


class SimpleObject:
    """Simple object to hold attributes (avoids MagicMock issues)"""
    pass


def create_mock_post(
    # Required fields
    id: str = "test_post_123",
    title: str = "Test Post Title",
    created_utc: float = 1234567890.0,
    permalink: str = "/r/test/comments/test_post_123/test_post_title/",

    # Optional/nullable fields
    author: Optional[MockAuthor] = None,
    author_flair_text: Optional[str] = None,
    selftext: str = "Test post body",
    selftext_html: Optional[str] = "<div>Test post body</div>",
    over_18: bool = False,
    score: int = 10,
    upvote_ratio: Optional[float] = 0.95,
    num_comments: int = 5,
    url: str = "https://reddit.com/r/test",

    # Subreddit
    subreddit_name: str = "test_subreddit",
    subreddit_id: str = "t5_test",

    # Additional attributes for testing
    extra_attributes: Optional[dict] = None
) -> Mock:
    """
    Create a mock Reddit post (Submission) object

    Args:
        id: Post ID (without t3_ prefix)
        title: Post title
        created_utc: Unix timestamp
        permalink: Relative URL to post
        author: Mock author object or None (for deleted)
        author_flair_text: User flair or None
        selftext: Post body text (empty string for link posts)
        selftext_html: HTML version of body or None
        over_18: NSFW flag
        score: Net upvotes
        upvote_ratio: Ratio of upvotes (0.0-1.0) or None for new posts
        num_comments: Number of comments
        url: External URL for link posts
        subreddit_name: Subreddit display name
        subreddit_id: Subreddit ID with t5_ prefix
        extra_attributes: Additional attributes to add

    Returns:
        Mock post object with all specified attributes
    """
    # Create default author if not provided
    # Use False as sentinel to mean "explicitly set to None"
    if author is not False and author is None:
        author = MockAuthor("test_user")
    elif author is False:
        author = None

    post = SimpleObject()

    # Set basic attributes
    post.id = id
    post.title = title
    post.created_utc = created_utc
    post.permalink = permalink
    post.author = author
    post.author_flair_text = author_flair_text
    post.selftext = selftext
    post.selftext_html = selftext_html
    post.over_18 = over_18
    post.score = score
    post.upvote_ratio = upvote_ratio
    post.num_comments = num_comments
    post.url = url

    # Set subreddit
    post.subreddit = MockSubreddit(subreddit_name, subreddit_id)

    # Add extra attributes if provided
    if extra_attributes:
        for key, value in extra_attributes.items():
            setattr(post, key, value)

    return post


def create_mock_comment(
    # Required fields
    id: str = "test_comment_123",
    body: str = "Test comment body",
    created_utc: float = 1234567890.0,
    permalink: str = "/r/test/comments/post_id/title/comment_id",

    # Parent relationship
    parent_id: str = "t3_post_123",  # t3_ = post, t1_ = comment
    is_root: bool = True,

    # Optional/nullable fields
    author: Optional[MockAuthor] = None,
    author_flair_text: Optional[str] = None,
    body_html: Optional[str] = "<div>Test comment body</div>",
    over_18: Optional[bool] = None,  # Not always present
    score: int = 5,

    # Subreddit
    subreddit_name: str = "test_subreddit",
    subreddit_id: str = "t5_test",

    # Parent mock for depth calculation
    parent_chain: Optional[List] = None,

    # Additional attributes
    extra_attributes: Optional[dict] = None
) -> Mock:
    """
    Create a mock Reddit comment object

    Args:
        id: Comment ID (without t1_ prefix)
        body: Comment text
        created_utc: Unix timestamp
        permalink: Relative URL to comment
        parent_id: Parent ID (t3_xxx for post, t1_xxx for comment)
        is_root: True if parent is post, False if parent is comment
        author: Mock author object or None (for deleted)
        author_flair_text: User flair or None
        body_html: HTML version of body or None
        over_18: NSFW flag (may not be present on comments)
        score: Net upvotes
        subreddit_name: Subreddit display name
        subreddit_id: Subreddit ID with t5_ prefix
        parent_chain: List of parent mocks for depth testing
        extra_attributes: Additional attributes to add

    Returns:
        Mock comment object with all specified attributes
    """
    # Create default author if not provided
    # Use False as sentinel to mean "explicitly set to None"
    if author is not False and author is None:
        author = MockAuthor("test_commenter")
    elif author is False:
        author = None

    comment = SimpleObject()

    # Set basic attributes
    comment.id = id
    comment.body = body
    comment.created_utc = created_utc
    comment.permalink = permalink
    comment.author = author
    comment.author_flair_text = author_flair_text
    comment.body_html = body_html
    comment.score = score
    comment.parent_id = parent_id
    comment.is_root = is_root

    # Set over_18 only if provided (not all comments have this)
    if over_18 is not None:
        comment.over_18 = over_18

    # Set subreddit
    comment.subreddit = MockSubreddit(subreddit_name, subreddit_id)

    # Mock parent() method for depth calculation
    if parent_chain:
        # Create a chain of parent mocks
        def make_parent_func(chain_index):
            if chain_index < len(parent_chain):
                return lambda: parent_chain[chain_index]
            return lambda: None

        comment.parent = make_parent_func(0)
    else:
        # Default: return a mock post parent
        parent_mock = SimpleObject()
        parent_mock.is_root = is_root
        parent_mock.parent = lambda: None
        comment.parent = lambda: parent_mock

    # Add extra attributes if provided
    if extra_attributes:
        for key, value in extra_attributes.items():
            setattr(comment, key, value)

    return comment


def create_nested_comment_chain(depth: int, base_post_id: str = "test_post") -> List[Mock]:
    """
    Create a chain of nested comments for depth testing

    Args:
        depth: Number of nesting levels
        base_post_id: ID of the root post

    Returns:
        List of mock comments with proper parent relationships
    """
    comments = []

    for i in range(depth):
        is_root = (i == 0)
        parent_id = f"t3_{base_post_id}" if is_root else f"t1_comment_{i-1}"

        # Build parent chain for depth calculation
        if i == 0:
            parent_chain = None
        else:
            parent_chain = comments[:i][::-1]  # Reverse order for parent walking

        comment = create_mock_comment(
            id=f"comment_{i}",
            body=f"Nested comment at level {i+1}",
            parent_id=parent_id,
            is_root=is_root,
            parent_chain=parent_chain
        )

        comments.append(comment)

    return comments


# Predefined edge case scenarios
def get_deleted_author_post() -> Mock:
    """Post with deleted author"""
    return create_mock_post(author=False)  # False means explicitly None


def get_link_post_no_selftext() -> Mock:
    """Link post with no body text"""
    return create_mock_post(
        selftext="",
        selftext_html=None,
        url="https://example.com/article"
    )


def get_nsfw_post() -> Mock:
    """NSFW post"""
    return create_mock_post(over_18=True)


def get_new_post_no_upvote_ratio() -> Mock:
    """Very new post without upvote_ratio"""
    return create_mock_post(upvote_ratio=None)


def get_post_no_flair() -> Mock:
    """Post with no author flair"""
    return create_mock_post(author_flair_text=None)


def get_deleted_author_comment() -> Mock:
    """Comment with deleted author"""
    return create_mock_comment(author=False)  # False means explicitly None


def get_comment_no_over18() -> Mock:
    """Comment without over_18 attribute"""
    comment = create_mock_comment(over_18=None)
    # Don't set the over_18 attribute at all
    if hasattr(comment, 'over_18'):
        del comment.over_18
    return comment


def get_nested_reply_comment() -> Mock:
    """Comment that's a reply to another comment"""
    return create_mock_comment(
        parent_id="t1_parent_comment",
        is_root=False
    )


def get_deeply_nested_comments(depth: int = 10) -> List[Mock]:
    """Chain of deeply nested comments"""
    return create_nested_comment_chain(depth)
