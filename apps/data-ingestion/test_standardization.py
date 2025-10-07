#!/usr/bin/env python3
"""Test drug name standardization"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from shared.drug_standardization import standardize_drug_name

# Test cases from the API
test_drugs = [
    "Wegovy", "Mounjaro", "Ozempic", "Zepbound", "Saxenda",
    "Tirzepatide", "Metformin", "GLP-1", "metformin", "semaglutide",
    "tirzepatide", "tren", "Semaglutide", "Trulicity", "inositol",
    "compounded semaglutide", "Liraglutide", "spironolactone",
    "Compounded Semaglutide", "mirtazapine", "testosterone", "TRT",
    "Galvusmet", "Dexcom", "Victoza", "liraglutide", "HRT", "Clomid",
    "Testosterone", "Rybelsus", "Amble", "Tenuiss", "Matsera",
    "Retatrutide", "Compounded GLP-1", "Compound Tirzepatide",
    "compounded tirzepatide", "Compounded Tirzepatide",
    "levothyroxine", "phentermine", "Testosterone Replacement Therapy"
]

print("Drug Name Standardization Test")
print("=" * 80)

changes = {}
for drug in test_drugs:
    standardized = standardize_drug_name(drug)
    if standardized != drug:
        if drug not in changes:
            changes[drug] = standardized
        print(f"  {drug:45} -> {standardized:30}")
    else:
        print(f"  {drug:45} (no change)")

print("\n" + "=" * 80)
print(f"Total: {len(test_drugs)} drugs tested, {len(changes)} would be changed")
print("=" * 80)

# Print grouped changes
if changes:
    print("\nGrouped by target:")
    from collections import defaultdict
    grouped = defaultdict(list)
    for old, new in changes.items():
        grouped[new].append(old)

    for target, sources in sorted(grouped.items()):
        print(f"\n{target}:")
        for source in sorted(sources):
            print(f"  - {source}")
