#!/usr/bin/env python3
"""Debug user analyzer to see where it's hanging."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "user-ingestion"))
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "shared"))

print("1. Importing modules...")
from shared.database import DatabaseManager
print("✓ Database imported")

print("\n2. Connecting to database...")
db = DatabaseManager()
print("✓ Database connected")

print("\n3. Querying unanalyzed usernames...")
query = """
    SELECT DISTINCT author
    FROM reddit_posts
    WHERE author NOT IN (
        SELECT username FROM reddit_users
    )
    AND author IS NOT NULL
    AND author != '[deleted]'
    AND author != 'AutoModerator'
    ORDER BY author
    LIMIT 5
"""

with db.conn.cursor() as cursor:
    print(f"   Executing query...")
    cursor.execute(query)
    rows = cursor.fetchall()
    usernames = [row[0] for row in rows]

print(f"✓ Found {len(usernames)} unanalyzed users:")
for username in usernames:
    print(f"   - {username}")

print("\n4. Testing PRAW initialization...")
import praw
import os
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_API_APP_ID"),
    client_secret=os.getenv("REDDIT_API_APP_SECRET"),
    user_agent=os.getenv("REDDIT_API_APP_NAME"),
)
print("✓ PRAW initialized")

if usernames:
    test_username = usernames[0]
    print(f"\n5. Testing fetch for u/{test_username}...")
    redditor = reddit.redditor(test_username)

    posts = []
    for i, submission in enumerate(redditor.submissions.new(limit=3)):
        posts.append({"title": submission.title, "body": submission.selftext or ""})
        print(f"   - Post {i+1}: {submission.title[:50]}...")

    print(f"✓ Fetched {len(posts)} posts")

print("\n✓ All components working!")
