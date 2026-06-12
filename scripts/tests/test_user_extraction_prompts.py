"""
Unit tests for apps/user-extraction/prompts.py (offline, no API).

Verifies the prompt-caching split: build_user_prompt must return
(system_prompt, user_prompt) where the system prompt is the byte-stable
static prefix and ONLY the volatile user history lives in the user prompt.

Loaded via importlib (not sys.path) because other test modules import a
different module also named `prompts`.

Run: venv/bin/pytest scripts/tests/test_user_extraction_prompts.py -q
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROMPTS_PATH = ROOT / "apps" / "user-extraction" / "prompts.py"

spec = importlib.util.spec_from_file_location("user_extraction_prompts", PROMPTS_PATH)
prompts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prompts_module)

build_user_prompt = prompts_module.build_user_prompt
SYSTEM_PROMPT = prompts_module.SYSTEM_PROMPT


def make_history(post_count=1, comment_count=1):
    # "PTitle"/"CBody" avoid colliding with the builder's own "## Post N:" headers
    posts = [{"title": f"PTitle {i}", "body": f"PBody {i}"} for i in range(post_count)]
    comments = [{"body": f"CBody {i}"} for i in range(comment_count)]
    return posts, comments


# --------------------------------------------------------------------------
# Prompt-caching split
# --------------------------------------------------------------------------

def test_returns_system_and_user_tuple():
    posts, comments = make_history()
    result = build_user_prompt("tester", posts, comments)
    assert isinstance(result, tuple) and len(result) == 2
    system_prompt, user_prompt = result
    assert system_prompt == SYSTEM_PROMPT
    assert isinstance(user_prompt, str)


def test_system_prompt_not_duplicated_into_user_prompt():
    _, user_prompt = build_user_prompt("tester", *make_history())
    assert SYSTEM_PROMPT not in user_prompt


def test_user_prompt_contains_only_volatile_history():
    _, user_prompt = build_user_prompt("tester", *make_history())
    assert "u/tester" in user_prompt
    assert "PTitle 0" in user_prompt and "PBody 0" in user_prompt
    assert "CBody 0" in user_prompt


def test_system_prompt_is_static_across_calls():
    sys_a, _ = build_user_prompt("alice", *make_history(3, 3))
    sys_b, _ = build_user_prompt("bob", [], [])
    assert sys_a == sys_b  # byte-identical prefix regardless of input


# --------------------------------------------------------------------------
# Empty / None handling
# --------------------------------------------------------------------------

def test_empty_history_uses_placeholders():
    _, user_prompt = build_user_prompt("tester", [], [])
    assert "(No posts)" in user_prompt
    assert "(No comments)" in user_prompt


def test_none_lists_tolerated():
    _, user_prompt = build_user_prompt("tester", None, None)
    assert "(No posts)" in user_prompt
    assert "(No comments)" in user_prompt


def test_none_and_whitespace_items_skipped():
    posts = [{"title": None, "body": None}, {"title": "  ", "body": "\n"}]
    comments = [{"body": None}, {"body": "   "}]
    _, user_prompt = build_user_prompt("tester", posts, comments)
    assert "(No posts)" in user_prompt
    assert "(No comments)" in user_prompt
    assert "None" not in user_prompt  # never leak the literal "None"


def test_post_with_title_but_empty_body_is_kept():
    posts = [{"title": "Only title", "body": ""}]
    _, user_prompt = build_user_prompt("tester", posts, [])
    assert "Only title" in user_prompt


# --------------------------------------------------------------------------
# Truncation limits
# --------------------------------------------------------------------------

def test_posts_and_comments_capped_at_twenty():
    posts, comments = make_history(post_count=25, comment_count=25)
    _, user_prompt = build_user_prompt("tester", posts, comments)
    assert "PTitle 19" in user_prompt and "PTitle 20" not in user_prompt
    assert "CBody 19" in user_prompt and "CBody 20" not in user_prompt
