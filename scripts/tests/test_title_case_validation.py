#!/usr/bin/env python3
"""
Test script to verify that primary_drug and drugs_mentioned are converted to Title Case
by the schema validators.

This tests the Pydantic validation without making any API calls.
"""

import sys
from pathlib import Path

# Add apps/post-extraction to path
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root / "apps" / "post-extraction"))

from schema import ExtractedFeatures

def test_title_case_validation():
    """Test that lowercase drug names are converted to Title Case"""

    print("=" * 80)
    print("TESTING TITLE CASE VALIDATION")
    print("=" * 80)

    # Test 1: Primary drug with lowercase
    print("\n📋 Test 1: primary_drug conversion")
    print("   Input: 'compounded tirzepatide'")

    features = ExtractedFeatures(
        summary="Test summary with minimum length",
        primary_drug="compounded tirzepatide"
    )

    print(f"   Output: '{features.primary_drug}'")
    assert features.primary_drug == "Compounded Tirzepatide", f"Expected 'Compounded Tirzepatide', got '{features.primary_drug}'"
    print("   ✅ PASS")

    # Test 2: drugs_mentioned with mixed case
    print("\n📋 Test 2: drugs_mentioned conversion")
    print("   Input: ['ozempic', 'MOUNJARO', 'compounded semaglutide']")

    features = ExtractedFeatures(
        summary="Test summary with minimum length",
        drugs_mentioned=["ozempic", "MOUNJARO", "compounded semaglutide"],
        primary_drug="ozempic"
    )

    print(f"   Output: {features.drugs_mentioned}")
    expected = ["Ozempic", "Mounjaro", "Compounded Semaglutide"]
    assert features.drugs_mentioned == expected, f"Expected {expected}, got {features.drugs_mentioned}"
    print("   ✅ PASS")

    # Test 3: drug_sentiments keys
    print("\n📋 Test 3: drug_sentiments key conversion")
    print("   Input: {'ozempic': 0.85, 'compounded tirzepatide': 0.6}")

    features = ExtractedFeatures(
        summary="Test summary with minimum length",
        drug_sentiments={"ozempic": 0.85, "compounded tirzepatide": 0.6}
    )

    print(f"   Output: {features.drug_sentiments}")
    assert "Ozempic" in features.drug_sentiments, "Expected 'Ozempic' key"
    assert "Compounded Tirzepatide" in features.drug_sentiments, "Expected 'Compounded Tirzepatide' key"
    assert features.drug_sentiments["Ozempic"] == 0.85
    assert features.drug_sentiments["Compounded Tirzepatide"] == 0.6
    print("   ✅ PASS")

    # Test 4: All three fields together
    print("\n📋 Test 4: Complete validation")
    print("   Input:")
    print("     primary_drug: 'metformin'")
    print("     drugs_mentioned: ['metformin', 'insulin']")
    print("     drug_sentiments: {'metformin': 0.7, 'insulin': 0.5}")

    features = ExtractedFeatures(
        summary="Test summary with minimum length",
        primary_drug="metformin",
        drugs_mentioned=["metformin", "insulin"],
        drug_sentiments={"metformin": 0.7, "insulin": 0.5}
    )

    print(f"   Output:")
    print(f"     primary_drug: '{features.primary_drug}'")
    print(f"     drugs_mentioned: {features.drugs_mentioned}")
    print(f"     drug_sentiments: {features.drug_sentiments}")

    assert features.primary_drug == "Metformin"
    assert features.drugs_mentioned == ["Metformin", "Insulin"]
    assert features.drug_sentiments == {"Metformin": 0.7, "Insulin": 0.5}
    print("   ✅ PASS")

    # Test 5: None values
    print("\n📋 Test 5: None handling")
    print("   Input: primary_drug=None, drugs_mentioned=None")

    features = ExtractedFeatures(
        summary="Test summary with minimum length",
        primary_drug=None,
        drugs_mentioned=None
    )

    print(f"   Output: primary_drug={features.primary_drug}, drugs_mentioned={features.drugs_mentioned}")
    assert features.primary_drug is None
    assert features.drugs_mentioned == []  # Should convert None to empty list
    print("   ✅ PASS")

    # Test 6: Edge cases with special characters
    print("\n📋 Test 6: Special characters and abbreviations")
    print("   Input: 'GLP-1', 'TRT', 'BPC 157'")

    features = ExtractedFeatures(
        summary="Test summary with minimum length",
        primary_drug="GLP-1",
        drugs_mentioned=["GLP-1", "TRT", "BPC 157"]
    )

    print(f"   Output:")
    print(f"     primary_drug: '{features.primary_drug}'")
    print(f"     drugs_mentioned: {features.drugs_mentioned}")

    # Note: .title() converts "GLP-1" to "Glp-1", which is what we want based on the prompt
    assert features.primary_drug == "Glp-1"
    assert features.drugs_mentioned == ["Glp-1", "Trt", "Bpc 157"]
    print("   ✅ PASS")

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED ✅")
    print("=" * 80)
    print("\nTitle case validation is working correctly!")
    print("- primary_drug is converted to Title Case")
    print("- drugs_mentioned items are converted to Title Case")
    print("- drug_sentiments keys are converted to Title Case")


if __name__ == "__main__":
    try:
        test_title_case_validation()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
