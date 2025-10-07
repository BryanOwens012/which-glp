"""
Test script for the ML recommender system.
Fetches real data from Supabase and generates recommendations.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
from recommender import DrugRecommender, UserProfile

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def get_supabase_client() -> Client:
    """Initialize Supabase client."""
    url = os.getenv("SUPABASE_URL")
    # For read-only operations, we can use the anon key
    key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")

    return create_client(url, key)


def fetch_experiences(supabase: Client, limit: int = 1000) -> pd.DataFrame:
    """Fetch experiences from Supabase."""
    logger.info(f"Fetching up to {limit} experiences from database...")

    response = supabase.table('mv_experiences_denormalized') \
        .select('*') \
        .not_.is_('primary_drug', 'null') \
        .not_.is_('weight_loss_lbs', 'null') \
        .limit(limit) \
        .execute()

    if not response.data:
        raise ValueError("No experiences found in database")

    df = pd.DataFrame(response.data)
    logger.info(f"Fetched {len(df)} experiences")
    logger.info(f"Drugs: {df['primary_drug'].value_counts().to_dict()}")

    return df


def create_test_user() -> UserProfile:
    """Create a test user profile."""
    return UserProfile(
        current_weight=220,
        weight_unit="lbs",
        goal_weight=180,
        age=35,
        sex="female",
        state="California",
        country="USA",
        comorbidities=["pcos", "hypothyroidism"],
        has_insurance=True,
        insurance_provider="Blue Cross",
        max_budget=100,
        side_effect_concerns=["vomiting", "diarrhea"]
    )


def print_recommendations(recommendations):
    """Pretty print recommendations."""
    print("\n" + "="*80)
    print("DRUG RECOMMENDATIONS")
    print("="*80 + "\n")

    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec.drug}")
        print(f"   Match Score: {rec.match_score}%")
        print(f"   Expected Weight Loss: {rec.expected_weight_loss['min']}-{rec.expected_weight_loss['max']} {rec.expected_weight_loss['unit']} (avg: {rec.expected_weight_loss['avg']})")
        print(f"   Success Rate: {rec.success_rate}%")
        print(f"   Estimated Cost: ${rec.estimated_cost}/month" if rec.estimated_cost else "   Estimated Cost: N/A")
        print(f"   Similar Users: {rec.similar_user_count}")

        if rec.side_effect_probability:
            print("   Common Side Effects:")
            for se in rec.side_effect_probability:
                print(f"     - {se['effect']}: {se['probability']:.1f}% ({se['severity']})")

        if rec.pros:
            print("   Pros:")
            for pro in rec.pros:
                print(f"     ✓ {pro}")

        if rec.cons:
            print("   Cons:")
            for con in rec.cons:
                print(f"     ✗ {con}")

        print()


def main():
    """Main test function."""
    try:
        # Initialize Supabase
        supabase = get_supabase_client()

        # Fetch experiences
        experiences_df = fetch_experiences(supabase, limit=1000)

        # Create test user
        user = create_test_user()
        print("\nTest User Profile:")
        print(f"  Age: {user.age}, Sex: {user.sex}")
        print(f"  Current Weight: {user.current_weight} {user.weight_unit}")
        print(f"  Goal Weight: {user.goal_weight} {user.weight_unit}")
        print(f"  Comorbidities: {', '.join(user.comorbidities)}")
        print(f"  Has Insurance: {user.has_insurance}")
        print(f"  Max Budget: ${user.max_budget}/month")
        print(f"  Side Effect Concerns: {', '.join(user.side_effect_concerns)}")

        # Initialize recommender
        recommender = DrugRecommender(
            k_neighbors=15,
            min_similar_users=5
        )

        # Generate recommendations
        logger.info("Generating recommendations...")
        recommendations = recommender.recommend(user, experiences_df)

        # Print results
        print_recommendations(recommendations)

        # Summary statistics
        print("="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total recommendations: {len(recommendations)}")
        if recommendations:
            print(f"Top recommendation: {recommendations[0].drug} (match score: {recommendations[0].match_score}%)")
            print(f"Average match score: {sum(r.match_score for r in recommendations) / len(recommendations):.1f}%")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
