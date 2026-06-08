"""
Unit tests for the OpenAI (GPT-5-nano) extraction client.

These tests mock the OpenAI SDK so they run offline (no API key, no network)
and isolate the client's own logic: message construction, the JSON-extraction
fallbacks, retry/backoff behavior, cost calculation, metadata assembly, and
empty/None response handling.

Run: venv/bin/pytest scripts/tests/test_openai_client_unit.py -q
"""

import sys
import types
from pathlib import Path

import pytest

# The post-extraction client is representative of all three OpenAI wrappers.
# apps/post-extraction has openai_client.py plus `schema`/`shared` symlinks.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "post-extraction"))

import openai_client as oc  # noqa: E402


def make_response(content, prompt_tokens=100, completion_tokens=20,
                  finish_reason="stop", response_id="resp_1"):
    """Build a stand-in that mimics the OpenAI ChatCompletion response shape."""
    message = types.SimpleNamespace(content=content)
    choice = types.SimpleNamespace(message=message, finish_reason=finish_reason)
    usage = types.SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    return types.SimpleNamespace(
        id=response_id, choices=[choice], usage=usage, model="gpt-5-nano"
    )


class _FakeCompletions:
    """Returns/raises queued behaviors per create() call and records kwargs."""

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
def _isolate(monkeypatch):
    # Replace the heavy Pydantic model with a passthrough so these tests target
    # the CLIENT logic, not schema validation.
    monkeypatch.setattr(oc, "ExtractedFeatures", lambda **kw: types.SimpleNamespace(**kw))
    # Never actually sleep during retry tests.
    monkeypatch.setattr(oc.time, "sleep", lambda *_a, **_k: None)


def build_client(behaviors):
    client = oc.OpenAIClient(api_key="sk-test")
    client.client = _FakeClient(behaviors)
    return client


# --------------------------------------------------------------------------
# Happy paths
# --------------------------------------------------------------------------

def test_string_prompt_builds_single_user_message_and_returns_features():
    client = build_client([make_response('{"summary": "ok"}')])
    features, metadata = client.extract_features("hello")

    assert features.summary == "ok"
    assert metadata["model"] == "gpt-5-nano"
    assert metadata["tokens_input"] == 100
    assert metadata["tokens_output"] == 20

    sent = client.client.chat.completions.calls[0]
    assert sent["messages"] == [{"role": "user", "content": "hello"}]
    # Reasoning-model invariants: reasoning_effort + JSON mode, NO temperature.
    assert sent["reasoning_effort"] == "minimal"
    assert sent["response_format"] == {"type": "json_object"}
    assert "temperature" not in sent
    assert sent["model"] == "gpt-5-nano"


def test_tuple_prompt_sets_system_and_user_messages():
    client = build_client([make_response('{"summary": "ok"}')])
    client.extract_features(("SYSTEM", "USER"))

    messages = client.client.chat.completions.calls[0]["messages"]
    assert messages[0] == {"role": "system", "content": "SYSTEM"}
    assert messages[1] == {"role": "user", "content": "USER"}


# --------------------------------------------------------------------------
# JSON-extraction fallbacks
# --------------------------------------------------------------------------

def test_parses_json_wrapped_in_markdown_fence():
    content = '```json\n{"summary": "fenced"}\n```'
    features, _ = build_client([make_response(content)]).extract_features("x")
    assert features.summary == "fenced"


def test_parses_json_embedded_in_prose():
    content = 'Sure, here is the data: {"summary": "embedded"} — hope it helps!'
    features, _ = build_client([make_response(content)]).extract_features("x")
    assert features.summary == "embedded"


def test_unparseable_response_retries_then_raises():
    client = build_client([make_response("no json at all")] * 3)
    with pytest.raises(Exception):
        client.extract_features("x")
    assert len(client.client.chat.completions.calls) == 3  # all retries used


# --------------------------------------------------------------------------
# Empty / None content guard (regression test for the None guard)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("empty", [None, ""])
def test_empty_content_is_treated_as_transient_and_retried(empty):
    client = build_client([make_response(empty)] * 3)
    with pytest.raises(Exception):
        client.extract_features("x")
    assert len(client.client.chat.completions.calls) == 3


# --------------------------------------------------------------------------
# Retry / backoff
# --------------------------------------------------------------------------

def test_rate_limit_then_success_retries_and_returns():
    rate_limited = Exception("Error code: 429 - rate limit exceeded")
    client = build_client([rate_limited, make_response('{"summary": "recovered"}')])
    features, _ = client.extract_features("x")
    assert features.summary == "recovered"
    assert len(client.client.chat.completions.calls) == 2


# --------------------------------------------------------------------------
# Cost calculation
# --------------------------------------------------------------------------

def test_calculate_cost_uses_model_pricing():
    client = build_client([])
    # 1M input @ $0.05 + 1M output @ $0.40
    assert client.calculate_cost("gpt-5-nano", 1_000_000, 1_000_000) == pytest.approx(0.45)


def test_calculate_cost_unknown_model_falls_back_to_default():
    client = build_client([])
    assert client.calculate_cost("does-not-exist", 1_000_000, 0) == pytest.approx(0.05)


def test_metadata_carries_cost_and_raw_response():
    resp = make_response('{"summary": "ok"}', response_id="resp_42")
    client = build_client([resp])
    _, metadata = client.extract_features("x")
    assert metadata["cost_usd"] == pytest.approx(client.calculate_cost("gpt-5-nano", 100, 20))
    assert metadata["raw_response"]["id"] == "resp_42"
    assert metadata["raw_response"]["finish_reason"] == "stop"


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        oc.OpenAIClient()
