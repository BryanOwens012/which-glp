"""
ML-based drug recommendation system for WhichGLP.

Uses k-Nearest Neighbors (k-NN) to find similar user experiences and
aggregate outcomes to generate personalized drug recommendations.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """User input for generating recommendations."""
    current_weight: float
    weight_unit: str  # "lbs" or "kg"
    goal_weight: float
    age: int
    sex: str  # "male", "female", "ftm", "mtf", "other"
    state: Optional[str] = None
    country: str = "USA"
    comorbidities: List[str] = None
    has_insurance: bool = False
    insurance_provider: Optional[str] = None
    max_budget: Optional[float] = None
    side_effect_concerns: List[str] = None

    def __post_init__(self):
        if self.comorbidities is None:
            self.comorbidities = []
        if self.side_effect_concerns is None:
            self.side_effect_concerns = []


@dataclass
class DrugRecommendation:
    """Recommendation result for a specific drug."""
    drug: str
    match_score: float
    expected_weight_loss: Dict[str, float]
    success_rate: float
    estimated_cost: Optional[float]
    side_effect_probability: List[Dict[str, Any]]
    similar_user_count: int
    pros: List[str]
    cons: List[str]


class DrugRecommender:
    """
    ML-based drug recommendation system using k-NN similarity.

    Algorithm:
    1. Convert user profile to feature vector
    2. Find k most similar experiences for each drug
    3. Aggregate outcomes (weight loss, side effects, cost)
    4. Calculate match scores based on similarity and outcomes
    5. Return ranked recommendations
    """

    def __init__(
        self,
        k_neighbors: int = 15,
        min_similar_users: int = 5,
        feature_weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize recommender.

        Args:
            k_neighbors: Number of similar users to find per drug
            min_similar_users: Minimum similar users required to recommend a drug
            feature_weights: Custom weights for features (age, sex, weight, etc.)
        """
        self.k = k_neighbors
        self.min_similar_users = min_similar_users

        # Default feature weights (sum to 1.0)
        self.weights = feature_weights or {
            'age': 0.15,
            'sex': 0.10,
            'weight': 0.30,
            'bmi_similarity': 0.20,
            'comorbidities': 0.15,
            'insurance': 0.10,
        }

        self.scaler = StandardScaler()

    def _convert_weight_to_lbs(self, weight: float, unit: str) -> float:
        """Convert weight to pounds for standardization."""
        if unit.lower() == 'kg':
            return weight * 2.20462
        return weight

    def _calculate_bmi(self, weight_lbs: float) -> float:
        """
        Estimate BMI category (simplified - assumes average height).
        In production, would collect height from user.
        """
        # Assume average height: 5'7" (67 inches) for rough BMI categories
        avg_height_inches = 67
        bmi = (weight_lbs / (avg_height_inches ** 2)) * 703
        return bmi

    def _extract_user_features(self, user: UserProfile) -> np.ndarray:
        """
        Convert user profile to numerical feature vector.

        Features:
        - Age (normalized)
        - Sex (one-hot)
        - Current weight in lbs
        - BMI category
        - Goal weight loss percentage
        - Comorbidities (binary indicators)
        - Insurance status
        """
        weight_lbs = self._convert_weight_to_lbs(user.current_weight, user.weight_unit)
        goal_lbs = self._convert_weight_to_lbs(user.goal_weight, user.weight_unit)
        weight_loss_goal_pct = ((weight_lbs - goal_lbs) / weight_lbs) * 100
        bmi = self._calculate_bmi(weight_lbs)

        features = {
            'age': user.age,
            'sex_male': 1.0 if user.sex == 'male' else 0.0,
            'sex_female': 1.0 if user.sex == 'female' else 0.0,
            'current_weight_lbs': weight_lbs,
            'bmi': bmi,
            'weight_loss_goal_pct': weight_loss_goal_pct,
            'has_insurance': 1.0 if user.has_insurance else 0.0,

            # Comorbidity indicators
            'comorbidity_diabetes': 1.0 if 'diabetes' in user.comorbidities else 0.0,
            'comorbidity_pcos': 1.0 if 'pcos' in user.comorbidities else 0.0,
            'comorbidity_hypertension': 1.0 if 'hypertension' in user.comorbidities else 0.0,
            'comorbidity_sleep_apnea': 1.0 if 'sleep apnea' in user.comorbidities else 0.0,
            'comorbidity_hypothyroidism': 1.0 if 'hypothyroidism' in user.comorbidities else 0.0,
        }

        return np.array(list(features.values()))

    def _extract_experience_features(self, experience: pd.Series) -> np.ndarray:
        """
        Convert database experience to numerical feature vector.
        Must match the structure of _extract_user_features.
        """
        # Helper to safely get numeric values, replacing None/NaN with default
        def safe_float(value, default=0.0):
            if value is None or (isinstance(value, float) and np.isnan(value)):
                return default
            return float(value)

        # Parse weight data
        beginning_weight_lbs = safe_float(experience.get('beginning_weight_lbs'), 0)
        weight_loss_lbs = safe_float(experience.get('weight_loss_lbs'), 0)
        weight_loss_pct = safe_float(experience.get('weight_loss_percentage'), 0)

        bmi = self._calculate_bmi(beginning_weight_lbs) if beginning_weight_lbs > 0 else 0

        # Parse comorbidities from array
        comorbidities = experience.get('comorbidities', []) or []
        if isinstance(comorbidities, str):
            comorbidities = []

        features = {
            'age': safe_float(experience.get('age'), 30),  # Default to 30 if missing
            'sex_male': 1.0 if experience.get('sex') == 'male' else 0.0,
            'sex_female': 1.0 if experience.get('sex') == 'female' else 0.0,
            'current_weight_lbs': beginning_weight_lbs,
            'bmi': bmi,
            'weight_loss_goal_pct': weight_loss_pct,
            'has_insurance': 1.0 if experience.get('has_insurance') else 0.0,

            # Comorbidity indicators
            'comorbidity_diabetes': 1.0 if 'diabetes' in comorbidities else 0.0,
            'comorbidity_pcos': 1.0 if 'pcos' in comorbidities else 0.0,
            'comorbidity_hypertension': 1.0 if 'hypertension' in comorbidities else 0.0,
            'comorbidity_sleep_apnea': 1.0 if 'sleep apnea' in comorbidities else 0.0,
            'comorbidity_hypothyroidism': 1.0 if 'hypothyroidism' in comorbidities else 0.0,
        }

        return np.array(list(features.values()), dtype=np.float64)

    def _calculate_similarity(
        self,
        user_features: np.ndarray,
        experience_features: np.ndarray
    ) -> float:
        """
        Calculate weighted cosine similarity between user and experience.
        """
        # Reshape for sklearn
        user_vec = user_features.reshape(1, -1)
        exp_vec = experience_features.reshape(1, -1)

        # Calculate cosine similarity
        similarity = cosine_similarity(user_vec, exp_vec)[0][0]

        return max(0, similarity)  # Ensure non-negative

    def _find_similar_experiences(
        self,
        user: UserProfile,
        experiences_df: pd.DataFrame,
        drug: str
    ) -> pd.DataFrame:
        """
        Find k most similar experiences for a specific drug.
        """
        # Filter to drug
        drug_experiences = experiences_df[experiences_df['primary_drug'] == drug].copy()

        if len(drug_experiences) == 0:
            return pd.DataFrame()

        # Extract user features
        user_features = self._extract_user_features(user)

        # Calculate similarity for each experience
        similarities = []
        for idx, exp in drug_experiences.iterrows():
            exp_features = self._extract_experience_features(exp)
            similarity = self._calculate_similarity(user_features, exp_features)
            similarities.append(similarity)

        drug_experiences['similarity'] = similarities

        # Sort by similarity and take top k
        similar_experiences = drug_experiences.nlargest(self.k, 'similarity')

        logger.info(f"Found {len(similar_experiences)} similar experiences for {drug}")
        return similar_experiences

    def _aggregate_outcomes(
        self,
        similar_experiences: pd.DataFrame,
        user: UserProfile
    ) -> Dict[str, Any]:
        """
        Aggregate outcomes from similar experiences.
        """
        if len(similar_experiences) == 0:
            return None

        # Weight loss statistics
        weight_losses = similar_experiences['weight_loss_lbs'].dropna()

        # Convert to user's preferred unit
        if user.weight_unit.lower() == 'kg':
            weight_losses = weight_losses / 2.20462

        # Side effects aggregation
        side_effects_counts = {}
        for side_effects in similar_experiences['side_effects']:
            if isinstance(side_effects, list):
                for se in side_effects:
                    if isinstance(se, dict) and 'name' in se:
                        # Normalize to title case to avoid duplicates (e.g., "nausea" vs "Nausea")
                        name = se['name'].strip().title() if se['name'] else ''
                        if not name:
                            continue
                        severity = se.get('severity', 'moderate')
                        if name not in side_effects_counts:
                            side_effects_counts[name] = {'count': 0, 'severity': severity}
                        side_effects_counts[name]['count'] += 1

        # Top side effects with probability
        total_users = len(similar_experiences)
        top_side_effects = []
        for se_name, se_data in sorted(
            side_effects_counts.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:5]:
            top_side_effects.append({
                'effect': se_name,
                'probability': round((se_data['count'] / total_users) * 100),  # Round to whole percentage
                'severity': se_data['severity']
            })

        # Cost statistics
        costs = similar_experiences['cost_per_month'].dropna()

        # Success rate (users who achieved >10% weight loss)
        weight_loss_pcts = similar_experiences['weight_loss_percentage'].dropna()
        success_count = (weight_loss_pcts >= 10).sum()
        success_rate = round((success_count / len(weight_loss_pcts)) * 100) if len(weight_loss_pcts) > 0 else 0

        return {
            'weight_loss_min': weight_losses.min() if len(weight_losses) > 0 else 0,
            'weight_loss_max': weight_losses.max() if len(weight_losses) > 0 else 0,
            'weight_loss_avg': weight_losses.mean() if len(weight_losses) > 0 else 0,
            'success_rate': success_rate,
            'estimated_cost': costs.median() if len(costs) > 0 else None,
            'side_effects': top_side_effects,
            'similar_user_count': total_users,
            'avg_similarity': similar_experiences['similarity'].mean()
        }

    def _calculate_match_score(
        self,
        outcomes: Dict[str, Any],
        user: UserProfile
    ) -> float:
        """
        Calculate match score (0-100) based on outcomes and user preferences.

        Factors:
        - Average similarity to found users (40%)
        - Success rate (30%)
        - Budget fit (20%)
        - Side effect concerns (10%)
        """
        if not outcomes:
            return 0

        # Similarity score (0-100)
        similarity_score = outcomes['avg_similarity'] * 100

        # Success rate score (0-100)
        success_score = outcomes['success_rate']

        # Budget score (0-100)
        budget_score = 100
        if user.max_budget and outcomes['estimated_cost']:
            if outcomes['estimated_cost'] <= user.max_budget:
                budget_score = 100
            elif outcomes['estimated_cost'] <= user.max_budget * 1.5:
                budget_score = 70
            else:
                budget_score = 40

        # Side effect score (0-100) - penalize if concerns match common side effects
        side_effect_score = 100
        if user.side_effect_concerns and outcomes['side_effects']:
            concern_count = 0
            for se in outcomes['side_effects']:
                if se['effect'] in user.side_effect_concerns:
                    concern_count += 1
            # Reduce score based on how many concerns appear
            side_effect_score = max(0, 100 - (concern_count * 20))

        # Weighted average
        match_score = (
            similarity_score * 0.40 +
            success_score * 0.30 +
            budget_score * 0.20 +
            side_effect_score * 0.10
        )

        return min(100, max(0, match_score))

    def _generate_pros_cons(
        self,
        drug: str,
        outcomes: Dict[str, Any],
        user: UserProfile
    ) -> Tuple[List[str], List[str]]:
        """Generate pros and cons list for a drug recommendation."""
        pros = []
        cons = []

        # Weight loss pros/cons
        if outcomes['weight_loss_avg'] > 30:
            pros.append(f"High average weight loss ({outcomes['weight_loss_avg']:.1f} {user.weight_unit})")
        elif outcomes['weight_loss_avg'] < 20:
            cons.append(f"Moderate average weight loss ({outcomes['weight_loss_avg']:.1f} {user.weight_unit})")

        # Success rate
        if outcomes['success_rate'] >= 80:
            pros.append(f"High success rate ({outcomes['success_rate']:.0f}%)")
        elif outcomes['success_rate'] < 70:
            cons.append(f"Moderate success rate ({outcomes['success_rate']:.0f}%)")

        # Cost
        if outcomes['estimated_cost']:
            if user.has_insurance and outcomes['estimated_cost'] < 50:
                pros.append("Good insurance coverage")
            elif not user.has_insurance and outcomes['estimated_cost'] < 500:
                pros.append("Relatively affordable without insurance")
            elif outcomes['estimated_cost'] > 1000:
                cons.append("High out-of-pocket cost")

        # Side effects
        if len(outcomes['side_effects']) <= 2:
            pros.append("Fewer reported side effects")
        elif len(outcomes['side_effects']) >= 4:
            cons.append("Multiple common side effects reported")

        # Similar user count
        if outcomes['similar_user_count'] >= 30:
            pros.append(f"Strong data from {outcomes['similar_user_count']} similar users")
        elif outcomes['similar_user_count'] < 10:
            cons.append(f"Limited data (only {outcomes['similar_user_count']} similar users)")

        return pros, cons

    def recommend(
        self,
        user: UserProfile,
        experiences_df: pd.DataFrame
    ) -> List[DrugRecommendation]:
        """
        Generate drug recommendations for a user.

        Args:
            user: User profile with demographics and preferences
            experiences_df: DataFrame of all experiences from database

        Returns:
            List of DrugRecommendation objects, sorted by match score
        """
        # Get unique drugs with sufficient data
        drug_counts = experiences_df['primary_drug'].value_counts()
        eligible_drugs = drug_counts[drug_counts >= self.min_similar_users].index.tolist()

        logger.info(f"Generating recommendations for {len(eligible_drugs)} drugs")

        recommendations = []

        for drug in eligible_drugs:
            # Find similar experiences
            similar_experiences = self._find_similar_experiences(user, experiences_df, drug)

            if len(similar_experiences) < self.min_similar_users:
                logger.debug(f"Skipping {drug} - only {len(similar_experiences)} similar users")
                continue

            # Aggregate outcomes
            outcomes = self._aggregate_outcomes(similar_experiences, user)

            if not outcomes:
                continue

            # Calculate match score
            match_score = self._calculate_match_score(outcomes, user)

            # Generate pros/cons
            pros, cons = self._generate_pros_cons(drug, outcomes, user)

            # Create recommendation
            recommendation = DrugRecommendation(
                drug=drug,
                match_score=round(match_score),  # Round to whole percentage
                expected_weight_loss={
                    'min': round(outcomes['weight_loss_min'], 1),
                    'max': round(outcomes['weight_loss_max'], 1),
                    'avg': round(outcomes['weight_loss_avg'], 1),
                    'unit': user.weight_unit
                },
                success_rate=outcomes['success_rate'],  # Already rounded to whole percentage
                estimated_cost=round(outcomes['estimated_cost']) if outcomes['estimated_cost'] else None,
                side_effect_probability=outcomes['side_effects'],
                similar_user_count=outcomes['similar_user_count'],
                pros=pros,
                cons=cons
            )

            recommendations.append(recommendation)

        # Sort by match score (descending)
        recommendations.sort(key=lambda r: r.match_score, reverse=True)

        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations
