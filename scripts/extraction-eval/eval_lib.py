"""
Shared pieces of the post-extraction evaluation harness.

The harness scores extraction variants (prompt, schema, reasoning effort, grounding)
against gold labels on the same posts, so a prompt or model change is measured on real
inputs before it ships. Posts, gold labels, and run outputs live under
backups/extraction-eval/ (gitignored): they contain Reddit text.

Every variant is reduced to the same comparable record: the values downstream
consumers read, computed the way they compute them. The v1 baseline is the legacy
prompt and schema in scripts/legacy-ingestion/extraction/, which the deployed service
used before post-v2.
"""

import importlib
import importlib.util
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
POST_EXTRACTION = ROOT / "apps" / "post-extraction"
LEGACY_EXTRACTION = ROOT / "scripts" / "legacy-ingestion" / "extraction"
DATA_DIR = ROOT / "backups" / "extraction-eval"

sys.path.insert(0, str(POST_EXTRACTION))
load_dotenv(ROOT / ".env")

# Imported after the path insert, which is what makes the service's modules importable.
_vocab = importlib.import_module("vocab")
_rows = importlib.import_module("rows")
CANONICAL_DRUGS, SIDE_EFFECT_NAMES, SIDE_EFFECT_SYNONYMS = (
    _vocab.CANONICAL_DRUGS, _vocab.SIDE_EFFECT_NAMES, _vocab.SIDE_EFFECT_SYNONYMS,
)
build_source_text, resolve_source_for_name, to_lbs = (
    _rows.build_source_text, _rows.resolve_source_for_name, _rows.to_lbs,
)


def load_module(name: str, path: Path):
    """Import a file under an explicit module name (the legacy files reuse app names)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------
# Read-only data access (PostgREST GET requests only)
# --------------------------------------------------------------------------

def supabase_get(table: str, params: Dict[str, str]) -> List[Dict[str, Any]]:
    """GET rows from Supabase's REST API. GET cannot write, so this is read-only."""
    url = os.environ["SUPABASE_URL"].rstrip("/") + f"/rest/v1/{table}?" + urllib.parse.urlencode(params, safe="(),.*:!")
    key = os.environ["SUPABASE_SERVICE_KEY"]
    request = urllib.request.Request(url, method="GET", headers={"apikey": key, "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())


def read_json(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text())


def write_json(name: str, data: Any) -> Path:
    path = DATA_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, default=str))
    return path


# --------------------------------------------------------------------------
# Comparable records
# --------------------------------------------------------------------------

_DRUG_BY_LOWER = {d.lower(): d for d in CANONICAL_DRUGS}
_SIDE_EFFECT_BY_PHRASE = {
    **{name: name for name in SIDE_EFFECT_NAMES},
    **{phrase: name for name, phrases in SIDE_EFFECT_SYNONYMS.items() for phrase in phrases},
}


def to_canonical_side_effect(name: str) -> str:
    """Map a free-text side-effect name (v1 output) onto the v2 vocabulary, generously."""
    name = (name or "").strip().lower()
    if name in _SIDE_EFFECT_BY_PHRASE:
        return _SIDE_EFFECT_BY_PHRASE[name]
    if name.startswith("injection site"):
        return "injection site reaction"
    return "other"


def _weight_to_lbs(weight: Optional[Dict[str, Any]]) -> Optional[float]:
    if not weight or weight.get("value") is None:
        return None
    return to_lbs(weight["value"], weight.get("unit"))


def _compute_view_weight_loss(beginning: Optional[dict], end: Optional[dict]) -> Optional[float]:
    """weight_loss_lbs the way mv_experiences_denormalized computes it: both weights, same unit."""
    if not beginning or not end or beginning.get("unit") != end.get("unit"):
        return None
    start, finish = _weight_to_lbs(beginning), _weight_to_lbs(end)
    return None if start is None or finish is None else start - finish


def to_comparable(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reduce an extracted_features-shaped row to the values downstream consumers read.

    weight_loss_lbs_view is what the site shows today (start minus end weight, in the
    materialized view). weight_loss_lbs also uses the weight_lost column, which only
    reaches the site once the view reads it. drug_source goes through the same
    brand/compounded rule for every run, so no variant is scored on it alone.
    """
    primary = row.get("primary_drug")
    primary = _DRUG_BY_LOWER.get(primary.strip().lower(), primary) if isinstance(primary, str) else None
    lost = _weight_to_lbs(row.get("weight_lost"))
    view_loss = _compute_view_weight_loss(row.get("beginning_weight"), row.get("end_weight"))
    side_effects = sorted({
        to_canonical_side_effect(s.get("name", "")) for s in row.get("side_effects") or [] if isinstance(s, dict)
    })
    return {
        "post_type": row.get("post_type"),
        "treatment_status": row.get("treatment_status"),
        "primary_drug": primary,
        "drug_source": resolve_source_for_name(primary, row.get("drug_source")),
        "beginning_weight_lbs": _weight_to_lbs(row.get("beginning_weight")),
        "end_weight_lbs": _weight_to_lbs(row.get("end_weight")),
        "weight_loss_lbs_view": view_loss,
        "weight_loss_lbs": lost if lost is not None else view_loss,
        "duration_weeks": row.get("duration_weeks"),
        "cost_per_month": row.get("cost_per_month"),
        "has_insurance": row.get("has_insurance"),
        "side_effects": side_effects,
        "sentiment_post": row.get("sentiment_post"),
        "recommendation_score": row.get("recommendation_score"),
        "age": row.get("age"),
        "sex": row.get("sex"),
        "country": row.get("country"),
    }
