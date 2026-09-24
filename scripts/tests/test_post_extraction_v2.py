"""
Offline tests for post-extraction v2: the schema, deterministic row mapping, quote
grounding, and the shared extractor's structured-output and validation-repair paths.

Run: venv/bin/pytest scripts/tests/test_post_extraction_v2.py -q
"""

import copy
import json
import sys
import types
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "post-extraction"))

import shared.openai_extractor as oe  # noqa: E402
from prompts import _EXAMPLE_1_OUTPUT, _EXAMPLE_2_OUTPUT, SYSTEM_PROMPT, build_post_prompt  # noqa: E402
from rows import derive_weight_lost, ground_extraction, source_for_name, to_feature_row, weight_conflict  # noqa: E402
from schema import PostExtraction  # noqa: E402
from shared.openai_extractor import BaseOpenAIExtractor, OpenAIExtractionError, strict_json_schema  # noqa: E402


def make_extraction(**overrides) -> PostExtraction:
    data = copy.deepcopy(_EXAMPLE_2_OUTPUT)
    data.update(overrides)
    return PostExtraction(**data)


POST_TEXT = (
    "Units question for new vial\n"
    "My last vial was 20mg/ml. Down 31 lbs since January so I don't want to mess this up lol. "
    "$249/mo is way better than the $1,086 Zepbound wanted."
)


# --------------------------------------------------------------------------
# Schema and prompt
# --------------------------------------------------------------------------

@pytest.mark.parametrize("example", [_EXAMPLE_1_OUTPUT, _EXAMPLE_2_OUTPUT])
def test_prompt_examples_validate_against_the_schema(example):
    PostExtraction(**copy.deepcopy(example))


def test_every_schema_property_is_required_and_closed():
    # Strict mode rejects a schema with an optional property or open object anywhere.
    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" in node:
                assert set(node["required"]) == set(node["properties"])
                assert node["additionalProperties"] is False
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    schema = strict_json_schema(PostExtraction)
    assert "$ref" not in json.dumps(schema) and "$defs" not in schema
    walk(schema)


def test_unknown_drug_name_is_rejected():
    data = copy.deepcopy(_EXAMPLE_2_OUTPUT)
    data["drugs"][0]["name"] = "Tirz"
    with pytest.raises(ValidationError):
        PostExtraction(**data)


def test_near_miss_values_are_repaired_not_rejected():
    data = copy.deepcopy(_EXAMPLE_2_OUTPUT)
    data["drugs"][0]["name"] = "compounded tirzepatide"
    data["weight_lost"]["unit"] = "Pounds"
    data["side_effects"] = [{"name": "Nausea", "detail": None, "severity": "extreme", "resolved": None}]
    extraction = PostExtraction(**data)
    assert extraction.drugs[0].name == "Compounded Tirzepatide"
    assert extraction.weight_lost.unit == "lbs"
    assert (extraction.side_effects[0].name, extraction.side_effects[0].severity) == ("nausea", "severe")


def test_system_prompt_carries_no_per_post_values():
    # The system prompt is the cached prefix: it must be identical for every post.
    first, _ = build_post_prompt("Ozempic", "a", "b", "35F", "2026-01-01")
    second, _ = build_post_prompt("zepbound", "c", "d", "", "2026-09-01")
    assert first == second == SYSTEM_PROMPT


def test_user_prompt_includes_posted_date_and_tolerates_empties():
    _, user = build_post_prompt("Ozempic", "Title", None, None, "2026-09-23T02:40:42+00:00")
    assert "POSTED: 2026-09-23\n" in user
    assert "(no body text)" in user and "AUTHOR FLAIR" not in user and "None" not in user


# --------------------------------------------------------------------------
# Quote grounding
# --------------------------------------------------------------------------

def test_grounded_quotes_are_kept():
    extraction = make_extraction()
    assert ground_extraction(extraction, POST_TEXT) == []
    assert extraction.weight_lost.value == 31 and extraction.cost_per_month == 249


def test_ungrounded_values_are_nulled():
    extraction = make_extraction(
        weight_lost={"value": 40, "unit": "lbs", "quote": "down 40 lbs"},
        cost_quote="$199 a month",
    )
    dropped = ground_extraction(extraction, POST_TEXT)
    assert dropped == ["weight_lost", "cost_per_month"]
    assert extraction.weight_lost is None
    assert extraction.cost_per_month is None and extraction.currency is None
    assert extraction.duration_weeks == 20  # its quote "since January" is in the text


def test_grounding_ignores_case_whitespace_curly_quotes_and_markdown():
    extraction = make_extraction(
        weight_lost={"value": 31, "unit": "lbs", "quote": "DOWN 31  lbs"},
        duration_quote="I don't want",
    )
    text = POST_TEXT.replace("I don't", "I **don’t**")
    assert ground_extraction(extraction, text) == []


def test_value_without_a_quote_is_dropped():
    extraction = make_extraction(duration_quote=None)
    assert ground_extraction(extraction, POST_TEXT) == ["duration_weeks"]


# --------------------------------------------------------------------------
# Row mapping
# --------------------------------------------------------------------------

def test_weight_lost_is_derived_from_start_and_end_when_not_stated():
    extraction = make_extraction(
        weight_lost=None,
        beginning_weight={"value": 220, "unit": "lbs", "quote": "SW:220"},
        end_weight={"value": 195, "unit": "lbs", "quote": "CW:195"},
    )
    assert derive_weight_lost(extraction) == {"value": 25, "unit": "lbs", "quote": None, "derived": True}


def test_mixed_units_derive_in_lbs_and_a_gain_is_not_a_loss():
    mixed = make_extraction(
        weight_lost=None,
        beginning_weight={"value": 100, "unit": "kg", "quote": "100kg"},
        end_weight={"value": 200, "unit": "lbs", "quote": "200 lbs"},
    )
    assert derive_weight_lost(mixed)["unit"] == "lbs"
    assert derive_weight_lost(mixed)["value"] == pytest.approx(20.5, abs=0.1)
    gain = make_extraction(
        weight_lost=None,
        beginning_weight={"value": 180, "unit": "lbs", "quote": "180"},
        end_weight={"value": 190, "unit": "lbs", "quote": "190"},
    )
    assert derive_weight_lost(gain) is None


def test_weight_conflict_flags_disagreeing_numbers():
    agree = make_extraction(
        beginning_weight={"value": 220, "unit": "lbs", "quote": "220"},
        end_weight={"value": 190, "unit": "lbs", "quote": "190"},
    )
    assert not weight_conflict(agree)  # 30 vs stated 31 is within tolerance
    disagree = make_extraction(
        beginning_weight={"value": 220, "unit": "lbs", "quote": "220"},
        end_weight={"value": 210, "unit": "lbs", "quote": "210"},
    )
    assert weight_conflict(disagree)


@pytest.mark.parametrize(
    "name, stated, expected",
    [
        ("Zepbound", None, "brand"),
        ("Zepbound", "compounded", "brand"),
        ("Compounded Tirzepatide", None, "compounded"),
        ("Tirzepatide", "other", "other"),
        ("Tirzepatide", None, None),
        (None, None, None),
    ],
)
def test_source_for_name(name, stated, expected):
    assert source_for_name(name, stated) == expected


def test_feature_row_derives_legacy_drug_columns():
    row = to_feature_row(make_extraction())
    assert row["extraction_version"] == "post-v2"
    assert row["primary_drug"] == "Compounded Tirzepatide"
    assert row["drug_source"] == "compounded"
    assert row["drugs_mentioned"] == ["Compounded Tirzepatide", "Zepbound"]
    # Zepbound is only mentioned, and the current drug has no stated opinion.
    assert row["drug_sentiments"] == {}
    assert row["weight_lost"]["value"] == 31
    assert row["confidence_score"] is None


def test_feature_row_uses_other_name_for_other_drugs():
    extraction = make_extraction(drugs=[
        {"name": "Other", "other_name": "metformin", "relation": "current", "source": None, "sentiment": 0.6},
    ], primary_drug=None)
    row = to_feature_row(extraction)
    assert row["drugs_mentioned"] == ["Metformin"]
    assert row["drug_sentiments"] == {"Metformin": 0.6}
    assert row["drug_source"] is None


# --------------------------------------------------------------------------
# Shared extractor: structured output and validation repair
# --------------------------------------------------------------------------

def _response(content, cost=0.001):
    usage = types.SimpleNamespace(prompt_tokens=100, completion_tokens=20, total_tokens=120, cost=cost)
    choice = types.SimpleNamespace(message=types.SimpleNamespace(content=content), finish_reason="stop")
    return types.SimpleNamespace(id="r", choices=[choice], usage=usage, model=oe.DEFAULT_MODEL)


class _Completions:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def _extractor(responses, **attrs):
    cls = type("TestExtractor", (BaseOpenAIExtractor,), attrs)
    ex = cls(api_key="sk-test")
    ex.client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=_Completions(responses)))
    return ex


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(oe.time, "sleep", lambda *_a, **_k: None)


def test_structured_output_sends_a_strict_json_schema_and_effort():
    ex = _extractor([_response(json.dumps(_EXAMPLE_2_OUTPUT))], STRUCTURED_OUTPUT=True, REASONING_EFFORT="low")
    ex.extract(("SYSTEM", "USER"), PostExtraction)
    call = ex.client.chat.completions.calls[0]
    assert call["response_format"]["type"] == "json_schema"
    assert call["response_format"]["json_schema"]["strict"] is True
    assert call["response_format"]["json_schema"]["name"] == "PostExtraction"
    assert call["extra_body"]["reasoning"]["effort"] == "low"


def test_validation_error_is_repaired_with_the_errors_shown():
    bad = copy.deepcopy(_EXAMPLE_2_OUTPUT)
    bad["post_type"] = "rant"
    ex = _extractor(
        [_response(json.dumps(bad), cost=0.001), _response(json.dumps(_EXAMPLE_2_OUTPUT), cost=0.002)],
        VALIDATION_REPAIRS=1,
    )
    result, meta = ex.extract(("SYSTEM", "USER"), PostExtraction)
    assert result.post_type == "question"
    assert meta["validation_repairs"] == 1
    assert meta["cost_usd"] == pytest.approx(0.003)  # both calls are billed
    repair = ex.client.chat.completions.calls[1]["messages"]
    assert repair[-2] == {"role": "assistant", "content": json.dumps(bad)}
    assert "post_type" in repair[-1]["content"]


def test_repairs_are_bounded():
    bad = copy.deepcopy(_EXAMPLE_2_OUTPUT)
    bad["post_type"] = "rant"
    ex = _extractor([_response(json.dumps(bad))] * 3, VALIDATION_REPAIRS=1)
    with pytest.raises(OpenAIExtractionError):
        ex.extract(("SYSTEM", "USER"), PostExtraction)
    assert len(ex.client.chat.completions.calls) == 2
