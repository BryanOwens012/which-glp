from datetime import datetime
from typing import Iterable

import pytz
import tzlocal
import praw


class PrawClient:
    def __init__(self):
        self.reddit = self.init_praw()

    def init_praw(self) -> praw.Reddit:
        """
        Initialize and return a PRAW Reddit instance using environment variables for credentials.
        """
        import os
        from pathlib import Path
        from dotenv import load_dotenv

        # Load .env file from project root (`~/.env`)
        # Clean pathlib approach
        env_path = Path(__file__).resolve().parents[4] / ".env"
        load_dotenv(env_path)

        needed_vars = [
            "REDDIT_API_APP_NAME",
            "REDDIT_API_APP_ID",
            "REDDIT_API_APP_SECRET",
        ]
        for var in needed_vars:
            if var not in os.environ:
                raise EnvironmentError(f"Environment variable {var} not found.")

        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_API_APP_ID"),
            client_secret=os.getenv("REDDIT_API_APP_SECRET"),
            user_agent=os.getenv("REDDIT_API_APP_NAME"),
        )

        return reddit

    def get_most_recent_posts(self, subreddit_name: str, limit: int = 100):
        return self.reddit.subreddit(subreddit_name).new(limit=limit)

    def get_most_recent_comments(self, post_id: str):
        return self.reddit.submission(id=post_id).comments

    def get_post(self, post_id: str):
        return self.reddit.submission(id=post_id)

    @staticmethod
    def format_timestamp(timestamp: float) -> str:
        """Convert a UTC timestamp to a formatted local datetime string."""
        local_timezone = tzlocal.get_localzone()
        utc_aware_dt = datetime.fromtimestamp(timestamp).replace(tzinfo=pytz.utc)
        local_dt = utc_aware_dt.astimezone(local_timezone)

        # Use cross-platform formatting (without platform-specific -)
        day = local_dt.day
        hour = local_dt.hour % 12 or 12
        month = local_dt.strftime("%b")
        year = local_dt.year
        minute = local_dt.strftime("%M")
        am_pm = local_dt.strftime("%p")

        formatted = f"{month} {day}, {year} at {hour}:{minute}{am_pm}"
        return formatted.lower().capitalize()

    @staticmethod
    def print_posts(posts: Iterable):
        for post in posts:
            formatted = PrawClient.format_timestamp(post.created_utc)

            print(
                f"## {post.title}  \n\n {post.author} on {formatted} ({post.url})  \n\n"
            )
            if post.selftext:
                print(f"{post.selftext}")

    @staticmethod
    def print_comments(comments, start: int | None = None, stop: int | None = None):
        start = 0 if start is None else start
        stop = len(comments) if stop is None else stop

        for author, created_utc, body in [
            (comment.author, comment.created_utc, comment.body) for comment in comments
        ][start:stop]:
            formatted = PrawClient.format_timestamp(created_utc)

            print(f"> ### Comment by {author} on {formatted}  \n > \n > {body}  \n\n")


if __name__ == "__main__":
    praw_client = PrawClient()

    subreddit_name = "zepbound"
    post_id = "1nsx6gz"
    post = praw_client.get_post(post_id)

    PrawClient.print_posts([post])
    PrawClient.print_comments(praw_client.get_most_recent_comments(post_id), stop=5)
