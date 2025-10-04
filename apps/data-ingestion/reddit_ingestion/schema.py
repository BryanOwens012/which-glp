"""
Pydantic models for AI-extracted data from Reddit posts and comments.

These schemas define the structure of data extracted by Claude AI,
ensuring type safety and validation before database insertion.
"""

from typing import Optional, List, Literal, Dict
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class WeightData(BaseModel):
    """Weight measurement with unit and confidence level"""
    value: Optional[float] = Field(None, description="Weight value (numeric)")
    unit: Optional[Literal["lbs", "kg"]] = Field(None, description="Unit of measurement")
    confidence: Optional[Literal["high", "medium", "low"]] = Field(
        None,
        description="Confidence in the extraction accuracy"
    )

    @field_validator("value")
    @classmethod
    def validate_weight(cls, v: Optional[float]) -> Optional[float]:
        """Ensure weight is positive if provided"""
        if v is not None and v <= 0:
            raise ValueError("Weight must be positive")
        if v is not None and v > 1000:  # Sanity check
            raise ValueError("Weight seems unrealistic (>1000)")
        return v


class SideEffectData(BaseModel):
    """Side effect with severity and confidence level"""
    name: str = Field(..., description="Name of the side effect (lowercase)")
    severity: Optional[Literal["mild", "moderate", "severe"]] = Field(
        None,
        description="Severity of the side effect"
    )
    confidence: Optional[Literal["high", "medium", "low"]] = Field(
        None,
        description="Confidence in the extraction accuracy"
    )


class ExtractedFeatures(BaseModel):
    """
    Complete structured data extracted from a Reddit post or comment.

    This model represents all features we want to extract from user experiences
    with GLP-1 medications.
    """

    # Summary (required)
    summary: str = Field(
        ...,
        description="First-person faithful summary of the user's experience",
        min_length=10,
        max_length=5000
    )

    # Weight data
    beginning_weight: Optional[WeightData] = Field(
        None,
        description="Starting weight before medication"
    )
    end_weight: Optional[WeightData] = Field(
        None,
        description="Current or ending weight"
    )

    # Duration
    duration_weeks: Optional[int] = Field(
        None,
        description="Duration of medication use in weeks",
        ge=0,
        le=520  # Max 10 years
    )

    # Cost
    cost_per_month: Optional[float] = Field(
        None,
        description="Out-of-pocket cost per month",
        ge=0,
        le=10000
    )
    currency: Optional[Literal["USD", "CAD", "GBP", "EUR", "AUD"]] = Field(
        "USD",
        description="Currency for cost"
    )

    # Drug information
    drugs_mentioned: List[str] = Field(
        default_factory=list,
        description="All drug names mentioned (e.g., Ozempic, Wegovy, Mounjaro)"
    )
    primary_drug: Optional[str] = Field(
        None,
        description="The main drug being discussed"
    )
    drug_sentiments: Dict[str, float] = Field(
        default_factory=dict,
        description="Sentiment score (0-1) toward each drug mentioned. 0=very negative, 0.5=neutral, 1=very positive"
    )

    # Overall sentiment
    sentiment_pre: Optional[float] = Field(
        None,
        description="Quality of life/sentiment BEFORE starting the drug (0-1). 0=very negative, 1=very positive",
        ge=0,
        le=1
    )
    sentiment_post: Optional[float] = Field(
        None,
        description="Quality of life/sentiment AFTER/while taking the drug (0-1). 0=very negative, 1=very positive",
        ge=0,
        le=1
    )
    recommendation_score: Optional[float] = Field(
        None,
        description="Likelihood they'd recommend this drug to a stranger in similar circumstances (0-1). 0=would not recommend, 1=strong recommendation",
        ge=0,
        le=1
    )

    # Insurance
    has_insurance: Optional[bool] = Field(
        None,
        description="Whether the user has insurance coverage"
    )
    insurance_provider: Optional[str] = Field(
        None,
        description="Name of insurance provider if mentioned"
    )

    # Side effects and comorbidities
    side_effects: List[SideEffectData] = Field(
        default_factory=list,
        description="List of side effects with severity and confidence"
    )
    comorbidities: List[str] = Field(
        default_factory=list,
        description="Pre-existing conditions mentioned (e.g., diabetes, pcos, hypertension, sleep apnea)"
    )
    location: Optional[str] = Field(
        None,
        description="Geographic location if mentioned (city, state, country)"
    )

    # Lifestyle and medical journey
    dosage_progression: Optional[str] = Field(
        None,
        description="How dose changed over time (e.g., 'started 2.5mg, now 7.5mg')"
    )
    exercise_frequency: Optional[str] = Field(
        None,
        description="How often they exercise (e.g., '3x/week', 'daily', 'none')"
    )
    dietary_changes: Optional[str] = Field(
        None,
        description="Dietary changes mentioned (e.g., 'low carb', 'calorie counting')"
    )
    previous_weight_loss_attempts: List[str] = Field(
        default_factory=list,
        description="Other weight loss methods tried before GLP-1s (e.g., 'keto', 'Weight Watchers')"
    )

    # Drug sourcing and switching
    drug_source: Optional[Literal["brand", "compounded", "other"]] = Field(
        None,
        description="Brand name, compounded, or other (e.g., foreign-sourced)"
    )
    switching_drugs: Optional[str] = Field(
        None,
        description="If they switched between different GLP-1s and reasons"
    )

    # Side effect details
    side_effect_timing: Optional[str] = Field(
        None,
        description="When side effects occurred (e.g., 'first 2 weeks', 'ongoing')"
    )
    side_effect_resolution: Optional[float] = Field(
        None,
        description="Degree of side effect improvement over time (0-1). 0=completely resolved, 0.5=somewhat better, 1=no improvement/worse",
        ge=0,
        le=1
    )
    food_intolerances: List[str] = Field(
        default_factory=list,
        description="Specific foods they can no longer tolerate"
    )

    # Weight loss journey details
    plateau_mentioned: Optional[bool] = Field(
        None,
        description="Whether they mention hitting a weight plateau"
    )
    rebound_weight_gain: Optional[bool] = Field(
        None,
        description="If they mention regaining weight after stopping"
    )

    # Health improvements
    labs_improvement: List[str] = Field(
        default_factory=list,
        description="Lab improvements mentioned (e.g., 'A1C down', 'cholesterol improved')"
    )
    medication_reduction: List[str] = Field(
        default_factory=list,
        description="Medications they were able to reduce/stop (e.g., 'metformin', 'blood pressure meds')"
    )
    nsv_mentioned: List[str] = Field(
        default_factory=list,
        description="Non-scale victories (e.g., 'more energy', 'clothes fit', 'can climb stairs')"
    )

    # Social and practical factors
    support_system: Optional[str] = Field(
        None,
        description="Mentions of support or lack thereof (e.g., 'family supportive', 'doing alone')"
    )
    pharmacy_access_issues: Optional[bool] = Field(
        None,
        description="Whether they mention difficulty finding medication in stock"
    )
    mental_health_impact: Optional[str] = Field(
        None,
        description="Mental health changes mentioned (e.g., 'less depressed', 'anxiety increased')"
    )

    # Demographics (for personalized predictions)
    age: Optional[int] = Field(
        None,
        description="Age of the user if mentioned",
        ge=13,  # Reddit minimum age
        le=120
    )
    sex: Optional[Literal["male", "female", "ftm", "mtf", "other"]] = Field(
        None,
        description="Sex/gender identity if mentioned. ftm=female-to-male trans, mtf=male-to-female trans"
    )
    state: Optional[str] = Field(
        None,
        description="US state if mentioned (e.g., 'California', 'NY', 'Texas')"
    )
    country: Optional[str] = Field(
        None,
        description="Country if mentioned (e.g., 'USA', 'Canada', 'UK')"
    )

    # Confidence score
    confidence_score: Optional[float] = Field(
        None,
        description="Overall confidence in extraction accuracy (0-1)",
        ge=0,
        le=1
    )

    @field_validator(
        "drugs_mentioned", "comorbidities", "previous_weight_loss_attempts",
        "food_intolerances", "labs_improvement", "medication_reduction", "nsv_mentioned",
        mode="before"
    )
    @classmethod
    def convert_none_to_empty_list(cls, v: Optional[List[str]], info) -> List[str]:
        """Convert None to empty list for all list fields"""
        if v is None:
            return []

        # Normalize based on field name
        field_name = info.field_name
        if field_name == "drugs_mentioned":
            return [drug.strip().title() for drug in v if drug.strip()]
        else:
            # Lowercase for all other list fields
            return [item.strip().lower() for item in v if item.strip()]

    @field_validator("side_effects", mode="before")
    @classmethod
    def normalize_side_effects(cls, v: Optional[List]) -> List[SideEffectData]:
        """Convert None to empty list and ensure SideEffectData objects"""
        if v is None:
            return []

        result = []
        for item in v:
            if isinstance(item, dict):
                # Normalize name to lowercase
                if "name" in item:
                    item["name"] = item["name"].strip().lower()
                result.append(SideEffectData(**item))
            elif isinstance(item, str):
                # Legacy support: convert string to SideEffectData
                result.append(SideEffectData(name=item.strip().lower()))
            elif isinstance(item, SideEffectData):
                result.append(item)

        return result

    @field_validator("drug_sentiments", mode="before")
    @classmethod
    def validate_drug_sentiments(cls, v: Optional[Dict[str, float]]) -> Dict[str, float]:
        """Validate sentiment scores are between 0 and 1"""
        if v is None:
            return {}
        validated = {}
        for drug, score in v.items():
            if not (0 <= score <= 1):
                raise ValueError(f"Sentiment score for {drug} must be between 0 and 1, got {score}")
            validated[drug.strip().title()] = score
        return validated


class ExtractionResult(BaseModel):
    """
    Complete result of AI extraction including metadata.

    This model is used for database insertion and includes both the extracted
    features and metadata about the extraction process.
    """

    # Source identifier (exactly one must be set)
    post_id: Optional[str] = Field(None, description="Reddit post ID if extracting from post")
    comment_id: Optional[str] = Field(None, description="Reddit comment ID if extracting from comment")

    # Extracted features
    features: ExtractedFeatures = Field(..., description="Extracted structured data")

    # Processing metadata
    model_used: str = Field(..., description="Claude model used (e.g., claude-sonnet-4-20250514)")
    processing_cost_usd: Optional[float] = Field(None, description="Cost in USD for this API call", ge=0)
    tokens_input: Optional[int] = Field(None, description="Input tokens used", ge=0)
    tokens_output: Optional[int] = Field(None, description="Output tokens generated", ge=0)
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds", ge=0)
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of extraction")

    # Raw response for debugging
    raw_response: Optional[dict] = Field(None, description="Full Claude API response")

    @field_validator("post_id", "comment_id")
    @classmethod
    def check_source(cls, v, info):
        """Ensure exactly one source is set"""
        # This validation happens at model level, not field level
        # We'll handle this in model_validator
        return v

    def model_post_init(self, __context):
        """Validate that exactly one source ID is set"""
        if (self.post_id is None and self.comment_id is None):
            raise ValueError("Either post_id or comment_id must be set")
        if (self.post_id is not None and self.comment_id is not None):
            raise ValueError("Cannot set both post_id and comment_id")


class ProcessingStats(BaseModel):
    """
    Statistics for a batch processing run.

    Tracks costs, timing, and success rates for monitoring.
    """

    total_processed: int = Field(0, description="Total items processed")
    total_success: int = Field(0, description="Successful extractions")
    total_failed: int = Field(0, description="Failed extractions")
    total_cost_usd: float = Field(0.0, description="Total cost in USD")
    total_tokens_input: int = Field(0, description="Total input tokens")
    total_tokens_output: int = Field(0, description="Total output tokens")
    total_time_seconds: float = Field(0.0, description="Total processing time")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def calculate_averages(self) -> dict:
        """Calculate average metrics"""
        if self.total_success == 0:
            return {
                "avg_cost_per_item": 0,
                "avg_tokens_per_item": 0,
                "avg_time_per_item_ms": 0
            }

        return {
            "avg_cost_per_item": self.total_cost_usd / self.total_success,
            "avg_tokens_per_item": (self.total_tokens_input + self.total_tokens_output) / self.total_success,
            "avg_time_per_item_ms": (self.total_time_seconds * 1000) / self.total_success
        }

    def mark_completed(self):
        """Mark the processing run as completed"""
        self.completed_at = datetime.utcnow()
