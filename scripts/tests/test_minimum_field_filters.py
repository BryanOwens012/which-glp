#!/usr/bin/env python3
"""
Test script for minimum_field_filters.py

Validates that the deterministic pre-filters correctly identify posts
that contain the minimum required fields (weight, duration, drug).
"""

import sys
from pathlib import Path

# Add apps/post-extraction to path so we can import the module
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "apps" / "post-extraction")
)

from minimum_field_filters import (
    passes_minimum_field_filter,
    diagnose_post,
    has_weight_mention,
    has_duration_mention,
    has_drug_mention,
)


def test_case(
    title: str,
    body: str,
    flair: str,
    subreddit: str,
    should_pass: bool,
    description: str,
):
    """Test a single case and print results."""
    result = passes_minimum_field_filter(title, body, flair, subreddit)
    status = "✅ PASS" if result == should_pass else "❌ FAIL"

    print(f"\n{status}: {description}")
    print(f"Expected: {should_pass}, Got: {result}")

    if result != should_pass:
        # Show diagnostic info for failures
        diagnosis = diagnose_post(title, body, flair, subreddit)
        print(f"Diagnosis: {diagnosis}")
        print(f"Title: {title[:100]}")
        print(f"Body: {body[:100]}")
        print(f"Flair: {flair}")
        print(f"Subreddit: {subreddit}")

    return result == should_pass


def run_tests():
    """Run all test cases."""
    print("=" * 80)
    print("MINIMUM FIELD FILTER TESTS")
    print("=" * 80)

    total = 0
    passed = 0

    # ========================================================================
    # POSITIVE TEST CASES - Should PASS filter (be processed by GLM)
    # ========================================================================

    print("\n" + "=" * 80)
    print("POSITIVE TEST CASES (Should pass filter)")
    print("=" * 80)

    # Test 1: Complete post with all fields
    total += 1
    if test_case(
        title="3 month Ozempic update",
        body="Started at 220 lbs, now down to 195 lbs after 12 weeks.",
        flair="35F 5'4\" SW:220 CW:195 GW:150",
        subreddit="Ozempic",
        should_pass=True,
        description="Complete post with weight, duration, and drug",
    ):
        passed += 1

    # Test 2: Weight from number in plausible range
    total += 1
    if test_case(
        title="Week 8 on Mounjaro",
        body="I'm 200 now, started at 215. Feeling great!",
        flair="",
        subreddit="Mounjaro",
        should_pass=True,
        description="Weight from plausible number (200, 215)",
    ):
        passed += 1

    # Test 3: Flair has weight info
    total += 1
    if test_case(
        title="Wegovy month 3",
        body="Started this journey back in January.",
        flair="SW:185 CW:170",
        subreddit="Wegovy",
        should_pass=True,
        description="Weight in flair (SW/CW), duration in body",
    ):
        passed += 1

    # Test 4: Using "pounds" keyword
    total += 1
    if test_case(
        title="Ozempic progress",
        body="Lost 20 pounds in 2 months!",
        flair="",
        subreddit="Ozempic",
        should_pass=True,
        description="'pounds' keyword + duration + drug",
    ):
        passed += 1

    # Test 5: Using "kg" keyword
    total += 1
    if test_case(
        title="Mounjaro 6 week update",
        body="Down from 95 kg to 88 kg",
        flair="",
        subreddit="Mounjaro",
        should_pass=True,
        description="'kg' keyword + duration + drug",
    ):
        passed += 1

    # Test 6: Duration in title
    total += 1
    if test_case(
        title="Year 1 on semaglutide",
        body="240 to 200 lbs!",
        flair="",
        subreddit="semaglutide",
        should_pass=True,
        description="Duration in title, weight in body",
    ):
        passed += 1

    # Test 7: "Started" as duration keyword
    total += 1
    if test_case(
        title="Zepbound update",
        body="I started at 180 lbs, now at 165.",
        flair="",
        subreddit="zepbound",
        should_pass=True,
        description="'started' keyword + weight + drug",
    ):
        passed += 1

    # ========================================================================
    # NEGATIVE TEST CASES - Should FAIL filter (skip GLM processing)
    # ========================================================================

    print("\n" + "=" * 80)
    print("NEGATIVE TEST CASES (Should fail filter)")
    print("=" * 80)

    # Test 8: Missing weight
    total += 1
    if test_case(
        title="3 months on Ozempic",
        body="Been taking this for 12 weeks now.",
        flair="",
        subreddit="Ozempic",
        should_pass=False,
        description="Missing weight information",
    ):
        passed += 1

    # Test 9: Missing duration
    total += 1
    if test_case(
        title="Ozempic question",
        body="I'm 200 lbs, was 220 lbs. Taking Ozempic.",
        flair="",
        subreddit="Ozempic",
        should_pass=False,
        description="Missing duration/time information",
    ):
        passed += 1

    # Test 10: Missing specific drug name (but "weight loss" is a valid keyword)
    total += 1
    if test_case(
        title="Progress update",
        body="Lost 20 lbs in 3 months, from 200 to 180.",
        flair="",
        subreddit="loseit",
        should_pass=False,
        description="Missing drug-related keywords",
    ):
        passed += 1

    # Test 11: Very short, low-quality post
    total += 1
    if test_case(
        title="Question",
        body="Anyone tried Ozempic?",
        flair="",
        subreddit="Ozempic",
        should_pass=False,
        description="No weight or duration mentioned",
    ):
        passed += 1

    # Test 12: Off-topic post
    total += 1
    if test_case(
        title="Intermittent fasting results",
        body="I've been fasting for 6 months and lost 30 lbs, from 200 to 170.",
        flair="",
        subreddit="intermittentfasting",
        should_pass=False,
        description="Has weight and duration but no GLP-1 drug",
    ):
        passed += 1

    # Test 13: Weight number outside plausible range
    total += 1
    if test_case(
        title="Ozempic update",
        body="Started 3 months ago, now at week 12. Down to 50.",
        flair="",
        subreddit="Ozempic",
        should_pass=False,
        description="Number 50 is below plausible weight range (80+)",
    ):
        passed += 1

    # Test 14: Number in text but not a weight
    total += 1
    if test_case(
        title="Ozempic question",
        body="I'm on dose 25 for 3 weeks now, any advice?",
        flair="",
        subreddit="Ozempic",
        should_pass=False,
        description="Has number (25) but it's a dose, not weight",
    ):
        passed += 1

    # ========================================================================
    # EDGE CASES
    # ========================================================================

    print("\n" + "=" * 80)
    print("EDGE CASES")
    print("=" * 80)

    # Test 15: Drug abbreviation
    total += 1
    if test_case(
        title="Sema progress - 3 months",
        body="220 to 200 lbs!",
        flair="",
        subreddit="sema",
        should_pass=True,
        description="Drug abbreviation (sema) recognized",
    ):
        passed += 1

    # Test 16: Multiple weight mentions
    total += 1
    if test_case(
        title="Mounjaro journey",
        body="Started at 240 pounds, now 220 pounds after 8 weeks.",
        flair="",
        subreddit="Mounjaro",
        should_pass=True,
        description="Multiple weight mentions with 'pounds'",
    ):
        passed += 1

    # Test 17: Compound semaglutide (should work - it has 'semaglutide')
    total += 1
    if test_case(
        title="Compounded semaglutide update",
        body="180 lbs down to 165 in 2 months",
        flair="",
        subreddit="compounded",
        should_pass=True,
        description="Compounded semaglutide recognized as drug",
    ):
        passed += 1

    # ========================================================================
    # FINAL RESULTS
    # ========================================================================

    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {(passed / total * 100):.1f}%")
    print("=" * 80)

    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n❌ {total - passed} TESTS FAILED")

    return passed == total


def test_individual_functions():
    """Test individual filter functions in isolation."""
    print("\n" + "=" * 80)
    print("INDIVIDUAL FUNCTION TESTS")
    print("=" * 80)

    # Test weight detection
    print("\n--- Weight Detection ---")
    assert has_weight_mention("i'm 200 lbs", "I'm 200 lbs") == True
    assert has_weight_mention("sw:220 cw:195", "SW:220 CW:195") == True
    assert has_weight_mention("lost 20 pounds", "lost 20 pounds") == True
    assert has_weight_mention("i'm 185 now", "I'm 185 now") == True  # Number in range
    assert has_weight_mention("95 kg", "95 kg") == True
    assert has_weight_mention("i'm 50 now", "I'm 50 now") == False  # Below range
    assert has_weight_mention("no weight info here", "no weight info here") == False
    print("✅ Weight detection tests passed")

    # Test duration detection
    print("\n--- Duration Detection ---")
    assert has_duration_mention("3 months on ozempic") == True
    assert has_duration_mention("week 8 update") == True
    assert has_duration_mention("started 12 weeks ago") == True
    assert has_duration_mention("i started in january") == True
    assert has_duration_mention("so far so good") == True
    assert has_duration_mention("question about dosing") == False
    print("✅ Duration detection tests passed")

    # Test drug detection
    print("\n--- Drug Detection ---")
    assert has_drug_mention("taking ozempic") == True
    assert has_drug_mention("mounjaro update") == True
    assert has_drug_mention("semaglutide journey") == True
    assert has_drug_mention("using sema") == True
    assert has_drug_mention("compounded tirzepatide") == True
    assert has_drug_mention("generic keyword like drug count") == True  # "drug" is in DRUG_KEYWORDS
    assert has_drug_mention("no glp mentioned here") == False
    print("✅ Drug detection tests passed")

    print("\n✅ ALL INDIVIDUAL FUNCTION TESTS PASSED")


if __name__ == "__main__":
    # Run individual function tests first
    test_individual_functions()

    # Then run full integration tests
    all_passed = run_tests()

    exit(0 if all_passed else 1)
