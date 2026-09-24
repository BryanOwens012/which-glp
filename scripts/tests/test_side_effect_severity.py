"""
Unit tests for SideEffect.severity normalization.

The extraction model sometimes answers severity with the confidence scale
(low/medium/high). Those must map onto mild/moderate/severe instead of failing
validation, which would cost a repair request or mark the post failed.

Run: venv/bin/pytest scripts/tests/test_side_effect_severity.py -q
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "post-extraction"))

from schema import SEVERITY_SYNONYMS, SEVERITY_VALUES, SideEffect


def test_every_synonym_maps_to_a_real_severity():
    assert set(SEVERITY_SYNONYMS.values()) <= set(SEVERITY_VALUES)


@pytest.mark.parametrize("value", ["mild", "moderate", "severe"])
def test_canonical_severity_passes_through(value):
    assert SideEffect(name="nausea", detail=None, severity=value, resolved=None).severity == value


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
    assert SideEffect(name="nausea", detail=None, severity=value, resolved=None).severity == expected


@pytest.mark.parametrize("value", [None, "", "unbearable", 3, ["mild"]])
def test_unrecognized_severity_becomes_none(value):
    assert SideEffect(name="nausea", detail=None, severity=value, resolved=None).severity is None


def test_confidence_scale_severity_is_repaired_inside_a_side_effect():
    # The shape the model returned live: severity on the confidence scale, name in Title Case.
    effect = SideEffect.model_validate({"name": "Hair Loss", "detail": None, "severity": "low", "resolved": None})
    assert (effect.name, effect.severity) == ("hair loss", "mild")
