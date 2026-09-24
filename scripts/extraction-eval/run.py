#!/usr/bin/env python3
"""
Run one extraction variant over the sampled posts and save its rows.

Variants:
    v1                 the legacy prompt and schema (what production ran before post-v2)
    v2                 the post-v2 prompt, strict schema, and quote grounding
    v2-nogrounding     post-v2 without quote grounding

Gold labels come from a separate labeling pass (see score.py), not from this script:
the pipeline's OpenRouter key has a small daily cap shared with production.

Writes backups/extraction-eval/runs/<name>.json, keyed by post_id.

Usage (from the repository root, venv active):
    python3 scripts/extraction-eval/run.py v2 --effort low
"""

import argparse
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Tuple

from eval_lib import LEGACY_EXTRACTION, load_module, read_json, source_text, write_json

from openai_client import OpenAIClient
from prompts import SYSTEM_PROMPT, build_post_prompt
from rows import ground_extraction, to_feature_row
from shared.openai_extractor import BaseOpenAIExtractor

def build_runner(variant: str, effort: str):
    """Return a function post -> (row, metadata) for the variant."""
    if variant == "v1":
        legacy_prompts = load_module("legacy_prompts", LEGACY_EXTRACTION / "prompts.py")
        legacy_schema = load_module("legacy_schema", LEGACY_EXTRACTION / "schema.py")
        client = BaseOpenAIExtractor()
        client.PROMPT_CACHE_KEY = "whichglp-extraction-eval-v1"
        client.prompt_cache_key = client.PROMPT_CACHE_KEY
        client.REASONING_EFFORT = effort

        def run_v1(post):
            prompts = legacy_prompts.build_post_prompt(post["subreddit"], post["title"], post["body"] or "", post["author_flair_text"] or "")
            features, meta = client.extract(prompts, legacy_schema.ExtractedFeatures)
            row = features.model_dump()
            row["primary_drug"] = features.primary_drug.strip().title() if features.primary_drug else None
            return row, meta

        return run_v1

    client = OpenAIClient()
    client.REASONING_EFFORT = effort
    client.prompt_cache_key = f"whichglp-extraction-eval-{variant}-{effort}"

    def run_v2(post):
        _, user_prompt = build_post_prompt(post["subreddit"], post["title"], post["body"], post["author_flair_text"] or "", post["created_at"])
        extraction, meta = client.extract_features((SYSTEM_PROMPT, user_prompt))
        meta["grounding_dropped"] = ground_extraction(extraction, source_text(post)) if variant == "v2" else []
        return to_feature_row(extraction), meta

    return run_v2


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("variant", choices=["v1", "v2", "v2-nogrounding"])
    parser.add_argument("--effort", default="minimal", help="Reasoning effort sent to OpenRouter")
    parser.add_argument("--name", help="Output name; defaults to <variant>-<effort>")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    posts = read_json("posts.json")[: args.limit]
    run = build_runner(args.variant, args.effort)
    name = args.name or f"{args.variant}-{args.effort}"

    def one(post) -> Tuple[str, Dict[str, Any]]:
        started = time.time()
        try:
            row, meta = run(post)
            return post["post_id"], {"row": row, "meta": {k: v for k, v in meta.items() if k != "raw_response"}}
        except Exception as e:  # recorded as a failure and scored as one
            return post["post_id"], {"error": f"{type(e).__name__}: {e}"[:500], "seconds": time.time() - started}

    # A first request alone writes the prompt cache; the rest fan out behind it.
    first = one(posts[0])
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = dict([first] + list(pool.map(one, posts[1:])))

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
