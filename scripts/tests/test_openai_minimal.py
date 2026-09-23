#!/usr/bin/env python3
"""Live smoke test: Muse Spark 1.3 Contributor through OpenRouter, with prompt caching.

Sends the real post-extraction system prompt twice with the extraction client's
exact request shape, then prints token usage, cache reads/writes, and billed cost.
The second call should report cached_tokens close to the system prompt's size;
zero means the cache breakpoint is not taking effect.

Needs OPENROUTER_API_KEY in the repository-root .env. Spends a fraction of a cent.
Run from the repository root: venv/bin/python scripts/tests/test_openai_minimal.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "post-extraction"))

from openai_client import OpenAIClient  # noqa: E402
from prompts import SYSTEM_PROMPT  # noqa: E402

client = OpenAIClient()
print(f"System prompt: {len(SYSTEM_PROMPT)} characters")

for attempt in (1, 2):
    user_prompt = f"Post {attempt}: Started Zepbound 2.5mg, down 4 lbs in two weeks. Reply in JSON."
    try:
        _, metadata = client.extract((SYSTEM_PROMPT, user_prompt), lambda **kw: kw, max_retries=1)
    except Exception as e:
        print(f"Call {attempt} failed: {e}")
        sys.exit(1)
    usage = metadata["raw_response"]["usage"]
    print(
        f"Call {attempt}: model={metadata['raw_response']['model']} "
        f"prompt={usage['prompt_tokens']} cached={usage['cached_tokens']} "
        f"written={usage['cache_write_tokens']} completion={usage['completion_tokens']} "
        f"cost=${metadata['cost_usd']:.6f} ({metadata['cost_source']}) "
        f"time={metadata['processing_time_ms']}ms"
    )
