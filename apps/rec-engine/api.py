#!/usr/bin/env python3
"""
FastAPI service for ML recommendations.
Replaces the command-line wrapper with a proper HTTP API.
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client, Client
from dotenv import load_dotenv
from recommender import DrugRecommender, UserProfile, DrugRecommendation
from doppler_secrets import load_doppler_secrets
from supabase_key import install_log_redaction, redact_supabase_secrets, require_supabase_secret_key

# Load environment variables
load_dotenv()
install_log_redaction()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("rec-engine")

# The secrets this service reads; nothing else is requested from Doppler. Loaded
# here, before any client that reads one is built.
DOPPLER_SECRETS = (
    "INTERNAL_API_KEY",
    "SUPABASE_SECRET_KEY",
    "SUPABASE_URL",
)
load_doppler_secrets(DOPPLER_SECRETS)

# Fail at boot, not at the first /recommend request, on missing Supabase config.
SUPABASE_SECRET_KEY = require_supabase_secret_key(os.getenv("SUPABASE_SECRET_KEY"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
if not SUPABASE_URL:
    raise ValueError("Missing SUPABASE_URL environment variable")

app = FastAPI(title="WhichGLP ML API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class RecommendationRequest(BaseModel):
    currentWeight: float = Field(gt=0)
    weightUnit: str = Field(pattern="^(lbs|kg)$")
    goalWeight: float = Field(gt=0)
    age: Optional[int] = Field(default=35, ge=18, le=100)
    sex: Optional[str] = Field(default="other", pattern="^(male|female|other)$")
    state: Optional[str] = None
    country: str = "USA"
    comorbidities: List[str] = []
    hasInsurance: bool = False
    insuranceProvider: Optional[str] = None
    maxBudget: Optional[float] = None
    sideEffectConcerns: List[str] = []


class SideEffectProbability(BaseModel):
    effect: str
    probability: float
    severity: str


class ExpectedWeightLoss(BaseModel):
    min: float
    max: float
    avg: float
    unit: str


class RecommendationResponse(BaseModel):
    drug: str
    matchScore: float
    expectedWeightLoss: ExpectedWeightLoss
    successRate: float
    estimatedCost: Optional[float]
    sideEffectProbability: List[SideEffectProbability]
    similarUserCount: int
    pros: List[str]
    cons: List[str]


class RecommendationsResponse(BaseModel):
    recommendations: List[RecommendationResponse]
    totalExperiences: int
    processingTime: Optional[float] = None


async def verify_internal_api_key(x_internal_api_key: Optional[str] = Header(None)) -> None:
    expected = os.getenv("INTERNAL_API_KEY")
    if not expected:
        logger.warning("[Auth] INTERNAL_API_KEY not configured - skipping validation")
        return
    if not x_internal_api_key or x_internal_api_key != expected:
        raise HTTPException(status_code=403, detail="Forbidden")


# Initialize Supabase (cached)
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client."""
    global _supabase_client

    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

    return _supabase_client


# Cache experiences (refresh every 5 minutes in production)
_experiences_cache: Optional[pd.DataFrame] = None


def fetch_experiences(supabase: Client, limit: int = 1000) -> pd.DataFrame:
    """Fetch experiences from Supabase with caching."""
    global _experiences_cache

    # In production, add cache invalidation logic here
    if _experiences_cache is not None:
        return _experiences_cache

    response = supabase.table('mv_experiences_denormalized') \
        .select('*') \
        .not_.is_('primary_drug', 'null') \
        .not_.is_('weight_loss_lbs', 'null') \
        .limit(limit) \
        .execute()

    if not response.data:
        raise ValueError("No experiences found in database")

    _experiences_cache = pd.DataFrame(response.data)
    return _experiences_cache


def recommendation_to_dict(rec: DrugRecommendation) -> dict:
    """Convert DrugRecommendation dataclass to dict."""
    return {
        'drug': rec.drug,
        'matchScore': rec.match_score,
        'expectedWeightLoss': rec.expected_weight_loss,
        'successRate': rec.success_rate,
        'estimatedCost': rec.estimated_cost,
        'sideEffectProbability': rec.side_effect_probability,
        'similarUserCount': rec.similar_user_count,
        'pros': rec.pros,
        'cons': rec.cons,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rec-engine-api"}


@app.post("/api/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(request: RecommendationRequest, _: None = Depends(verify_internal_api_key)):
    """
    Generate drug recommendations based on user profile.
    """
    logger.info("[ML API] Received recommendation request: %s", request.dict())
    try:
        # Create user profile
        user = UserProfile(
            current_weight=request.currentWeight,
            weight_unit=request.weightUnit,
            goal_weight=request.goalWeight,
            age=request.age,
            sex=request.sex,
            state=request.state,
            country=request.country,
            comorbidities=request.comorbidities,
            has_insurance=request.hasInsurance,
            insurance_provider=request.insuranceProvider,
            max_budget=request.maxBudget,
            side_effect_concerns=request.sideEffectConcerns,
        )

        # Fetch experiences
        supabase = get_supabase_client()
        experiences_df = fetch_experiences(supabase, limit=1000)

        # Initialize recommender
        recommender = DrugRecommender(
            k_neighbors=15,
            min_similar_users=5
        )

        # Generate recommendations
        recommendations = recommender.recommend(user, experiences_df)

        # Convert to dict for response
        recommendations_dict = [recommendation_to_dict(rec) for rec in recommendations]

        return {
            'recommendations': recommendations_dict,
            'totalExperiences': len(experiences_df),
        }

    except Exception as e:
        logger.exception("[ML API] ERROR: %s: %s", type(e).__name__, e)
        raise HTTPException(status_code=500, detail=redact_supabase_secrets(str(e)))


@app.get("/api/cache/clear")
async def clear_cache(_: None = Depends(verify_internal_api_key)):
    """Clear the experiences cache (admin endpoint)."""
    global _experiences_cache
    _experiences_cache = None
    return {"status": "cache cleared"}


if __name__ == "__main__":
    import uvicorn

    # Railway sets PORT env var, fall back to REC_ENGINE_PORT or 8001 for local dev
    port = int(os.getenv("PORT", os.getenv("REC_ENGINE_PORT", "8001")))

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
