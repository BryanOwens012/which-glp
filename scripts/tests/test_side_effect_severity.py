"""
Unit tests for SideEffectData.severity normalization.

The extraction model sometimes answers severity with the confidence scale
(low/medium/high). Those must map onto mild/moderate/severe instead of failing
validation, because extract() does not retry a ValidationError and the post is
then marked failed.

Run: venv/bin/pytest scripts/tests/test_side_effect_severity.py -q
"""

import sys
from pathlib import Path

import pytest

# apps/post-extraction exposes schema.py (-> scripts/legacy-ingestion/extraction/schema.py).
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "post-extraction"))

from schema import SEVERITY_SYNONYMS, SEVERITY_VALUES, ExtractedFeatures, SideEffectData


def test_every_synonym_maps_to_a_real_severity():
    assert set(SEVERITY_SYNONYMS.values()) <= set(SEVERITY_VALUES)


@pytest.mark.parametrize("value", ["mild", "moderate", "severe"])
def test_canonical_severity_passes_through(value):
    assert SideEffectData(name="nausea", severity=value).severity == value


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("low", "mild"),
        ("minor", "mild"),
        ("slight", "mild"),
        ("medium", "moderate"),
        ("high", "severe"),
        ("extreme", "severe"),
        ("  Severe ", "severe"),
        ("LOW", "mild"),
    ],
)
def test_severity_synonyms_normalize(value, expected):
    assert SideEffectData(name="nausea", severity=value).severity == expected


@pytest.mark.parametrize("value", [None, "", "unbearable", 3, ["mild"]])
def test_unrecognized_severity_becomes_none(value):
    assert SideEffectData(name="nausea", severity=value).severity is None


def test_confidence_scale_severity_no_longer_fails_the_whole_extraction():
    # The shape the model returned live: severity on the confidence scale.
    features = ExtractedFeatures.model_validate(
        {"side_effects": [{"name": "Hair Loss", "severity": "low", "confidence": "medium"}]}
    )
    assert features.side_effects[0].name == "hair loss"
    assert features.side_effects[0].severity == "mild"
    assert features.side_effects[0].confidence == "medium"
