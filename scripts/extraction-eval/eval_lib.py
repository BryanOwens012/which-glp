"""
Shared pieces of the post-extraction evaluation harness.

The harness scores extraction variants (prompt, schema, reasoning effort, grounding)
against gold labels on the same posts, so a prompt or model change is measured on real
inputs before it ships. Posts, gold labels, and run outputs live under
backups/extraction-eval/ (gitignored): they contain Reddit text.

Every variant is reduced to the same comparable record: the values downstream
consumers actually read (see mv_experiences_denormalized and get_drug_stats), computed
the way they compute them. The current extractor (v1) is the legacy prompt and schema in
scripts/legacy-ingestion/extraction/, which the deployed service used before post-v2.
"""

import importlib.util
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
POST_EXTRACTION = ROOT / "apps" / "post-extraction"
LEGACY_EXTRACTION = ROOT / "scripts" / "legacy-ingestion" / "extraction"
DATA_DIR = ROOT / "backups" / "extraction-eval"

sys.path.insert(0, str(POST_EXTRACTION))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from vocab import CANONICAL_DRUGS, SIDE_EFFECT_GUIDE, SIDE_EFFECT_NAMES  # noqa: E402

KG_TO_LBS = 2.20462


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


def source_text(post: Dict[str, Any]) -> str:
    """Everything the extractor sees about a post, for quote grounding."""
    return "\n".join(filter(None, [post.get("title"), post.get("author_flair_text"), post.get("body")]))


# --------------------------------------------------------------------------
# Comparable records
# --------------------------------------------------------------------------

_DRUG_BY_LOWER = {d.lower(): d for d in CANONICAL_DRUGS}


def _side_effect_synonyms() -> Dict[str, str]:
    synonyms = {name: name for name in SIDE_EFFECT_NAMES}
    for name, guide in SIDE_EFFECT_GUIDE.items():
        for phrase in guide.split(","):
            synonyms[phrase.strip().lower()] = name
    synonyms.update({
        "exhaustion": "fatigue", "tiredness": "fatigue", "low energy": "fatigue", "lethargy": "fatigue",
        "sulfur burps": "burping", "heartburn": "acid reflux", "migraine": "headache",
        "lightheadedness": "dizziness", "hair shedding": "hair loss", "loss of appetite": "reduced appetite",
        "decreased appetite": "reduced appetite", "stomach pain": "abdominal pain", "stomach cramps": "abdominal pain",
        "upset stomach": "abdominal pain", "hives": "allergic reaction", "sleep disruption": "insomnia",
        "sleep disturbance": "insomnia", "panic attack": "anxiety", "panic attacks": "anxiety",
        "anhedonia": "depression", "hypoglycemia": "low blood sugar", "elevated lipase": "pancreas problem",
        "pancreatitis": "pancreas problem", "gallstones": "gallbladder problem",
    })
    return synonyms


_SIDE_EFFECT_SYNONYMS = _side_effect_synonyms()


def canonical_side_effect(name: str) -> str:
    """Map free-text side-effect names (v1 output) onto the v2 vocabulary, generously."""
    name = (name or "").strip().lower()
    if name in _SIDE_EFFECT_SYNONYMS:
        return _SIDE_EFFECT_SYNONYMS[name]
    if name.startswith("injection site"):
        return "injection site reaction"
    return "other"


def _to_lbs(weight: Optional[Dict[str, Any]]) -> Optional[float]:
    if not weight or weight.get("value") is None:
        return None
    unit = weight.get("unit")
    if unit == "kg":
        return weight["value"] * KG_TO_LBS
    if unit == "lbs":
        return weight["value"]
    return None


def _view_weight_loss(beginning: Optional[dict], end: Optional[dict]) -> Optional[float]:
    """weight_loss_lbs the way mv_experiences_denormalized computes it: both weights, same unit."""
    if not beginning or not end or beginning.get("unit") != end.get("unit"):
        return None
    start, finish = _to_lbs(beginning), _to_lbs(end)
    return None if start is None or finish is None else start - finish


def comparable(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reduce an extracted_features-shaped row to the values downstream consumers read.

    weight_loss_lbs uses the row's weight_lost column when present (post-v2), else the
    view's start-minus-end formula (what v1 rows get today).
    """
    primary = row.get("primary_drug")
    lost = _to_lbs(row.get("weight_lost"))
    view_loss = _view_weight_loss(row.get("beginning_weight"), row.get("end_weight"))
    side_effects = sorted({canonical_side_effect(s.get("name", "")) for s in row.get("side_effects") or [] if isinstance(s, dict)})
    return {
        "post_type": row.get("post_type"),
        "treatment_status": row.get("treatment_status"),
        "primary_drug": _DRUG_BY_LOWER.get(primary.strip().lower(), primary) if isinstance(primary, str) else None,
        "drug_source": row.get("drug_source"),
        "beginning_weight_lbs": _to_lbs(row.get("beginning_weight")),
        "end_weight_lbs": _to_lbs(row.get("end_weight")),
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
