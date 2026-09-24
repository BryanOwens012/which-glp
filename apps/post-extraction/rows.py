"""
Deterministic post-processing between the model's PostExtraction and the database.

Two jobs, both kept out of the prompt because they have one right answer:
- ground_extraction: null any quoted number whose quote is not in the post, which
  catches invented values mechanically.
- to_feature_row: shape an extraction into an `extracted_features` row, deriving the
  legacy columns (drugs_mentioned, drug_sentiments, drug_source) from `drugs` and
  filling weight_lost from the start and end weights when the post gives both.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional

from schema import PostExtraction, Weight
from vocab import BRAND_DRUGS, COMPOUNDED_DRUGS, TAKEN_RELATIONS

EXTRACTION_VERSION = "post-v2"

KG_TO_LBS = 2.20462
# Start and end weights this close are treated as agreeing with a stated weight_lost.
WEIGHT_LOST_TOLERANCE_LBS = 3.0


def _normalize(text: str) -> str:
    """Casefold, drop Markdown emphasis, and collapse whitespace and quote/dash variants, so quotes match loosely."""
    text = unicodedata.normalize("NFKC", text).casefold().replace("*", "").replace("_", "")
    text = text.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-"}))
    return re.sub(r"\s+", " ", text).strip()


def _quote_found(quote: Optional[str], source: str) -> bool:
    return bool(quote) and _normalize(quote) in source


def ground_extraction(extraction: PostExtraction, source_text: str) -> List[str]:
    """
    Null every quoted value whose quote does not appear in `source_text`.

    Args:
        extraction: The validated model output; modified in place.
        source_text: Everything the model was shown about the post (title, flair, body).

    Returns:
        Names of the fields that were nulled, for logging and evaluation.
    """
    source = _normalize(source_text)
    dropped: List[str] = []
    for field in ("beginning_weight", "end_weight", "weight_lost"):
        weight: Optional[Weight] = getattr(extraction, field)
        if weight is not None and not _quote_found(weight.quote, source):
            setattr(extraction, field, None)
            dropped.append(field)
    if extraction.duration_weeks is not None and not _quote_found(extraction.duration_quote, source):
        extraction.duration_weeks = None
        dropped.append("duration_weeks")
    if extraction.cost_per_month is not None and not _quote_found(extraction.cost_quote, source):
        extraction.cost_per_month = None
        extraction.currency = None
        dropped.append("cost_per_month")
    return dropped


def _in_lbs(weight: Weight) -> float:
    return weight.value * KG_TO_LBS if weight.unit == "kg" else weight.value


def derive_weight_lost(extraction: PostExtraction) -> Optional[Dict[str, Any]]:
    """
    Return the weight_lost column value: the stated loss, else start minus end weight.

    A derived loss is marked with "derived": true and no quote. Returns None when there
    is no loss to report, including a weight gain.
    """
    if extraction.weight_lost is not None:
        return extraction.weight_lost.model_dump()
    start, end = extraction.beginning_weight, extraction.end_weight
    if start is None or end is None:
        return None
    lost_lbs = _in_lbs(start) - _in_lbs(end)
    if lost_lbs <= 0:
        return None
    if start.unit == end.unit:
        value, unit = start.value - end.value, start.unit
    else:
        value, unit = lost_lbs, "lbs"
    return {"value": round(value, 1), "unit": unit, "quote": None, "derived": True}


def weight_conflict(extraction: PostExtraction) -> bool:
    """True when a stated weight_lost disagrees with the stated start and end weights."""
    start, end, lost = extraction.beginning_weight, extraction.end_weight, extraction.weight_lost
    if start is None or end is None or lost is None:
        return False
    return abs((_in_lbs(start) - _in_lbs(end)) - _in_lbs(lost)) > WEIGHT_LOST_TOLERANCE_LBS


def source_for_name(name: Optional[str], stated: Optional[str]) -> Optional[str]:
    """A brand or compounded canonical name settles the source; otherwise keep what the post said."""
    if name in BRAND_DRUGS:
        return "brand"
    if name in COMPOUNDED_DRUGS:
        return "compounded"
    return stated


def _drug_source(extraction: PostExtraction) -> Optional[str]:
    """The source of the primary drug, falling back to the first taken drug with one."""
    if extraction.primary_drug in BRAND_DRUGS or extraction.primary_drug in COMPOUNDED_DRUGS:
        return source_for_name(extraction.primary_drug, None)
    taken = [d for d in extraction.drugs if d.relation in TAKEN_RELATIONS]
    for drug in taken:
        if drug.name == extraction.primary_drug and drug.source:
            return drug.source
    return next((d.source for d in taken if d.source), None)


def _display_name(drug) -> str:
    return drug.other_name.strip().title() if drug.name == "Other" and drug.other_name else drug.name


def to_feature_row(extraction: PostExtraction) -> Dict[str, Any]:
    """
    Map an extraction onto `extracted_features` columns (model-produced fields only).

    The caller adds identifiers and processing metadata (post_id, model_used, cost,
    tokens, processed_at, raw_response).
    """
    drug_sentiments = {
        _display_name(d): d.sentiment
        for d in extraction.drugs
        if d.relation in TAKEN_RELATIONS and d.sentiment is not None
    }
    return {
        "extraction_version": EXTRACTION_VERSION,
        "post_type": extraction.post_type,
        "treatment_status": extraction.treatment_status,
        "summary": extraction.summary,
        "drugs": [d.model_dump() for d in extraction.drugs],
        "drugs_mentioned": list(dict.fromkeys(_display_name(d) for d in extraction.drugs)),
        "primary_drug": extraction.primary_drug,
        "drug_sentiments": drug_sentiments,
        "drug_source": _drug_source(extraction),
        "dosage_progression": extraction.dosage_progression,
        "switching_drugs": extraction.switching_drugs,
        "beginning_weight": extraction.beginning_weight.model_dump() if extraction.beginning_weight else None,
        "end_weight": extraction.end_weight.model_dump() if extraction.end_weight else None,
        "weight_lost": derive_weight_lost(extraction),
        "duration_weeks": extraction.duration_weeks,
        "plateau_mentioned": extraction.plateau_mentioned,
        "rebound_weight_gain": extraction.rebound_weight_gain,
        "cost_per_month": extraction.cost_per_month,
        "currency": extraction.currency,
        "has_insurance": extraction.has_insurance,
        "insurance_provider": extraction.insurance_provider,
        "pharmacy_access_issues": extraction.pharmacy_access_issues,
        "side_effects": [s.model_dump() for s in extraction.side_effects],
        "side_effect_timing": extraction.side_effect_timing,
        "side_effect_resolution": None,
        "food_intolerances": extraction.food_intolerances,
        "comorbidities": extraction.comorbidities,
        "labs_improvement": extraction.labs_improvement,
        "medication_reduction": extraction.medication_reduction,
        "nsv_mentioned": extraction.nsv_mentioned,
        "mental_health_impact": extraction.mental_health_impact,
        "exercise_frequency": extraction.exercise_frequency,
        "dietary_changes": extraction.dietary_changes,
        "previous_weight_loss_attempts": extraction.previous_weight_loss_attempts,
        "support_system": extraction.support_system,
        "sentiment_pre": extraction.sentiment_pre,
        "sentiment_post": extraction.sentiment_post,
        "recommendation_score": extraction.recommendation_score,
        "age": extraction.age,
        "sex": extraction.sex,
        "location": extraction.location,
        "state": extraction.state,
        "country": extraction.country,
        "confidence_score": None,
    }
