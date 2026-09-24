#!/usr/bin/env python3
"""Live smoke test: Muse Spark 1.3 Contributor through OpenRouter, with prompt caching.

Sends the real post-extraction system prompt twice with the extraction client's
exact request shape, then prints token usage, cache reads/writes, and billed cost.
The second call should usually report cached_tokens close to the system prompt's
size; zero on every run means the cache breakpoint is not taking effect.

It makes paid API calls, so everything runs inside main() under the __main__ guard:
pytest collection only imports the module and makes no calls (it defines no tests).
Needs OPENROUTER_API_KEY in the repository-root .env. Spends a fraction of a cent.
Run from the repository root: venv/bin/python scripts/tests/test_openai_minimal.py
"""

import sys
from pathlib import Path


def main() -> int:
    """Run two extraction calls and print their usage. Returns a process exit code."""
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "apps" / "post-extraction"))
    from openai_client import OpenAIClient
    from prompts import SYSTEM_PROMPT, build_post_prompt

    client = OpenAIClient()
    print(f"System prompt: {len(SYSTEM_PROMPT)} characters")

    for attempt in (1, 2):
        prompts = build_post_prompt(
            "zepbound", f"Week 2 update {attempt}", "Started Zepbound 2.5mg, down 4 lbs in two weeks.", "", "2026-09-01"
        )
        try:
            _, metadata = client.extract_features(prompts, max_retries=1)
        except Exception as e:
            print(f"Call {attempt} failed: {e}")
            return 1
        usage = metadata["raw_response"]["usage"]
        print(
            f"Call {attempt}: model={metadata['raw_response']['model']} "
            f"prompt={usage['prompt_tokens']} cached={usage['cached_tokens']} "
            f"written={usage['cache_write_tokens']} completion={usage['completion_tokens']} "
            f"cost=${metadata['cost_usd']:.6f} ({metadata['cost_source']}) "
            f"time={metadata['processing_time_ms']}ms"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
