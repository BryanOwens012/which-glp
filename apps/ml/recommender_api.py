#!/usr/bin/env python3
"""
API wrapper for the ML recommender system.
Accepts JSON input via command line and returns JSON output.
"""

import sys
import json
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
from ml.recommender import DrugRecommender, UserProfile, DrugRecommendation

# Load environment variables
load_dotenv()


def get_supabase_client() -> Client:
    """Initialize Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")

    return create_client(url, key)


def fetch_experiences(supabase: Client, limit: int = 1000) -> pd.DataFrame:
    """Fetch experiences from Supabase."""
    response = supabase.table('mv_experiences_denormalized') \
        .select('*') \
        .not_.is_('primary_drug', 'null') \
        .not_.is_('weight_loss_lbs', 'null') \
        .limit(limit) \
        .execute()

    if not response.data:
        raise ValueError("No experiences found in database")

    return pd.DataFrame(response.data)


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


def main():
    """Main API function."""
    try:
        # Parse input from command line argument
        if len(sys.argv) < 2:
            raise ValueError("Missing input JSON argument")

        input_json = sys.argv[1]
        input_data = json.loads(input_json)

        # Create user profile with defaults for optional fields
        user = UserProfile(
            current_weight=input_data['currentWeight'],
            weight_unit=input_data['weightUnit'],
            goal_weight=input_data['goalWeight'],
            age=input_data.get('age', 35),  # Default to 35 if not provided
            sex=input_data.get('sex', 'other'),  # Default to 'other' if not provided
            state=input_data.get('state'),
            country=input_data.get('country', 'USA'),
            comorbidities=input_data.get('comorbidities', []),
            has_insurance=input_data.get('hasInsurance', False),
            insurance_provider=input_data.get('insuranceProvider'),
            max_budget=input_data.get('maxBudget'),
            side_effect_concerns=input_data.get('sideEffectConcerns', []),
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

        # Convert to dict for JSON serialization
        recommendations_dict = [recommendation_to_dict(rec) for rec in recommendations]

        # Output JSON result
        result = {
            'recommendations': recommendations_dict,
            'totalExperiences': len(experiences_df),
        }

        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        # Return error as JSON
        error_result = {
            'error': str(e),
            'recommendations': [],
        }
        print(json.dumps(error_result))
        sys.exit(1)


if __name__ == "__main__":
    main()
