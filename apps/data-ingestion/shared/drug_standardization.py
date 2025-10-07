"""
Drug name standardization utilities.

This module provides consistent drug naming across:
- AI extraction pipeline
- Database storage
- Analytics and reporting
- Frontend display

Standardization rules:
1. ALL drug names: Title Case (e.g., "Ozempic", "Wegovy", "Metformin", "Testosterone")
2. Abbreviations: Expand to full names (e.g., "TRT" -> "Testosterone")
3. Compounded variants: Standardize format (e.g., "Compounded Semaglutide")
4. Non-GLP-1 drugs: Keep but standardize to Title Case (e.g., "Metformin", "Spironolactone")
"""

# Mapping of variant names to standardized names
DRUG_NAME_MAPPING = {
    # GLP-1 Brand Names (Title Case)
    "ozempic": "Ozempic",
    "Ozempic": "Ozempic",
    "wegovy": "Wegovy",
    "Wegovy": "Wegovy",
    "mounjaro": "Mounjaro",
    "Mounjaro": "Mounjaro",
    "zepbound": "Zepbound",
    "Zepbound": "Zepbound",
    "saxenda": "Saxenda",
    "Saxenda": "Saxenda",
    "victoza": "Victoza",
    "Victoza": "Victoza",
    "trulicity": "Trulicity",
    "Trulicity": "Trulicity",
    "rybelsus": "Rybelsus",
    "Rybelsus": "Rybelsus",

    # GLP-1 Generic Names (Title Case)
    "semaglutide": "Semaglutide",
    "Semaglutide": "Semaglutide",
    "SEMAGLUTIDE": "Semaglutide",
    "tirzepatide": "Tirzepatide",
    "Tirzepatide": "Tirzepatide",
    "TIRZEPATIDE": "Tirzepatide",
    "liraglutide": "Liraglutide",
    "Liraglutide": "Liraglutide",
    "LIRAGLUTIDE": "Liraglutide",
    "dulaglutide": "Dulaglutide",
    "Dulaglutide": "Dulaglutide",
    "retatrutide": "Retatrutide",
    "Retatrutide": "Retatrutide",

    # Compounded variants (standardized format)
    "compounded semaglutide": "Compounded Semaglutide",
    "Compounded Semaglutide": "Compounded Semaglutide",
    "Compounded semaglutide": "Compounded Semaglutide",
    "compounded Semaglutide": "Compounded Semaglutide",
    "compounded tirzepatide": "Compounded Tirzepatide",
    "Compounded Tirzepatide": "Compounded Tirzepatide",
    "Compounded tirzepatide": "Compounded Tirzepatide",
    "Compound Tirzepatide": "Compounded Tirzepatide",
    "compounded GLP-1": "Compounded GLP-1",
    "Compounded GLP-1": "Compounded GLP-1",

    # Generic GLP-1 references
    "GLP-1": "GLP-1",
    "glp-1": "GLP-1",
    "GLP1": "GLP-1",
    "glp1": "GLP-1",

    # Metformin variants (Title Case)
    "metformin": "Metformin",
    "Metformin": "Metformin",
    "METFORMIN": "Metformin",

    # Testosterone variants (Title Case, expand abbreviations)
    "testosterone": "Testosterone",
    "Testosterone": "Testosterone",
    "TESTOSTERONE": "Testosterone",
    "trt": "Testosterone",
    "TRT": "Testosterone",
    "Testosterone Replacement Therapy": "Testosterone",
    "testosterone replacement therapy": "Testosterone",

    # Trenbolone (Title Case)
    "tren": "Trenbolone",
    "Tren": "Trenbolone",
    "trenbolone": "Trenbolone",
    "Trenbolone": "Trenbolone",

    # Other medications (Title Case)
    "inositol": "Inositol",
    "Inositol": "Inositol",
    "spironolactone": "Spironolactone",
    "Spironolactone": "Spironolactone",
    "mirtazapine": "Mirtazapine",
    "Mirtazapine": "Mirtazapine",
    "levothyroxine": "Levothyroxine",
    "Levothyroxine": "Levothyroxine",
    "phentermine": "Phentermine",
    "Phentermine": "Phentermine",

    # Brand name medications (Title Case)
    "Galvusmet": "Galvusmet",
    "galvusmet": "Galvusmet",
    "Clomid": "Clomid",
    "clomid": "Clomid",

    # HRT
    "hrt": "HRT",
    "HRT": "HRT",
    "Hrt": "HRT",

    # Devices (not drugs, but appear in data)
    "Dexcom": "Dexcom",
    "dexcom": "Dexcom",

    # Brand name compounded medications (keep as-is)
    "Amble": "Amble",
    "Tenuiss": "Tenuiss",
    "Matsera": "Matsera",
}

# GLP-1 specific drugs for filtering
GLP1_DRUGS = {
    "Ozempic",
    "Wegovy",
    "Mounjaro",
    "Zepbound",
    "Saxenda",
    "Victoza",
    "Trulicity",
    "Rybelsus",
    "Semaglutide",
    "Tirzepatide",
    "Liraglutide",
    "Dulaglutide",
    "Retatrutide",
    "Compounded Semaglutide",
    "Compounded Tirzepatide",
    "Compounded GLP-1",
    "GLP-1",
}


def standardize_drug_name(drug_name: str | None) -> str | None:
    """
    Standardize a drug name using the mapping.

    Args:
        drug_name: Raw drug name from extraction or user input

    Returns:
        Standardized drug name, or None if input is None

    Examples:
        >>> standardize_drug_name("ozempic")
        'Ozempic'
        >>> standardize_drug_name("TRT")
        'Testosterone'
        >>> standardize_drug_name("compounded semaglutide")
        'Compounded Semaglutide'
    """
    if drug_name is None:
        return None

    # Check for exact match first
    if drug_name in DRUG_NAME_MAPPING:
        return DRUG_NAME_MAPPING[drug_name]

    # Try case-insensitive match
    drug_lower = drug_name.lower()
    for variant, standard in DRUG_NAME_MAPPING.items():
        if variant.lower() == drug_lower:
            return standard

    # If no match found, return original (preserves unknown drugs)
    return drug_name


def is_glp1_drug(drug_name: str | None) -> bool:
    """
    Check if a drug is a GLP-1 medication.

    Args:
        drug_name: Standardized or raw drug name

    Returns:
        True if drug is GLP-1, False otherwise

    Examples:
        >>> is_glp1_drug("Ozempic")
        True
        >>> is_glp1_drug("Metformin")
        False
        >>> is_glp1_drug("Testosterone")
        False
    """
    if drug_name is None:
        return False

    # Standardize first to ensure consistent checking
    standardized = standardize_drug_name(drug_name)
    return standardized in GLP1_DRUGS


def get_all_glp1_drugs() -> set[str]:
    """
    Get set of all standardized GLP-1 drug names.

    Returns:
        Set of GLP-1 drug names (standardized format)
    """
    return GLP1_DRUGS.copy()


def get_drug_display_name(drug_name: str | None) -> str:
    """
    Get display-friendly drug name for frontend.

    Args:
        drug_name: Raw or standardized drug name

    Returns:
        Display-friendly name
    """
    if drug_name is None:
        return "Unknown"

    standardized = standardize_drug_name(drug_name)
    if standardized is None:
        return drug_name

    return standardized
