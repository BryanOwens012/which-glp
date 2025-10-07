#!/usr/bin/env python3
"""Full end-to-end test of user analysis pipeline."""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "user-extraction"))
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "shared"))

load_dotenv()

import praw
from shared.database import DatabaseManager
from glm_client import get_client
from prompts import build_user_prompt

print("=" * 60)
print("USER ANALYSIS TEST")
print("=" * 60)

# Get 1 unanalyzed user
db = DatabaseManager()
with db.conn.cursor() as cursor:
    cursor.execute("""
        SELECT DISTINCT author
        FROM reddit_posts
        WHERE author NOT IN (SELECT username FROM reddit_users)
        AND author IS NOT NULL
        AND author != '[deleted]'
        AND author != 'AutoModerator'
        LIMIT 1
    """)
    username = cursor.fetchone()[0]

print(f"\nAnalyzing: u/{username}")

# Initialize PRAW
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_API_APP_ID"),
    client_secret=os.getenv("REDDIT_API_APP_SECRET"),
    user_agent=os.getenv("REDDIT_API_APP_NAME"),
)

# Fetch user history
redditor = reddit.redditor(username)

posts = []
for submission in redditor.submissions.new(limit=5):
    posts.append({"title": submission.title, "body": submission.selftext or ""})

comments = []
for comment in redditor.comments.new(limit=5):
    comments.append({"body": comment.body or ""})

print(f"✓ Fetched {len(posts)} posts, {len(comments)} comments")

# Build prompt
prompt = build_user_prompt(username, posts, comments)
print(f"✓ Built prompt ({len(prompt)} chars)")

# Extract with GLM
glm = get_client()
print("✓ Calling GLM API...")
demographics, metadata = glm.extract_demographics(prompt)

print(f"\n✓ EXTRACTION SUCCESSFUL")
print(f"  Cost: ${metadata['cost_usd']:.6f}")
print(f"  Confidence: {demographics.confidence_score}")
print(f"  Age: {demographics.age}, Sex: {demographics.sex}, State: {demographics.state}")

# Insert to database
with db.conn.cursor() as cursor:
    cursor.execute("""
        INSERT INTO reddit_users (
            username, age, sex, state, country,
            height_inches, starting_weight_lbs, current_weight_lbs,
            comorbidities, has_insurance, insurance_provider,
            post_count, comment_count, confidence_score,
            model_used, processing_cost_usd
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        username, demographics.age, demographics.sex, demographics.state, demographics.country,
        demographics.height_inches, demographics.starting_weight_lbs, demographics.current_weight_lbs,
        demographics.comorbidities, demographics.has_insurance, demographics.insurance_provider,
        len(posts), len(comments), demographics.confidence_score,
        metadata['model'], metadata['cost_usd']
    ))
    db.conn.commit()

print(f"✓ Inserted to database")

print("\n" + "=" * 60)
print("TEST COMPLETE!")
print("=" * 60)
