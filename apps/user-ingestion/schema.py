"""
Pydantic models for user demographic data extraction.

This defines the schema that GLM-4.5-Air should extract from Reddit user histories.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class UserDemographics(BaseModel):
    """
    Demographic data extracted from a Reddit user's post/comment history.

    This is what we ask GLM-4.5-Air to extract from analyzing
    a user's last 20 posts + 20 comments.
    """

    # Physical characteristics
    height_inches: Optional[float] = Field(
        default=None,
        description="Height in inches (e.g., 68.5 for 5'8.5\"). Extract from mentions like '5 foot 8', 'I'm 170cm', etc."
    )

    start_weight_lbs: Optional[float] = Field(
        default=None,
        description="Starting weight before GLP-1 medication in pounds. Extract from phrases like 'started at 200lbs', 'SW: 95kg', etc."
    )

    end_weight_lbs: Optional[float] = Field(
        default=None,
        description="Most recent/current weight mentioned in pounds. Extract from 'CW: 170lbs', 'now weigh 80kg', etc."
    )

    # Demographics
    age: Optional[int] = Field(
        default=None,
        ge=18,
        le=100,
        description="Age in years. Extract from mentions like 'I'm 35', '42F', 'I am a 28 year old', etc."
    )

    sex: Optional[str] = Field(
        default=None,
        description="Gender: 'male', 'female', 'other', or 'unknown'. Extract from '35M', 'I'm a woman', etc."
    )

    # Location
    state: Optional[str] = Field(
        default=None,
        description="US state (e.g., 'California', 'TX', 'New York'). Extract from 'I live in Texas', 'here in CA', etc."
    )

    country: Optional[str] = Field(
        default="USA",
        description="Country of residence. Extract if mentioned explicitly, otherwise default to USA."
    )

    # Medical conditions
    comorbidities: List[str] = Field(
        default_factory=list,
        description="Medical conditions mentioned (e.g., ['diabetes', 'PCOS', 'hypothyroidism']). Extract from mentions of diseases, conditions, diagnoses."
    )

    # Insurance
    has_insurance: Optional[bool] = Field(
        default=None,
        description="Whether user has insurance. Extract from mentions like 'my insurance covers it', 'no insurance', 'paying out of pocket', etc."
    )

    insurance_provider: Optional[str] = Field(
        default=None,
        description="Insurance provider name if mentioned (e.g., 'Blue Cross', 'Aetna', 'UnitedHealthcare', 'Kaiser'). Extract from explicit mentions."
    )

    # Extraction metadata
    confidence_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in extraction quality (0.0 = very uncertain, 1.0 = very certain). Based on how explicit the user's mentions are."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "height_inches": 68.5,
                "start_weight_lbs": 220.0,
                "end_weight_lbs": 185.0,
                "age": 35,
                "sex": "female",
                "state": "California",
                "country": "USA",
                "comorbidities": ["PCOS", "insulin resistance"],
                "has_insurance": True,
                "insurance_provider": "Blue Cross",
                "confidence_score": 0.85
            }
        }
