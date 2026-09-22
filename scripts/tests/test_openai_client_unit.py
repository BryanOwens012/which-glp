"""
Unit tests for the shared OpenAI (GPT-6 Luna) extraction base class.

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
                  finish_reason="stop", response_id="resp_1", cached_tokens=None,
                  cache_write_tokens=None):
    message = types.SimpleNamespace(content=content)
    choice = types.SimpleNamespace(message=message, finish_reason=finish_reason)
    usage = types.SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    details = {}
    if cached_tokens is not None:
        details["cached_tokens"] = cached_tokens
    if cache_write_tokens is not None:
        details["cache_write_tokens"] = cache_write_tokens
    if details:
        usage.prompt_tokens_details = types.SimpleNamespace(**details)
    return types.SimpleNamespace(id=response_id, choices=[choice], usage=usage, model="gpt-6-luna")


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
    assert sent["reasoning_effort"] == "none"
    assert sent["response_format"] == {"type": "json_object"}
    assert "temperature" not in sent
    assert sent["model"] == "gpt-6-luna"


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
    assert ex.calculate_cost("gpt-6-luna", 1_000_000, 1_000_000) == pytest.approx(0.60)


def test_calculate_cost_unknown_model_falls_back_to_default():
    ex = build_extractor([])
    assert ex.calculate_cost("does-not-exist", 1_000_000, 0) == pytest.approx(0.10)


def test_metadata_shape():
    ex = build_extractor([make_response('{"summary": "ok"}', response_id="resp_42")])
    _, metadata = ex.extract("x", passthrough)
    assert metadata["model"] == "gpt-6-luna"
    assert metadata["tokens_input"] == 100
    assert metadata["tokens_output"] == 20
    assert metadata["cost_usd"] == pytest.approx(ex.calculate_cost("gpt-6-luna", 100, 20))
    assert metadata["raw_response"]["id"] == "resp_42"
    assert metadata["raw_response"]["finish_reason"] == "stop"
    assert metadata["raw_response"]["usage"]["total_tokens"] == 120


# --------------------------------------------------------------------------
# Prompt caching: cost, metadata, and prompt_cache_key routing
# --------------------------------------------------------------------------

def test_calculate_cost_discounts_cached_input():
    ex = build_extractor([])
    # 1M prompt tokens of which 800k cached, 1M output:
    # 0.2M × $0.10/M + 0.8M × $0.01/M + 1M × $0.50/M = 0.528
    cost = ex.calculate_cost("gpt-6-luna", 1_000_000, 1_000_000, tokens_input_cached=800_000)
    assert cost == pytest.approx(0.528)


def test_calculate_cost_clamps_cached_to_total_input():
    ex = build_extractor([])
    fully_cached = ex.calculate_cost("gpt-6-luna", 1_000_000, 0, tokens_input_cached=1_000_000)
    over_reported = ex.calculate_cost("gpt-6-luna", 1_000_000, 0, tokens_input_cached=2_000_000)
    assert over_reported == pytest.approx(fully_cached) == pytest.approx(0.01)


def test_calculate_cost_cached_none_treated_as_zero():
    ex = build_extractor([])
    assert ex.calculate_cost("gpt-6-luna", 1_000_000, 0, tokens_input_cached=None) == pytest.approx(0.10)


def test_calculate_cost_bills_cache_writes_at_write_rate():
    ex = build_extractor([])
    # 1M prompt tokens: 0.5M cached, 0.3M written to cache, 0.2M plain; no output:
    # 0.5M × $0.01/M + 0.3M × $0.125/M + 0.2M × $0.10/M = 0.0625
    cost = ex.calculate_cost("gpt-6-luna", 1_000_000, 0, tokens_input_cached=500_000,
                             tokens_input_cache_write=300_000)
    assert cost == pytest.approx(0.0625)


def test_calculate_cost_clamps_cache_writes_to_uncached_input():
    # Writes can only come from input that was not a cache hit.
    ex = build_extractor([])
    clamped = ex.calculate_cost("gpt-6-luna", 1_000_000, 0, tokens_input_cached=800_000,
                                tokens_input_cache_write=5_000_000)
    # 0.8M × $0.01/M + 0.2M × $0.125/M = 0.033
    assert clamped == pytest.approx(0.033)


def test_calculate_cost_cache_writes_none_treated_as_zero():
    ex = build_extractor([])
    assert ex.calculate_cost("gpt-6-luna", 1_000_000, 0,
                             tokens_input_cache_write=None) == pytest.approx(0.10)


def test_calculate_cost_unknown_model_without_cached_rate_charges_full_input():
    # Fallback pricing has no "input_cached" guarantee — must not crash or discount wrongly.
    ex = build_extractor([])
    pricing = {"input": 1.0, "output": 2.0}
    oe.MODEL_PRICING["test-model-no-cache-rate"] = pricing
    try:
        cost = ex.calculate_cost("test-model-no-cache-rate", 1_000_000, 0, tokens_input_cached=500_000)
        assert cost == pytest.approx(1.0)  # cached portion billed at full input rate
    finally:
        del oe.MODEL_PRICING["test-model-no-cache-rate"]


def test_metadata_includes_cached_tokens_and_discounted_cost():
    ex = build_extractor([make_response('{"summary": "ok"}', prompt_tokens=100,
                                        completion_tokens=20, cached_tokens=60)])
    _, metadata = ex.extract("x", passthrough)
    assert metadata["tokens_input_cached"] == 60
    assert metadata["raw_response"]["usage"]["cached_tokens"] == 60
    assert metadata["cost_usd"] == pytest.approx(ex.calculate_cost("gpt-6-luna", 100, 20, 60))


def test_metadata_cached_tokens_defaults_to_zero_when_details_missing():
    # Older/partial SDK responses may omit prompt_tokens_details entirely.
    ex = build_extractor([make_response('{"summary": "ok"}')])
    _, metadata = ex.extract("x", passthrough)
    assert metadata["tokens_input_cached"] == 0


def test_metadata_clamps_over_reported_cached_tokens():
    ex = build_extractor([make_response('{"summary": "ok"}', prompt_tokens=100, cached_tokens=150)])
    _, metadata = ex.extract("x", passthrough)
    assert metadata["tokens_input_cached"] == 100


def test_prompt_cache_key_forwarded_when_subclass_sets_it():
    class KeyedExtractor(BaseOpenAIExtractor):
        PROMPT_CACHE_KEY = "whichglp-test"

    ex = KeyedExtractor(api_key="sk-test")
    ex.client = _FakeClient([make_response('{"x": 1}')])
    ex.extract("hello", passthrough)
    assert ex.client.chat.completions.calls[0]["prompt_cache_key"] == "whichglp-test"


def test_prompt_cache_key_omitted_when_unset():
    ex = build_extractor([make_response('{"x": 1}')])
    ex.extract("hello", passthrough)
    assert "prompt_cache_key" not in ex.client.chat.completions.calls[0]


def test_prompt_cache_key_empty_string_disables_class_key():
    class KeyedExtractor(BaseOpenAIExtractor):
        PROMPT_CACHE_KEY = "whichglp-test"

    ex = KeyedExtractor(api_key="sk-test", prompt_cache_key="")
    ex.client = _FakeClient([make_response('{"x": 1}')])
    ex.extract("hello", passthrough)
    assert "prompt_cache_key" not in ex.client.chat.completions.calls[0]


def test_prompt_cache_key_constructor_arg_overrides_class_key():
    class KeyedExtractor(BaseOpenAIExtractor):
        PROMPT_CACHE_KEY = "class-key"

    ex = KeyedExtractor(api_key="sk-test", prompt_cache_key="ctor-key")
    ex.client = _FakeClient([make_response('{"x": 1}')])
    ex.extract("hello", passthrough)
    assert ex.client.chat.completions.calls[0]["prompt_cache_key"] == "ctor-key"


def test_prompt_cache_key_sent_on_every_retry_attempt():
    class KeyedExtractor(BaseOpenAIExtractor):
        PROMPT_CACHE_KEY = "whichglp-test"

    ex = KeyedExtractor(api_key="sk-test")
    ex.client = _FakeClient([Exception("boom"), make_response('{"x": 1}')])
    ex.extract("hello", passthrough)
    assert all(c["prompt_cache_key"] == "whichglp-test" for c in ex.client.chat.completions.calls)


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        BaseOpenAIExtractor()


def test_metadata_includes_cache_write_tokens_and_their_cost():
    ex = build_extractor([make_response('{"summary": "ok"}', prompt_tokens=100,
                                        completion_tokens=20, cached_tokens=40,
                                        cache_write_tokens=50)])
    _, metadata = ex.extract("x", passthrough)
    assert metadata["tokens_input_cache_write"] == 50
    assert metadata["raw_response"]["usage"]["cache_write_tokens"] == 50
    assert metadata["cost_usd"] == pytest.approx(ex.calculate_cost("gpt-6-luna", 100, 20, 40, 50))


def test_metadata_cache_write_tokens_defaults_to_zero_when_field_missing():
    # Older models and partial responses omit the field; its absence must not fail extraction.
    ex = build_extractor([make_response('{"summary": "ok"}', cached_tokens=10)])
    _, metadata = ex.extract("x", passthrough)
    assert metadata["tokens_input_cache_write"] == 0


def test_metadata_clamps_over_reported_cache_write_tokens():
    # Writes can only come from non-cached input: 100 prompt − 40 cached = 60.
    ex = build_extractor([make_response('{"summary": "ok"}', prompt_tokens=100,
                                        completion_tokens=20, cached_tokens=40,
                                        cache_write_tokens=500)])
    _, metadata = ex.extract("x", passthrough)
    assert metadata["tokens_input_cache_write"] == 60
    assert metadata["raw_response"]["usage"]["cache_write_tokens"] == 60
    assert metadata["cost_usd"] == pytest.approx(ex.calculate_cost("gpt-6-luna", 100, 20, 40, 60))


@pytest.mark.parametrize(
    ("details_kwargs", "expected_cached", "expected_write"),
    [
        ({"cached_tokens": 40}, 40, 0),  # SDK leaves cache_write_tokens as None
        ({"cached_tokens": None, "cache_write_tokens": None}, 0, 0),
        ({"cached_tokens": 40, "cache_write_tokens": 50}, 40, 50),
    ],
)
def test_metadata_from_real_sdk_usage_types(details_kwargs, expected_cached, expected_write):
    # The real SDK declares these fields, so an unreported count is None rather
    # than a missing attribute; metadata must still hold integers.
    from openai.types.completion_usage import CompletionUsage, PromptTokensDetails

    response = make_response('{"summary": "ok"}')
    response.usage = CompletionUsage(
        prompt_tokens=100,
        completion_tokens=20,
        total_tokens=120,
        prompt_tokens_details=PromptTokensDetails(**details_kwargs),
    )
    ex = build_extractor([response])
    _, metadata = ex.extract("x", passthrough)
    assert metadata["tokens_input_cached"] == expected_cached
    assert metadata["tokens_input_cache_write"] == expected_write
    assert metadata["raw_response"]["usage"]["cache_write_tokens"] == expected_write
    assert metadata["cost_usd"] == pytest.approx(
        ex.calculate_cost("gpt-6-luna", 100, 20, expected_cached, expected_write)
    )


def test_extract_always_uses_the_extraction_model_and_its_effort():
    # The effort value is only valid for DEFAULT_MODEL, so extract() takes no model override.
    ex = build_extractor([make_response('{"summary": "ok"}')])
    with pytest.raises(TypeError):
        ex.extract("x", passthrough, model="gpt-5-nano")
