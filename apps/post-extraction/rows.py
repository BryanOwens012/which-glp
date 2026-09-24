"""
Deterministic post-processing between the model's PostExtraction and the database.

Kept out of the prompt because each has one right answer:
- ground_extraction: null any quoted value whose quote is not in the post or is too
  short to ground anything, any weight whose quote does not state its number, any
  duration whose quote names no number, time, or treatment start, and any cost whose
  quote states no amount.
- has_weight_conflict: flag a stated weight_lost that disagrees with the start and end
  weights (logged, not corrected).
- to_feature_row: shape an extraction into an `extracted_features` row, deriving the
  legacy columns (drugs_mentioned, drug_sentiments, drug_source) from `drugs` and
  filling weight_lost from the start and end weights when the post gives both.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional

from schema import DrugUse, PostExtraction, SideEffect, Weight
from vocab import BRAND_DRUGS, COMPOUNDED_DRUGS, KG_TO_LBS, TAKEN_RELATIONS

EXTRACTION_VERSION = "post-v2"

# Start and end weights this close are treated as agreeing with a stated weight_lost.
WEIGHT_LOST_TOLERANCE_LBS = 3.0

_QUOTE_VARIANTS = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-"})


def build_source_text(title: Optional[str], flair: Optional[str], body: Optional[str]) -> str:
    """The post text quotes may come from: title, flair, and body, in prompt order."""
    return "\n".join(filter(None, [title, flair, body]))


def _normalize(text: str) -> str:
    """Casefold, drop Markdown emphasis, and collapse whitespace and quote/dash variants, so quotes match loosely."""
    text = unicodedata.normalize("NFKC", text).casefold().replace("*", "").replace("_", "")
    return re.sub(r"\s+", " ", text.translate(_QUOTE_VARIANTS)).strip()


# A quote shorter than this matches almost any post, so it grounds nothing.
MIN_QUOTE_CHARS = 3
# "13st 5lb", "13 stone 5": the prompt converts stone to lbs, so the quoted number differs.
# The pounds part counts only with a unit or at the end of the quote, so "18 stone 10
# weeks ago" is 18 stone, not 18 stone 10 lb.
_STONE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:st|stone)s?\b(?:\s*(\d+)(?=\s*(?:lbs?|pounds?)\b|\s*$))?"
)
# A thousands separator ("1,086"), as opposed to a decimal comma ("85,5").
_THOUSANDS_COMMA = re.compile(r"(?<=\d),(?=\d{3}\b)")
# A duration quote must name a number, a time ("since January", "a couple of months"),
# or the start of treatment ("just did my first shot" is 0 weeks).
_TIME_WORDS = re.compile(
    r"\d|\b(?:days?|weeks?|wks?|months?|mos?|years?|yrs?|fortnights?|"
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|"
    r"sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|"
    r"spring|summer|fall|autumn|winter|christmas|today|yesterday|ago|since|"
    r"first|doses?|shots?|injections?|jabs?|start(?:ed|ing|s)?)\b",
)


def _is_quote_found(quote: Optional[str], source: str) -> bool:
    normalized = _normalize(quote or "")
    return len(normalized) >= MIN_QUOTE_CHARS and normalized in source


def _is_number_in_quote(value: float, quote: Optional[str]) -> bool:
    """True when the quote states the value's whole number, or the same weight in stone."""
    # Only thousands separators are removed; a decimal comma ("85,5") stays a separator,
    # so its whole-number part is compared like "85.5".
    text = _THOUSANDS_COMMA.sub("", (quote or "").casefold())
    if str(int(value)) in re.findall(r"\d+", text):
        return True
    return any(
        abs(float(st) * 14 + int(lb or 0) - value) <= 1 for st, lb in _STONE.findall(text)
    )


def ground_extraction(extraction: PostExtraction, source_text: str) -> List[str]:
    """
    Null every quoted value whose quote does not appear in `source_text`, whose quote is
    too short to ground anything, or (for weights) that does not state the number; every
    duration whose quote names no number, time, or treatment start; and every cost whose quote states no
    amount.

    Args:
        extraction: The validated model output; modified in place.
        source_text: The post's title, flair, and body (build_source_text), the only
            text quotes may come from.

    Returns:
        Names of the fields that were nulled, for logging and evaluation.
    """
    source = _normalize(source_text)
    dropped: List[str] = []
    for field in ("beginning_weight", "end_weight", "weight_lost"):
        weight: Optional[Weight] = getattr(extraction, field)
        if weight is not None and not (
            _is_quote_found(weight.quote, source) and _is_number_in_quote(weight.value, weight.quote)
        ):
            setattr(extraction, field, None)
            dropped.append(field)
    if extraction.duration_weeks is not None and not (
        _is_quote_found(extraction.duration_quote, source)
        and _TIME_WORDS.search((extraction.duration_quote or "").casefold())
    ):
        extraction.duration_weeks = None
        dropped.append("duration_weeks")
    # A cost may be converted to a monthly figure ("$900 for 3 months" is 300), so its
    # quote only has to state some amount.
    if extraction.cost_per_month is not None and not (
        _is_quote_found(extraction.cost_quote, source) and re.search(r"\d", extraction.cost_quote or "")
    ):
        extraction.cost_per_month = None
        extraction.currency = None
        dropped.append("cost_per_month")
    return dropped


def to_lbs(value: float, unit: Optional[str]) -> Optional[float]:
    """A weight in lbs, or None for an unknown unit."""
    if unit == "kg":
        return value * KG_TO_LBS
    return value if unit == "lbs" else None


def compute_loss_lbs(start_lbs: Optional[float], end_lbs: Optional[float]) -> Optional[float]:
    """Start minus end weight in lbs; None when either is unknown or there was no loss."""
    if start_lbs is None or end_lbs is None:
        return None
    lost = start_lbs - end_lbs
    return lost if lost > 0 else None


def derive_weight_lost(extraction: PostExtraction) -> Optional[Dict[str, Any]]:
    """
    Return the weight_lost column value: the stated loss, else start minus end weight.

    Every value carries `derived`; a derived one has no quote. Returns None when there is
    no loss to report, including a weight gain.
    """
    if extraction.weight_lost is not None:
        return {**extraction.weight_lost.model_dump(), "derived": False}
    start, end = extraction.beginning_weight, extraction.end_weight
    if start is None or end is None:
        return None
    lost_lbs = compute_loss_lbs(to_lbs(start.value, start.unit), to_lbs(end.value, end.unit))
    if lost_lbs is None:
        return None
    if start.unit == end.unit:
        value, unit = start.value - end.value, start.unit
    else:
        value, unit = lost_lbs, "lbs"
    return {"value": round(value, 1), "unit": unit, "quote": None, "derived": True}


def has_weight_conflict(extraction: PostExtraction) -> bool:
    """True when a stated weight_lost disagrees with the stated start and end weights."""
    start, end, lost = extraction.beginning_weight, extraction.end_weight, extraction.weight_lost
    if start is None or end is None or lost is None:
        return False
    # Signed on purpose (not compute_loss_lbs): a gain against a stated loss is a conflict.
    implied = to_lbs(start.value, start.unit) - to_lbs(end.value, end.unit)
    return abs(implied - to_lbs(lost.value, lost.unit)) > WEIGHT_LOST_TOLERANCE_LBS


def resolve_source_for_name(name: Optional[str], stated: Optional[str]) -> Optional[str]:
    """A brand or compounded canonical name settles the source; otherwise keep what the post said."""
    if name in BRAND_DRUGS:
        return "brand"
    if name in COMPOUNDED_DRUGS:
        return "compounded"
    return stated


def _resolve_drug_source(extraction: PostExtraction) -> Optional[str]:
    """
    The source of the primary drug. Only with no primary drug does it fall back to the
    first taken drug, so one drug's source is never attributed to another.
    """
    taken = [d for d in extraction.drugs if d.relation in TAKEN_RELATIONS]
    if extraction.primary_drug is None:
        return next((s for d in taken if (s := resolve_source_for_name(d.name, d.source))), None)
    if extraction.primary_drug == "Other":
        chosen = _choose_other_primary(extraction)
        return chosen.source if chosen else None
    stated = next((d.source for d in extraction.drugs if d.name == extraction.primary_drug and d.source), None)
    return resolve_source_for_name(extraction.primary_drug, stated)


def _format_display_name(drug: DrugUse) -> Optional[str]:
    """The canonical name, or the written name for "Other" (None when that is blank)."""
    if drug.name != "Other":
        return drug.name
    return (drug.other_name or "").strip().title() or None


def _choose_other_primary(extraction: PostExtraction) -> Optional[DrugUse]:
    """
    The drug a primary_drug of "Other" refers to: the first "Other" entry with a written
    name, preferring one the author takes.
    """
    others = sorted(
        (d for d in extraction.drugs if d.name == "Other"),
        key=lambda d: d.relation not in TAKEN_RELATIONS,
    )
    return next((d for d in others if _format_display_name(d)), None)


def _resolve_primary_drug(extraction: PostExtraction) -> Optional[str]:
    """The primary drug as stored: "Other" is replaced by the drug's written name."""
    if extraction.primary_drug != "Other":
        return extraction.primary_drug
    chosen = _choose_other_primary(extraction)
    return _format_display_name(chosen) if chosen else None


def _to_legacy_side_effect(effect: SideEffect) -> Optional[Dict[str, Any]]:
    """
    The side_effects column entry. Downstream counts by name, so an "other" effect is
    stored under the author's wording, and dropped when there is none.
    """
    row = effect.model_dump()
    if effect.name == "other":
        detail = (effect.detail or "").strip().lower()
        if not detail:
            return None
        row["name"] = detail
    return row


def to_feature_row(extraction: PostExtraction) -> Dict[str, Any]:
    """
    Map an extraction onto `extracted_features` columns (model-produced fields only).

    The caller adds identifiers and processing metadata (post_id, model_used, cost,
    tokens, processed_at, raw_response).
    """
    drug_sentiments = {
        name: d.sentiment
        for d in extraction.drugs
        if d.relation in TAKEN_RELATIONS and d.sentiment is not None and (name := _format_display_name(d))
    }
    return {
        "extraction_version": EXTRACTION_VERSION,
        "post_type": extraction.post_type,
        "treatment_status": extraction.treatment_status,
        "summary": extraction.summary,
        "drugs": [d.model_dump() for d in extraction.drugs],
        "drugs_mentioned": list(dict.fromkeys(filter(None, map(_format_display_name, extraction.drugs)))),
        "primary_drug": _resolve_primary_drug(extraction),
        "drug_sentiments": drug_sentiments,
        "drug_source": _resolve_drug_source(extraction),
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
        "side_effects": list(filter(None, map(_to_legacy_side_effect, extraction.side_effects))),
        "side_effect_timing": extraction.side_effect_timing,
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
        # Columns post-v2 no longer produces (resolution is per side effect now). Written
        # as null so a re-extraction upserted onto a v1 row clears the old values.
        "side_effect_resolution": None,
        "confidence_score": None,
    }
