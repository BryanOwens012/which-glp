# ML-Based Drug Recommendation System

## Overview

This module implements a machine learning-based drug recommendation system for WhichGLP using k-Nearest Neighbors (k-NN) similarity matching. It analyzes user profiles against historical experiences from the database to generate personalized drug recommendations.

## Algorithm

**k-Nearest Neighbors with Cosine Similarity**

1. **Feature Extraction**: Converts user profile and experiences into numerical feature vectors
2. **Similarity Calculation**: Uses cosine similarity to find the k most similar users for each drug
3. **Outcome Aggregation**: Aggregates weight loss, side effects, and costs from similar users
4. **Match Scoring**: Calculates 0-100 match score based on:
   - User similarity (40%)
   - Success rate (30%)
   - Budget fit (20%)
   - Side effect concerns (10%)

## Features

### Input Features (User Profile)
- Demographics: age, sex
- Weight profile: current weight, goal weight, BMI
- Health: comorbidities (diabetes, PCOS, hypertension, sleep apnea, hypothyroidism)
- Financial: insurance status, max budget
- Preferences: side effect concerns

### Output (Per Drug)
- **Match Score**: 0-100 similarity to successful users
- **Expected Weight Loss**: Min/max/average from similar users
- **Success Rate**: % of similar users achieving >10% weight loss
- **Estimated Cost**: Median monthly cost from similar users
- **Side Effect Probabilities**: % experiencing each side effect
- **Pros/Cons**: Personalized based on user preferences

## Files

### `recommender.py`
Core ML module with:
- `DrugRecommender`: Main recommendation engine
- `UserProfile`: Input dataclass for user information
- `DrugRecommendation`: Output dataclass for results

### `test_recommender.py`
Test script that:
- Fetches real experiences from Supabase
- Generates recommendations for a test user
- Pretty-prints results with match scores, expected outcomes, pros/cons

## Usage

### Testing Locally

```bash
cd /Users/bryan/Github/which-glp
source venv/bin/activate
cd apps/backend
python3 ml/test_recommender.py
```

### In Code

```python
from ml.recommender import DrugRecommender, UserProfile
import pandas as pd

# Create user profile
user = UserProfile(
    current_weight=220,
    weight_unit="lbs",
    goal_weight=180,
    age=35,
    sex="female",
    comorbidities=["pcos", "hypothyroidism"],
    has_insurance=True,
    max_budget=100,
    side_effect_concerns=["vomiting", "diarrhea"]
)

# Initialize recommender
recommender = DrugRecommender(
    k_neighbors=15,           # Find 15 similar users per drug
    min_similar_users=5       # Require at least 5 similar users
)

# Generate recommendations (requires pandas DataFrame of experiences)
recommendations = recommender.recommend(user, experiences_df)

# Access results
for rec in recommendations:
    print(f"{rec.drug}: {rec.match_score}% match")
    print(f"  Expected weight loss: {rec.expected_weight_loss['avg']} {rec.expected_weight_loss['unit']}")
    print(f"  Success rate: {rec.success_rate}%")
```

## Test Results

**Test User**: 35F, 220 lbs → 180 lbs, PCOS + hypothyroidism, insured, $100/month budget

### Top 3 Recommendations:

1. **Mounjaro** - 99.9% match
   - Expected: 36-148 lbs loss (avg 77 lbs)
   - Success rate: 100%
   - Cost: $12/month
   - 15 similar users

2. **Ozempic** - 99.9% match
   - Expected: 44-140 lbs loss (avg 71 lbs)
   - Success rate: 100%
   - 15 similar users

3. **Zepbound** - 97.9% match
   - Expected: 24-135 lbs loss (avg 86 lbs)
   - Success rate: 93%
   - 15 similar users

**Average match score across all drugs**: 92.8%

## Configuration

### Tunable Parameters

```python
DrugRecommender(
    k_neighbors=15,          # More neighbors = smoother estimates
    min_similar_users=5,     # Minimum data quality threshold
    feature_weights={        # Custom importance weights
        'age': 0.15,
        'sex': 0.10,
        'weight': 0.30,
        'bmi_similarity': 0.20,
        'comorbidities': 0.15,
        'insurance': 0.10,
    }
)
```

## Dependencies

- `scikit-learn>=1.7.2`: Machine learning algorithms
- `numpy>=2.3.3`: Numerical operations
- `pandas>=2.3.3`: Data manipulation
- `supabase>=2.21.1`: Database access

Install with:
```bash
pip install scikit-learn supabase
```

## Data Requirements

Requires the `mv_experiences_denormalized` materialized view with columns:
- `primary_drug`: Drug name
- `age`, `sex`: Demographics
- `beginning_weight_lbs`, `weight_loss_lbs`, `weight_loss_percentage`: Weight data
- `comorbidities`: Array of conditions
- `has_insurance`, `cost_per_month`: Financial data
- `side_effects`: JSON array of side effects

## Performance

- **Processing time**: ~100ms for 267 experiences, 8 drugs
- **Memory usage**: <50MB for typical datasets
- **Scalability**: O(n*m) where n=experiences, m=drugs
  - Handles 1000+ experiences easily
  - Consider caching for production

## Future Improvements

1. **Feature Engineering**:
   - Add dosage progression patterns
   - Include temporal features (plateaus, rebounds)
   - Weight by recency of experiences

2. **Algorithm Enhancements**:
   - Ensemble methods (combine k-NN with other models)
   - Personalized feature weights based on user priorities
   - Clustering to identify user archetypes

3. **Production Optimizations**:
   - Pre-compute embeddings for faster similarity search
   - Cache recommendations for common profiles
   - A/B testing framework for algorithm improvements

4. **Explainability**:
   - Show which similar users influenced the recommendation
   - Highlight key matching factors
   - Confidence intervals for predictions

## Integration with Backend

Next steps (not yet implemented):
1. Create tRPC endpoint: `recommendations.getForUser`
2. Add Redis caching for results
3. Connect frontend form to endpoint
4. Replace mock data in `/recommendations` page

## License

Part of the WhichGLP project.
