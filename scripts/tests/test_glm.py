#!/usr/bin/env python3
"""Quick test of GLM client to verify API key works."""

import sys
from pathlib import Path

# Add apps to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "user-ingestion"))
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "shared"))

from glm_client import get_client
from prompts import build_user_prompt

# Test data
test_posts = [
    {"title": "Started Ozempic 3 months ago", "body": "I'm a 45 year old female, started at 220 lbs, now down to 195 lbs on 1mg weekly. Some nausea but manageable."}
]

test_comments = [
    {"body": "I live in California and pay $25/month with insurance through Blue Cross."}
]

print("Testing GLM client...")
print("=" * 60)

# Build prompt
prompt = build_user_prompt("test_user", test_posts, test_comments)

print(f"\nPrompt length: {len(prompt)} chars")
print("\nCalling GLM API...")

# Get client and extract
client = get_client()
demographics, metadata = client.extract_demographics(prompt)

print("\n" + "=" * 60)
print("EXTRACTION SUCCESSFUL!")
print("=" * 60)
print(f"\nDemographics:")
print(f"  Age: {demographics.age}")
print(f"  Sex: {demographics.sex}")
print(f"  State: {demographics.state}")
print(f"  Starting weight: {demographics.starting_weight_lbs} lbs")
print(f"  Current weight: {demographics.current_weight_lbs} lbs")
print(f"  Has insurance: {demographics.has_insurance}")
print(f"  Insurance provider: {demographics.insurance_provider}")

print(f"\nMetadata:")
print(f"  Model: {metadata['model']}")
print(f"  Cost: ${metadata['cost_usd']:.6f}")
print(f"  Input tokens: {metadata['tokens_input']}")
print(f"  Output tokens: {metadata['tokens_output']}")
print(f"  Processing time: {metadata['processing_time_ms']}ms")

print("\n✓ GLM API key is working!")
