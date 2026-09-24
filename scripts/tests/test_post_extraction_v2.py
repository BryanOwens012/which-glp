"""
Offline tests for post-extraction v2: the schema, deterministic row mapping, quote
grounding, and the shared extractor's structured-output and validation-repair paths.

Run: venv/bin/pytest scripts/tests/test_post_extraction_v2.py -q
"""

import copy
import importlib
import json
import re
import sys
import types
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "post-extraction"))

# Imported after the path insert, which is what makes the service's modules importable.
oe = importlib.import_module("shared.openai_extractor")
_prompts = importlib.import_module("prompts")
_rows = importlib.import_module("rows")
PostExtraction = importlib.import_module("schema").PostExtraction

_EXAMPLE_1_OUTPUT, _EXAMPLE_2_OUTPUT = _prompts.EXAMPLE_1_OUTPUT, _prompts.EXAMPLE_2_OUTPUT
SYSTEM_PROMPT, build_post_prompt = _prompts.SYSTEM_PROMPT, _prompts.build_post_prompt
derive_weight_lost, ground_extraction = _rows.derive_weight_lost, _rows.ground_extraction
build_source_text, resolve_source_for_name = _rows.build_source_text, _rows.resolve_source_for_name
to_feature_row, has_weight_conflict = _rows.to_feature_row, _rows.has_weight_conflict
BaseOpenAIExtractor, OpenAIExtractionError = oe.BaseOpenAIExtractor, oe.OpenAIExtractionError
build_strict_json_schema = oe.build_strict_json_schema
OpenAIClient = importlib.import_module("openai_client").OpenAIClient
_vocab = importlib.import_module("vocab")
MIGRATIONS = ROOT / "apps" / "shared" / "migrations"


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

    schema = build_strict_json_schema(PostExtraction)
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
        duration_quote="since January so I don't want",
    )
    text = POST_TEXT.replace("I don't", "I **don’t**")
    assert ground_extraction(extraction, text) == []


def test_value_without_a_quote_is_dropped():
    extraction = make_extraction(duration_quote=None)
    assert ground_extraction(extraction, POST_TEXT) == ["duration_weeks"]


@pytest.mark.parametrize("quote", ["   ", "**", "_", "", "I"])
def test_blank_markup_or_trivial_quotes_ground_nothing(quote):
    extraction = make_extraction(weight_lost={"value": 31, "unit": "lbs", "quote": quote})
    assert ground_extraction(extraction, POST_TEXT) == ["weight_lost"]
    assert extraction.weight_lost is None


def test_a_weight_whose_quote_states_another_number_is_dropped():
    extraction = make_extraction(weight_lost={"value": 400, "unit": "lbs", "quote": "Down 31 lbs"})
    assert ground_extraction(extraction, POST_TEXT) == ["weight_lost"]


def test_a_weight_converted_from_stone_is_kept():
    extraction = make_extraction(weight_lost={"value": 28, "unit": "lbs", "quote": "down 2 st"})
    assert ground_extraction(extraction, "Update: down 2 st since January, $249/mo") == []


def test_a_converted_monthly_cost_is_kept_and_an_amountless_cost_quote_is_not():
    converted = make_extraction(weight_lost=None, cost_per_month=300, cost_quote="$900 for 3 months", duration_quote=None, duration_weeks=None)
    assert ground_extraction(converted, "I pay $900 for 3 months") == []
    amountless = make_extraction(weight_lost=None, cost_quote="way better than", duration_quote=None, duration_weeks=None)
    assert ground_extraction(amountless, POST_TEXT) == ["cost_per_month"]



@pytest.mark.parametrize(
    "value, quote, is_kept",
    [
        (196, "down to 14st", True),
        (187, "13st 5lb", True),
        (999, "13st 5lb", False),
        (240, "1st weigh in was 250", False),  # an ordinal is not stone
        (85.5, "now 85,5 kg", True),  # decimal comma
    ],
)
def test_weight_number_checks(value, quote, is_kept):
    extraction = make_extraction(weight_lost={"value": value, "unit": "lbs", "quote": quote})
    assert ("weight_lost" not in ground_extraction(extraction, quote)) is is_kept


def test_a_thousands_separator_is_not_a_decimal_comma():
    assert _rows._is_number_in_quote(1086, "$1,086 retail")
    assert not _rows._is_number_in_quote(1.086, "$1,086 retail")


@pytest.mark.parametrize(
    "quote, is_kept",
    [("since January", True), ("for 3 wks", True), ("Just did my first shot", True), ("and the", False)],
)
def test_duration_quote_must_name_a_number_or_time(quote, is_kept):
    extraction = make_extraction(weight_lost=None, cost_per_month=None, cost_quote=None, duration_quote=quote)
    assert (ground_extraction(extraction, f"I have been on it {quote} now") == []) is is_kept

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
    stated = make_extraction()
    assert derive_weight_lost(stated) == {"value": 31, "unit": "lbs", "quote": "Down 31 lbs since January", "derived": False}


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


def test_has_weight_conflict_flags_disagreeing_numbers():
    agree = make_extraction(
        beginning_weight={"value": 220, "unit": "lbs", "quote": "220"},
        end_weight={"value": 190, "unit": "lbs", "quote": "190"},
    )
    assert not has_weight_conflict(agree)  # 30 vs stated 31 is within tolerance
    disagree = make_extraction(
        beginning_weight={"value": 220, "unit": "lbs", "quote": "220"},
        end_weight={"value": 210, "unit": "lbs", "quote": "210"},
    )
    assert has_weight_conflict(disagree)


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
def test_resolve_source_for_name(name, stated, expected):
    assert resolve_source_for_name(name, stated) == expected


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


def _drug(name, relation="current", source=None, other_name=None, sentiment=None):
    return {"name": name, "other_name": other_name, "relation": relation, "source": source, "sentiment": sentiment}


@pytest.mark.parametrize(
    "primary, drugs, expected",
    [
        # A generic primary keeps the source the post stated for it.
        ("Tirzepatide", [_drug("Tirzepatide", source="compounded")], "compounded"),
        # Another drug's source is never attributed to the primary.
        ("Semaglutide", [_drug("Semaglutide"), _drug("Ozempic", "previous", "brand")], None),
        # With no primary, the first taken drug decides, and a brand name settles it.
        (None, [_drug("Zepbound")], "brand"),
        (None, [_drug("Tirzepatide", source="other")], "other"),
        # Planned and mentioned-only drugs are not taken, so they never decide.
        (None, [_drug("Zepbound", "planned"), _drug("Wegovy", "mentioned_only", "brand")], None),
    ],
)
def test_drug_source(primary, drugs, expected):
    assert to_feature_row(make_extraction(primary_drug=primary, drugs=drugs))["drug_source"] == expected


def test_other_primary_drug_is_stored_under_its_written_name():
    extraction = make_extraction(
        primary_drug="Other",
        drugs=[_drug("Other", "mentioned_only", other_name="phentermine"), _drug("Other", other_name="metformin")],
    )
    assert to_feature_row(extraction)["primary_drug"] == "Metformin"  # the taken one wins
    blank = make_extraction(primary_drug="Other", drugs=[_drug("Other", other_name="  ")])
    row = to_feature_row(blank)
    assert row["primary_drug"] is None
    assert row["drugs_mentioned"] == []



def test_other_primary_drug_takes_its_source_from_the_same_drug():
    extraction = make_extraction(
        primary_drug="Other",
        drugs=[
            _drug("Other", "mentioned_only", source="compounded", other_name="foo"),
            _drug("Other", other_name="bar"),
        ],
    )
    row = to_feature_row(extraction)
    assert (row["primary_drug"], row["drug_source"]) == ("Bar", None)

def test_other_side_effect_is_stored_under_its_detail_or_dropped():
    extraction = make_extraction(side_effects=[
        {"name": "other", "detail": "Tinnitus", "severity": "mild", "resolved": None},
        {"name": "other", "detail": None, "severity": None, "resolved": None},
        {"name": "nausea", "detail": None, "severity": None, "resolved": True},
    ])
    names = [s["name"] for s in to_feature_row(extraction)["side_effects"]]
    assert names == ["tinnitus", "nausea"]


def test_a_string_where_a_list_belongs_becomes_one_item():
    assert make_extraction(comorbidities="Hypertension").comorbidities == ["hypertension"]


def test_extra_key_in_a_side_effect_is_rejected():
    # The live v1 shape carried a per-effect "confidence"; strict mode refuses it, and the
    # extractor's repair request is what recovers the post.
    data = copy.deepcopy(_EXAMPLE_2_OUTPUT)
    data["side_effects"] = [{"name": "nausea", "detail": None, "severity": "low", "resolved": None, "confidence": "medium"}]
    with pytest.raises(ValidationError):
        PostExtraction(**data)


def test_build_source_text_skips_missing_parts_and_quotes_can_span_them():
    assert build_source_text("Title", None, "") == "Title"
    assert build_source_text("T", "SW:220", "B") == "T\nSW:220\nB"
    extraction = make_extraction(duration_quote="Title since January")
    assert ground_extraction(extraction, build_source_text("Title", None, "since January")) == ["weight_lost", "cost_per_month"]
    assert extraction.duration_weeks == 20


def _check_values(migration: str, constraint: str) -> set:
    sql = (MIGRATIONS / migration).read_text()
    clause = sql[sql.index(constraint):]
    clause = clause[: clause.index(")")]
    return set(re.findall(r"'([^']+)'", clause))


def test_currencies_match_the_database_check():
    assert set(_vocab.CURRENCIES) == _check_values("002_create_extracted_features.up.sql", "valid_currency")


@pytest.mark.parametrize(
    "values, constraint",
    [("POST_TYPES", "extracted_features_post_type_check"), ("TREATMENT_STATUSES", "extracted_features_treatment_status_check")],
)
def test_post_v2_enums_match_migration_035(values, constraint):
    sql = (MIGRATIONS / "035_post_extraction_v2.up.sql").read_text()
    add = sql[sql.index(f"ADD CONSTRAINT {constraint}"):]
    add = add[: add.index(";")]
    assert set(getattr(_vocab, values)) == set(re.findall(r"'([^']+)'", add))


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


def test_post_client_uses_strict_schema_low_effort_and_one_repair():
    client = OpenAIClient(api_key="sk-test")
    client.client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=_Completions([
        _response(json.dumps({**_EXAMPLE_2_OUTPUT, "post_type": "rant"})),
        _response(json.dumps(_EXAMPLE_2_OUTPUT)),
    ])))
    _, meta = client.extract_features(("SYSTEM", "USER"))
    call = client.client.chat.completions.calls[0]
    assert call["response_format"]["json_schema"]["strict"] is True
    assert call["response_format"]["json_schema"]["name"] == "PostExtraction"
    assert call["extra_body"]["reasoning"]["effort"] == "low"
    assert meta["validation_repairs"] == 1


def test_constructor_overrides_class_configuration():
    ex = BaseOpenAIExtractor(api_key="sk-test", reasoning_effort="medium", structured_output=True, validation_repairs=2)
    assert (ex.reasoning_effort, ex.structured_output, ex.validation_repairs) == ("medium", True, 2)
    default = BaseOpenAIExtractor(api_key="sk-test")
    assert (default.reasoning_effort, default.structured_output, default.validation_repairs) == ("minimal", False, 0)


def test_every_billed_call_counts_toward_cost_tokens_and_time():
    bad = json.dumps({**_EXAMPLE_2_OUTPUT, "post_type": "rant"})
    ex = _extractor(
        [_response(bad, cost=0.001), _response("not json", cost=0.002), _response(json.dumps(_EXAMPLE_2_OUTPUT), cost=0.004)],
        VALIDATION_REPAIRS=1,
    )
    ticks = iter(range(0, 60, 1))  # each time.time() call advances one second
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(oe.time, "time", lambda: float(next(ticks)))
        _, meta = ex.extract(("SYSTEM", "USER"), PostExtraction)
    assert meta["processing_time_ms"] == 3000  # three calls, one second each
    assert meta["cost_usd"] == pytest.approx(0.007)
    assert meta["tokens_input"] == 300 and meta["tokens_output"] == 60
    assert meta["raw_response"]["usage"]["prompt_tokens"] == 100  # the returned response's own usage


def test_a_response_without_usage_is_still_used():
    response = _response(json.dumps(_EXAMPLE_2_OUTPUT))
    response.usage = None
    result, meta = _extractor([response]).extract(("SYSTEM", "USER"), PostExtraction)
    assert result.post_type == "question"
    assert meta["tokens_input"] == 0


def test_pipeline_grounds_against_title_flair_and_body():
    pipeline = importlib.import_module("pipeline")
    flair_weights = copy.deepcopy(_EXAMPLE_2_OUTPUT)
    flair_weights.update(
        beginning_weight={"value": 220, "unit": "lbs", "quote": "SW:220"},
        end_weight={"value": 189, "unit": "lbs", "quote": "CW:189"},
        duration_quote="Units question since January",
    )
    client = OpenAIClient(api_key="sk-test")
    client.client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=_Completions(
        [_response(json.dumps(flair_weights)), _response(json.dumps(flair_weights))]
    )))
    post = dict(subreddit="tirzepatidecompound", title="Units question since January", flair="SW:220 CW:189",
                body="Down 31 lbs since January. $249/mo.", created_at="2026-05-20T01:00:00+00:00")
    result = pipeline.extract_post_row(client, **post)
    assert result.dropped == []  # flair and title quotes are grounded
    assert result.row["beginning_weight"]["value"] == 220
    assert result.row["extraction_version"] == "post-v2"
    assert result.has_weight_conflict is False  # 220 - 189 = 31, as stated
    assert pipeline.extract_post_row(client, **post, is_grounded=False).dropped is None
    user_message = client.client.chat.completions.calls[0]["messages"][-1]["content"]
    assert "POSTED: 2026-05-20" in user_message and "AUTHOR FLAIR: SW:220 CW:189" in user_message
