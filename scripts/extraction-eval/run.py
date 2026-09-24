#!/usr/bin/env python3
"""
Run one extraction variant over the sampled posts and save its rows.

Variants:
    v1    the legacy prompt and schema (what production ran before post-v2)
    v2    the post-v2 pipeline (apps/post-extraction/pipeline.py), exactly as the
          service runs it; --no-grounding switches quote grounding off to measure it

Gold labels come from a separate labeling pass (see README.md), not from this script:
the pipeline's OpenRouter key has a small daily cap shared with production.

Writes backups/extraction-eval/runs/<name>.json, keyed by post_id.

Usage (from the repository root, venv active):
    python3 scripts/extraction-eval/run.py v2 --effort low
    python3 scripts/extraction-eval/run.py v1 --effort minimal
"""

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Tuple

from eval_lib import LEGACY_EXTRACTION, load_module, read_json, write_json

from openai_client import OpenAIClient
from pipeline import extract_post_row
from shared.openai_extractor import BaseOpenAIExtractor


def build_runner(variant: str, effort: str, is_grounded: bool):
    """Return a function post -> (row, metadata) for the variant."""
    if variant == "v1":
        legacy_prompts = load_module("legacy_prompts", LEGACY_EXTRACTION / "prompts.py")
        legacy_schema = load_module("legacy_schema", LEGACY_EXTRACTION / "schema.py")
        client = BaseOpenAIExtractor(prompt_cache_key="whichglp-extraction-eval-v1", reasoning_effort=effort)

        def run_v1(post):
            prompts = legacy_prompts.build_post_prompt(
                post["subreddit"], post["title"], post["body"] or "", post["author_flair_text"] or ""
            )
            features, meta = client.extract(prompts, legacy_schema.ExtractedFeatures)
            row = features.model_dump()
            row["primary_drug"] = features.primary_drug.strip().title() if features.primary_drug else None
            return row, meta

        return run_v1

    client = OpenAIClient(
        prompt_cache_key=f"whichglp-extraction-eval-{variant}-{effort}", reasoning_effort=effort
    )

    def run_v2(post):
        result = extract_post_row(
            client,
            subreddit=post["subreddit"],
            title=post["title"],
            body=post["body"],
            flair=post["author_flair_text"],
            created_at=post["created_at"],
            is_grounded=is_grounded,
        )
        return result.row, {**result.metadata, "grounding_dropped": result.dropped}

    return run_v2


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("variant", choices=["v1", "v2"])
    parser.add_argument("--effort", default="minimal", help="Reasoning effort sent to OpenRouter")
    parser.add_argument("--no-grounding", action="store_true", help="v2 only: skip quote grounding")
    parser.add_argument("--name", help="Output name; defaults to <variant>-<effort>")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.no_grounding and args.variant != "v2":
        parser.error("--no-grounding applies to v2 only")

    posts = read_json("posts.json")[: args.limit]
    if not posts:
        sys.exit("No posts to run: posts.json is empty or --limit is 0. Run sample.py first.")
    run = build_runner(args.variant, args.effort, is_grounded=not args.no_grounding)
    name = args.name or f"{args.variant}-{args.effort}" + ("-nogrounding" if args.no_grounding else "")

    def run_one_post(post) -> Tuple[str, Dict[str, Any]]:
        started = time.time()
        try:
            row, meta = run(post)
            return post["post_id"], {"row": row, "meta": {k: v for k, v in meta.items() if k != "raw_response"}}
        except Exception as e:  # recorded as a failure and scored as one
            return post["post_id"], {"error": f"{type(e).__name__}: {e}"[:500], "seconds": time.time() - started}

    # A first request alone writes the prompt cache; the rest fan out behind it.
    first = run_one_post(posts[0])
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = dict([first] + list(pool.map(run_one_post, posts[1:])))

    ok = [r for r in results.values() if "row" in r]
    cost = sum(r["meta"].get("cost_usd", 0) for r in ok)
    print(f"{name}: {len(ok)}/{len(results)} ok, ${cost:.4f} total, ${cost / max(len(ok), 1):.6f}/post")
    for post_id, r in results.items():
        if "error" in r:
            print(f"  FAILED {post_id}: {r['error'][:200]}")
    path = write_json(f"runs/{name}.json", results)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
