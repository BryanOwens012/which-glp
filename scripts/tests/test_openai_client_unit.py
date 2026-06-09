"""
Unit tests for the shared OpenAI (GPT-5-nano) extraction base class.

These mock the OpenAI SDK so they run offline (no API key, no network) and
isolate the client logic: message construction, the JSON-extraction fallbacks,
retry/backoff, cost calculation, metadata assembly, empty/None handling, and
fail-fast on validation errors.

Run: venv/bin/pytest scripts/tests/test_openai_client_unit.py -q
"""

import sys
import types
from pathlib import Path

import pytest
from pydantic import BaseModel

# apps/post-extraction exposes the `shared` symlink (-> scripts/legacy-ingestion/shared).
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "post-extraction"))

from shared.openai_extractor import BaseOpenAIExtractor, OpenAIExtractionError  # noqa: E402
import shared.openai_extractor as oe  # noqa: E402


# A permissive passthrough "model" for tests that only care about client logic.
def passthrough(**kwargs):
    return types.SimpleNamespace(**kwargs)


# A strict Pydantic model for the validation-failure test.
class StrictModel(BaseModel):
    required_int: int


def make_response(content, prompt_tokens=100, completion_tokens=20,
                  finish_reason="stop", response_id="resp_1"):
    message = types.SimpleNamespace(content=content)
    choice = types.SimpleNamespace(message=message, finish_reason=finish_reason)
    usage = types.SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    return types.SimpleNamespace(id=response_id, choices=[choice], usage=usage, model="gpt-5-nano")


class _FakeCompletions:
    def __init__(self, behaviors):
        self._behaviors = list(behaviors)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        behavior = self._behaviors.pop(0)
        if isinstance(behavior, Exception):
            raise behavior
        return behavior


class _FakeClient:
    def __init__(self, behaviors):
        self.chat = types.SimpleNamespace(completions=_FakeCompletions(behaviors))


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(oe.time, "sleep", lambda *_a, **_k: None)


def build_extractor(behaviors):
    extractor = BaseOpenAIExtractor(api_key="sk-test")
    extractor.client = _FakeClient(behaviors)
    return extractor


# --------------------------------------------------------------------------
# Message construction
# --------------------------------------------------------------------------

def test_string_prompt_builds_single_user_message():
    ex = build_extractor([make_response('{"summary": "ok"}')])
    result, metadata = ex.extract("hello", passthrough)

    assert result.summary == "ok"
    sent = ex.client.chat.completions.calls[0]
    assert sent["messages"] == [{"role": "user", "content": "hello"}]
    # Reasoning-model invariants: reasoning_effort + JSON mode, NO temperature.
    assert sent["reasoning_effort"] == "minimal"
    assert sent["response_format"] == {"type": "json_object"}
    assert "temperature" not in sent
    assert sent["model"] == "gpt-5-nano"


def test_tuple_prompt_sets_system_and_user_messages():
    ex = build_extractor([make_response('{"x": 1}')])
    ex.extract(("SYSTEM", "USER"), passthrough)
    messages = ex.client.chat.completions.calls[0]["messages"]
    assert messages[0] == {"role": "system", "content": "SYSTEM"}
    assert messages[1] == {"role": "user", "content": "USER"}


def test_default_system_prompt_used_for_bare_string():
    ex = build_extractor([make_response('{"x": 1}')])
    ex.extract("USER", passthrough, default_system_prompt="DEFAULT_SYS")
    messages = ex.client.chat.completions.calls[0]["messages"]
    assert messages[0] == {"role": "system", "content": "DEFAULT_SYS"}
    assert messages[1] == {"role": "user", "content": "USER"}


# --------------------------------------------------------------------------
# JSON-extraction fallbacks
# --------------------------------------------------------------------------

def test_parses_json_in_markdown_fence():
    content = '```json\n{"summary": "fenced"}\n```'
    result, _ = build_extractor([make_response(content)]).extract("x", passthrough)
    assert result.summary == "fenced"


def test_parses_json_in_markdown_fence_without_closing():
    content = '```json\n{"summary": "unclosed"}'
    result, _ = build_extractor([make_response(content)]).extract("x", passthrough)
    assert result.summary == "unclosed"


def test_parses_json_embedded_in_prose():
    content = 'Sure: {"summary": "embedded"} — done!'
    result, _ = build_extractor([make_response(content)]).extract("x", passthrough)
    assert result.summary == "embedded"


def test_unparseable_response_retries_then_raises():
    ex = build_extractor([make_response("no json at all")] * 3)
    with pytest.raises(OpenAIExtractionError):
        ex.extract("x", passthrough)
    assert len(ex.client.chat.completions.calls) == 3


# --------------------------------------------------------------------------
# Empty / None content guard
# --------------------------------------------------------------------------

@pytest.mark.parametrize("empty", [None, ""])
def test_empty_content_is_treated_as_transient_and_retried(empty):
    ex = build_extractor([make_response(empty)] * 3)
    with pytest.raises(OpenAIExtractionError):
        ex.extract("x", passthrough)
    assert len(ex.client.chat.completions.calls) == 3


# --------------------------------------------------------------------------
# Validation failures fail fast (no retry)
# --------------------------------------------------------------------------

def test_validation_error_is_not_retried():
    ex = build_extractor([make_response('{"wrong": "shape"}')] * 3)
    with pytest.raises(OpenAIExtractionError):
        ex.extract("x", StrictModel)
    assert len(ex.client.chat.completions.calls) == 1  # no retry on schema mismatch


# --------------------------------------------------------------------------
# Retry / backoff
# --------------------------------------------------------------------------

def test_rate_limit_then_success():
    rate_limited = Exception("Error code: 429 - rate limit exceeded")
    ex = build_extractor([rate_limited, make_response('{"summary": "recovered"}')])
    result, _ = ex.extract("x", passthrough)
    assert result.summary == "recovered"
    assert len(ex.client.chat.completions.calls) == 2


# --------------------------------------------------------------------------
# Cost calculation + metadata
# --------------------------------------------------------------------------

def test_calculate_cost_uses_model_pricing():
    ex = build_extractor([])
    assert ex.calculate_cost("gpt-5-nano", 1_000_000, 1_000_000) == pytest.approx(0.45)


def test_calculate_cost_unknown_model_falls_back_to_default():
    ex = build_extractor([])
    assert ex.calculate_cost("does-not-exist", 1_000_000, 0) == pytest.approx(0.05)


def test_metadata_shape():
    ex = build_extractor([make_response('{"summary": "ok"}', response_id="resp_42")])
    _, metadata = ex.extract("x", passthrough)
    assert metadata["model"] == "gpt-5-nano"
    assert metadata["tokens_input"] == 100
    assert metadata["tokens_output"] == 20
    assert metadata["cost_usd"] == pytest.approx(ex.calculate_cost("gpt-5-nano", 100, 20))
    assert metadata["raw_response"]["id"] == "resp_42"
    assert metadata["raw_response"]["finish_reason"] == "stop"
    assert metadata["raw_response"]["usage"]["total_tokens"] == 120


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        BaseOpenAIExtractor()
