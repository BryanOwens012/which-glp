"""
Tests for the extraction eval's comparable records (scripts/extraction-eval/eval_lib.py),
which every effort and prompt decision is scored through.

Run: venv/bin/pytest scripts/tests/test_extraction_eval.py -q
"""

import importlib.util
from pathlib import Path

EVAL_LIB = Path(__file__).resolve().parents[2] / "scripts" / "extraction-eval" / "eval_lib.py"
_spec = importlib.util.spec_from_file_location("extraction_eval_lib", EVAL_LIB)
eval_lib = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eval_lib)


def test_view_weight_loss_needs_both_weights_in_one_unit():
    row = {
        "beginning_weight": {"value": 100, "unit": "kg"},
        "end_weight": {"value": 90, "unit": "kg"},
    }
    comparable = eval_lib.to_comparable(row)
    assert round(comparable["weight_loss_lbs_view"], 2) == 22.05
    assert comparable["weight_loss_lbs"] == comparable["weight_loss_lbs_view"]

    mixed = eval_lib.to_comparable({
        "beginning_weight": {"value": 100, "unit": "kg"},
        "end_weight": {"value": 190, "unit": "lbs"},
    })
    assert mixed["weight_loss_lbs_view"] is None  # the view refuses mixed units


def test_weight_lost_column_counts_only_toward_weight_loss_lbs():
    comparable = eval_lib.to_comparable({"weight_lost": {"value": 10, "unit": "kg"}})
    assert comparable["weight_loss_lbs_view"] is None
    assert round(comparable["weight_loss_lbs"], 2) == 22.05


def test_drug_names_and_sources_are_normalized_the_same_way_for_every_run():
    comparable = eval_lib.to_comparable({"primary_drug": "zepbound", "drug_source": None})
    assert (comparable["primary_drug"], comparable["drug_source"]) == ("Zepbound", "brand")


def test_free_text_side_effects_map_onto_the_vocabulary():
    names = [{"name": "Exhaustion"}, {"name": "injection site itching"}, {"name": "tinnitus"}, "not a dict"]
    assert eval_lib.to_comparable({"side_effects": names})["side_effects"] == [
        "fatigue", "injection site reaction", "other",
    ]
