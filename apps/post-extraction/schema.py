"""
Pydantic model for post extraction.

`PostExtraction` is what the model returns. It is sent to OpenRouter as a strict JSON
schema, so every field is required (nullable where data may be missing), enumerations
come from vocab.py, and there are no free-form dicts. The `mode="before"` validators
repair near-misses (unit spellings, severity synonyms, a string where a list belongs)
for when a provider does not enforce the strict schema, so one odd value does not fail
the whole post.

rows.py turns a validated extraction into an `extracted_features` row.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from vocab import (
    CANONICAL_DRUGS,
    SEVERITY_SYNONYMS,
    SEVERITY_VALUES,
    SIDE_EFFECT_NAMES,
    WEIGHT_UNIT_SYNONYMS,
    CanonicalDrug,
    Currency,
    DrugRelation,
    DrugSource,
    PostType,
    Severity,
    Sex,
    SideEffectName,
    TreatmentStatus,
    WeightUnit,
)


class _Strict(BaseModel):
    """Base for every schema node: unknown keys are rejected, as strict mode requires."""

    model_config = ConfigDict(extra="forbid")


class Weight(_Strict):
    """A body weight, or an amount of weight, as the author stated it."""

    value: float = Field(..., gt=0, le=1000)
    unit: WeightUnit
    quote: str = Field(..., description="Shortest verbatim span of the post or flair that states this number")

    @field_validator("unit", mode="before")
    @classmethod
    def _normalize_unit(cls, v):
        if isinstance(v, str):
            v = v.strip().lower()
            return WEIGHT_UNIT_SYNONYMS.get(v, v)
        return v


class DrugUse(_Strict):
    """One drug the post names, and how the author relates to it."""

    name: CanonicalDrug
    other_name: Optional[str] = Field(..., description="The name as written when name is Other, else null")
    relation: DrugRelation
    source: Optional[DrugSource]
    sentiment: Optional[float] = Field(..., ge=0, le=1)

    @field_validator("name", mode="before")
    @classmethod
    def _canonicalize_name(cls, v):
        if isinstance(v, str):
            for canonical in CANONICAL_DRUGS:
                if v.strip().lower() == canonical.lower():
                    return canonical
        return v


class SideEffect(_Strict):
    """A side effect the author attributes to their GLP-1 use."""

    name: SideEffectName
    detail: Optional[str] = Field(..., description="The author's wording when name is other or it adds nuance")
    severity: Optional[Severity]
    resolved: Optional[bool]

    @field_validator("severity", mode="before")
    @classmethod
    def _normalize_severity(cls, v):
        """Map synonyms onto mild/moderate/severe; drop anything else rather than fail the post."""
        if not isinstance(v, str):
            return None
        v = v.strip().lower()
        return v if v in SEVERITY_VALUES else SEVERITY_SYNONYMS.get(v)

    @field_validator("name", mode="before")
    @classmethod
    def _normalize_name(cls, v):
        if isinstance(v, str) and v.strip().lower() in SIDE_EFFECT_NAMES:
            return v.strip().lower()
        return v


class PostExtraction(_Strict):
    """Everything extracted from one Reddit post. Field meanings are defined in prompts.py."""

    post_type: PostType
    summary: str

    # Drugs
    drugs: List[DrugUse]
    primary_drug: Optional[CanonicalDrug]
    treatment_status: TreatmentStatus
    dosage_progression: Optional[str]
    switching_drugs: Optional[str]

    # Outcomes
    beginning_weight: Optional[Weight]
    end_weight: Optional[Weight]
    weight_lost: Optional[Weight]
    duration_weeks: Optional[int] = Field(..., ge=0, le=520)
    duration_quote: Optional[str]
    plateau_mentioned: Optional[bool]
    rebound_weight_gain: Optional[bool]

    # Cost and access
    cost_per_month: Optional[float] = Field(..., ge=0, le=10000)
    currency: Optional[Currency]
    cost_quote: Optional[str]
    has_insurance: Optional[bool]
    insurance_provider: Optional[str]
    pharmacy_access_issues: Optional[bool]

    # Side effects and health
    side_effects: List[SideEffect]
    side_effect_timing: Optional[str]
    food_intolerances: List[str]
    comorbidities: List[str]
    labs_improvement: List[str]
    medication_reduction: List[str]
    nsv_mentioned: List[str]
    mental_health_impact: Optional[str]

    # Lifestyle
    exercise_frequency: Optional[str]
    dietary_changes: Optional[str]
    previous_weight_loss_attempts: List[str]
    support_system: Optional[str]

    # Sentiment
    sentiment_pre: Optional[float] = Field(..., ge=0, le=1)
    sentiment_post: Optional[float] = Field(..., ge=0, le=1)
    recommendation_score: Optional[float] = Field(..., ge=0, le=1)

    # Demographics
    age: Optional[int] = Field(..., ge=13, le=120)
    sex: Optional[Sex]
    location: Optional[str]
    state: Optional[str]
    country: Optional[str]

    @field_validator(
        "comorbidities",
        "food_intolerances",
        "labs_improvement",
        "medication_reduction",
        "nsv_mentioned",
        "previous_weight_loss_attempts",
        mode="before",
    )
    @classmethod
    def _lowercase_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            v = [v]
        return [item.strip().lower() for item in v if isinstance(item, str) and item.strip()]

    @field_validator("drugs", "side_effects", mode="before")
    @classmethod
    def _none_to_list(cls, v):
        return [] if v is None else v
