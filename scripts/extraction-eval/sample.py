#!/usr/bin/env python3
"""
Snapshot a sample of already-processed Reddit posts for the extraction eval.

Draws a mix of recent posts (what the pipeline sees today) and older long posts (which
carry the weight, cost, and duration details the harder fields depend on), and writes
them to backups/extraction-eval/posts.json. Read-only against Supabase.

Usage (from the repository root, venv active):
    python3 scripts/extraction-eval/sample.py --recent 50 --long 30 --seed 7
"""

import argparse
import random

from eval_lib import supabase_get, write_json

POST_COLUMNS = "post_id,subreddit,title,body,author_flair_text,created_at"
MIN_LONG_BODY_CHARS = 400


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--recent", type=int, default=50, help="Posts drawn from the most recent processed posts")
    parser.add_argument("--long", type=int, default=30, help="Older posts with long bodies")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    recent_pool = supabase_get("reddit_posts", {
        "select": POST_COLUMNS, "extraction_status": "eq.processed", "order": "created_at.desc", "limit": "400",
    })
    older_pool = supabase_get("reddit_posts", {
        "select": POST_COLUMNS, "extraction_status": "eq.processed", "order": "created_at.desc",
        "offset": "3000", "limit": "1500",
    })
    long_pool = [p for p in older_pool if len(p.get("body") or "") >= MIN_LONG_BODY_CHARS]
    print(f"pools: recent={len(recent_pool)} older={len(older_pool)} long={len(long_pool)}")

    sample = rng.sample(recent_pool, min(args.recent, len(recent_pool)))
    taken = {p["post_id"] for p in sample}
    sample += rng.sample([p for p in long_pool if p["post_id"] not in taken], min(args.long, len(long_pool)))
    path = write_json("posts.json", sample)
    print(f"wrote {len(sample)} posts to {path}")


if __name__ == "__main__":
    main()
