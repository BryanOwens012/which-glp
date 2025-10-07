"""
Prompt templates for Claude AI extraction of structured data from Reddit posts/comments.

These templates guide Claude to extract weight loss features, costs, and experiences
in a structured format while maintaining accuracy and not hallucinating data.
"""


# System prompt that defines Claude's role and extraction rules
SYSTEM_PROMPT = """You are analyzing Reddit posts and comments about GLP-1 weight loss medications (Ozempic, Wegovy, Mounjaro, Zepbound, semaglutide, tirzepatide, liraglutide, etc.).

Your task is to:
1. Write a first-person summary capturing the user's experience faithfully
2. Extract structured data about their weight loss journey

CRITICAL RULES:
- Summary MUST be in first-person perspective ("I started Ozempic...", "I lost 20 lbs...")
- Only extract data EXPLICITLY mentioned in the text
- Use null/None for missing data - NEVER guess or infer
- Indicate confidence level for numeric extractions (high/medium/low):
  - high: explicitly stated with clear numbers
  - medium: mentioned but with some ambiguity
  - low: implied or vague reference
- Preserve exact drug names as mentioned
- For weights: extract value and unit separately (lbs or kg). Weight objects should include:
  - value: numeric weight (e.g., 180.5)
  - unit: "lbs" or "kg"
  - confidence: "high", "medium", or "low"
- Extract ALL side effects mentioned, even minor ones
- Extract location only if explicitly mentioned (city, state, country)
- Be conservative: if uncertain, mark as null and lower confidence score

EXTRACTION GUIDELINES:

**Author Flair Data (HIGH PRIORITY):**
- Reddit user flairs often contain structured stats in format: "SW:220 CW:107 GW:110 - 15mg"
  - SW = Starting Weight, CW = Current Weight, GW = Goal Weight
  - May also include: age, sex, height, dose
  - Examples: "56F 5'1\" SW:186 CW:179 GW:140 Dose:7.5", "5'0 - SW:220 CW:107 GW:110 - 15mg"
- **PRIORITIZE flair data over body text when both exist** (flair is more structured/accurate)
- If flair contains weight data, use it and mark confidence as "high"
- Parse common flair patterns:
  - Age/sex: "56F", "28M", "32F"
  - Weights: "SW:220", "CW:180", "GW:150"
  - Height: "5'1\"", "5'10\""
  - Dose: "15mg", "2.5mg", "Dose:7.5"

**Summary (REQUIRED - NEVER null):**
- Rewrite the user's experience in first-person
- Capture key points: drug used, duration, weight change, cost, side effects
- Keep it concise (2-5 sentences typically)
- Be faithful to the original tone and content
- If post has minimal content, create a brief summary from available data (title + flair)
- Summary must ALWAYS be a string with at least 10 characters, NEVER null

**Beginning/End Weight:**
- CHECK AUTHOR FLAIR FIRST for SW (starting weight) and CW (current weight)
- Extract exact numbers with units
- Note if user mentions "starting at 200 lbs" vs "currently 180 lbs"
- Confidence high if from flair or explicit, medium if calculated from "lost X lbs"

**Duration:**
- Convert to weeks: "3 months" → 12 weeks, "1 year" → 52 weeks
- If ongoing, use duration mentioned so far
- Only extract if time period is clear
- Return as a simple integer (e.g., 12), NOT as an object with confidence

**Cost:**
- Extract monthly cost if mentioned
- Note currency (default USD if not specified)
- Include insurance context (e.g., "$25 copay" vs "$1200 retail")

**Drugs:**
- List ALL drug names mentioned in drugs_mentioned array
- primary_drug should be the main drug discussed
- Use standard naming:
  * Brand names: Title case (Ozempic, Wegovy, Mounjaro, Zepbound)
  * Generic drugs: lowercase (semaglutide, tirzepatide, metformin)
  * Compounded: "Compounded Semaglutide" or "Compounded Tirzepatide"
  * Expand abbreviations: TRT → testosterone

**Sentiment Scores (CRITICAL - read carefully):**
- **sentiment_pre**: Quality of life/feelings BEFORE starting the drug (0-1)
  - How did they feel about their weight/health situation before treatment?
  - Example: "I was miserable at 300 lbs, couldn't breathe" → 0.2 (very negative pre-state)
- **sentiment_post**: Quality of life/feelings AFTER/while taking the drug (0-1)
  - How do they feel NOW after treatment?
  - Example: "I lost 100 lbs and feel amazing" → 0.95 (very positive post-state)
- **drug_sentiments**: Sentiment toward EACH SPECIFIC DRUG mentioned (0-1)
  - How do they feel about the drug itself (not their life situation)?
  - 0.0-0.3: Very negative (severe side effects, didn't work, regret taking it)
  - 0.3-0.5: Somewhat negative (more downsides than upsides, considering stopping)
  - 0.5-0.7: Neutral/mixed (pros and cons balance out)
  - 0.7-0.9: Positive (working well, would recommend, manageable sides)
  - 0.9-1.0: Very positive (life-changing drug, no issues, highly recommend)
  - Example: {"Ozempic": 0.85, "Compounded Semaglutide": 0.40}
- **recommendation_score**: Likelihood they'd recommend this drug to a stranger in similar circumstances (0-1)
  - 0.0-0.3: Would not recommend, warn others against it
  - 0.3-0.5: Hesitant, mixed recommendation
  - 0.5-0.7: Cautious recommendation, "worth trying"
  - 0.7-0.9: Recommend, "worked for me"
  - 0.9-1.0: Strong recommendation, "life-changing, everyone should try"
  - Usually close to drug_sentiments but may differ (e.g., worked well but too expensive/hard to get)

**IMPORTANT:** Don't conflate pre-drug misery with drug negativity!
- "I was 400 lbs and hated life, but Ozempic saved me" → pre=0.1, post=0.9, drug=0.95, rec=0.95
- "I started at 200 lbs feeling fine, Ozempic made me sick" → pre=0.7, post=0.3, drug=0.2, rec=0.1

**Insurance:**
- has_insurance: true if they mention insurance coverage, false if paying out-of-pocket, null if not mentioned
- insurance_provider: extract if named (Aetna, Blue Cross, etc.)

**Side Effects (STRUCTURED FORMAT):**
- Extract as JSON list with name, severity, and confidence
- Format: [{"name": "nausea", "severity": "moderate", "confidence": "high"}, ...]
- **Severity levels:**
  - mild: Minor discomfort, doesn't affect daily life much
  - moderate: Noticeable impact, affects some activities
  - severe: Significantly impacts daily life, may require medical attention
- **Confidence:** high (explicit statement), medium (implied), low (vague)
- **CRITICAL:** Distinguish from comorbidities - side effects are NEW symptoms from the drug
- Examples:
  - "I had terrible nausea the first week" → [{"name": "nausea", "severity": "severe", "confidence": "high"}]
  - "slight fatigue" → [{"name": "fatigue", "severity": "mild", "confidence": "high"}]

**Comorbidities:**
- Extract pre-existing conditions mentioned (e.g., diabetes, type 2 diabetes, pcos, hypertension, high blood pressure, sleep apnea, fatty liver, hypothyroidism, metabolic syndrome)
- Use lowercase, normalize similar conditions (e.g., "high blood pressure" → "hypertension")
- **CRITICAL:** Distinguish from side effects - comorbidities existed BEFORE starting the drug
- Example: "I have diabetes and started Ozempic, got nausea" → comorbidities: ["diabetes"], side_effects: [{"name": "nausea", ...}]

**Lifestyle & Medical Journey:**
- **dosage_progression**: Track dose changes (e.g., "started 2.5mg, now 7.5mg", "titrated up to 15mg")
- **exercise_frequency**: How often they exercise (e.g., "3x/week", "daily", "none", "started walking 30min daily")
- **dietary_changes**: Diet modifications (e.g., "low carb", "calorie counting", "intermittent fasting", "eating less")
- **previous_weight_loss_attempts**: Prior methods tried (e.g., ["keto", "weight watchers", "bariatric surgery"])

**Drug Sourcing & Switching:**
- **drug_source**: "brand" (Ozempic, Wegovy, etc.), "compounded" (compounding pharmacy), or "other" (foreign-sourced, gray market)
  - Examples: "using compounded semaglutide" → "compounded", "getting it from Canada" → "other"
- **switching_drugs**: If they switched GLP-1s and why (e.g., "switched from Ozempic to Mounjaro due to side effects")

**Side Effect Details:**
- **side_effect_timing**: When they occurred (e.g., "first 2 weeks", "after dose increase", "ongoing", "months 3-6")
- **side_effect_resolution**: Degree of improvement (0-1 scale)
  - 0.0: Completely resolved, no longer an issue
  - 0.3: Significantly improved, much better
  - 0.5: Somewhat better, still noticeable
  - 0.7: Minimal improvement, still problematic
  - 1.0: No improvement or gotten worse
  - null: Not mentioned or unclear
  - Examples: "nausea went away after week 3" → 0.0, "fatigue is better but still there" → 0.5
- **food_intolerances**: Specific foods they can't tolerate (e.g., ["red meat", "greasy food", "alcohol", "sugar"])

**Weight Loss Journey Details:**
- **plateau_mentioned**: true if they mention hitting a plateau, false/null otherwise
- **rebound_weight_gain**: true if they mention regaining weight after stopping, false/null otherwise

**Health Improvements:**
- **labs_improvement**: Lab results that improved (e.g., ["a1c down to 5.2", "cholesterol improved", "blood pressure normalized"])
- **medication_reduction**: Meds they reduced/stopped (e.g., ["metformin", "blood pressure meds", "insulin"])
- **nsv_mentioned**: Non-scale victories (e.g., ["more energy", "clothes fit better", "can climb stairs", "sleep better", "joint pain gone"])

**Social & Practical Factors:**
- **support_system**: Support mentions (e.g., "family very supportive", "doing this alone", "doctor skeptical")
- **pharmacy_access_issues**: true if they mention shortage/difficulty finding medication
- **mental_health_impact**: Mental health changes (e.g., "less depressed", "anxiety increased", "mood swings")

**Demographics (CRITICAL for personalized predictions):**
- **Age:** Extract if explicitly stated ("I'm 28", "45M", "32F", "I am 35 years old")
- **Sex:** Extract if mentioned (male/female/ftm/mtf/other)
  - "male": cisgender male or not specified as trans
  - "female": cisgender female or not specified as trans
  - "ftm": female-to-male transgender
  - "mtf": male-to-female transgender
  - "other": non-binary, genderqueer, or other identities
  - Indicators: "M", "F", "male", "female", "trans man", "trans woman", "FTM", "MTF", "non-binary", pronouns
  - Use lowercase: "male", "female", "ftm", "mtf", "other"
- **State:** Extract US state if mentioned
  - Examples: "I'm in California", "TX resident", "NYC" → "New York"
  - Use full state name when possible
- **Country:** Extract country if mentioned
  - Examples: "I'm in Canada", "UK here", "from Australia"
  - Language/currency hints: "£" → "UK", "$CAD" → "Canada", "NHS" → "UK"
  - Use: "USA", "Canada", "UK", "Australia", etc.

**Confidence Score:**
- Overall confidence in extraction accuracy (0-1)
- 0.9-1.0: very explicit, clear data
- 0.7-0.9: mostly clear, minor ambiguities
- 0.5-0.7: some inference needed, partial data
- <0.5: vague, limited data

OUTPUT FORMAT:
Return valid JSON matching this schema:
{
  "summary": "I started taking Ozempic...",
  "beginning_weight": {"value": 200, "unit": "lbs", "confidence": "high"},
  "end_weight": {"value": 180, "unit": "lbs", "confidence": "high"},
  "duration_weeks": 12,
  "cost_per_month": 25.00,
  "currency": "USD",
  "drugs_mentioned": ["Ozempic"],
  "primary_drug": "Ozempic",
  "drug_sentiments": {"Ozempic": 0.85},
  "sentiment_pre": 0.3,
  "sentiment_post": 0.9,
  "recommendation_score": 0.9,
  "has_insurance": true,
  "insurance_provider": "Aetna",
  "side_effects": [
    {"name": "nausea", "severity": "moderate", "confidence": "high"},
    {"name": "fatigue", "severity": "mild", "confidence": "medium"}
  ],
  "comorbidities": ["type 2 diabetes", "hypertension"],
  "location": "New York, NY",
  "age": 28,
  "sex": "male",
  "state": "New York",
  "country": "USA",
  "dosage_progression": "started 2.5mg, now 7.5mg",
  "exercise_frequency": "3x/week",
  "dietary_changes": "low carb, calorie counting",
  "previous_weight_loss_attempts": ["keto", "weight watchers"],
  "drug_source": "brand",
  "switching_drugs": null,
  "side_effect_timing": "first 2 weeks",
  "side_effect_resolution": 0.0,
  "food_intolerances": ["greasy food"],
  "plateau_mentioned": false,
  "rebound_weight_gain": false,
  "labs_improvement": ["a1c down to 5.2"],
  "medication_reduction": ["metformin"],
  "nsv_mentioned": ["more energy", "clothes fit better"],
  "support_system": "family supportive",
  "pharmacy_access_issues": false,
  "mental_health_impact": "less depressed",
  "confidence_score": 0.85
}

CRITICAL JSON FORMATTING RULES - READ CAREFULLY BEFORE GENERATING OUTPUT:

**ARRAY FIELDS - MUST BE [] WHEN EMPTY, NEVER null:**
These fields must ALWAYS be an array, even if empty. null is INVALID and will cause validation errors.
- drugs_mentioned: [] (NOT null)
- side_effects: [] (NOT null)
- comorbidities: [] (NOT null)
- previous_weight_loss_attempts: [] (NOT null)
- food_intolerances: [] (NOT null)
- labs_improvement: [] (NOT null)
- medication_reduction: [] (NOT null)
- nsv_mentioned: [] (NOT null)

**SCALAR FIELDS - Use null when not available:**
- Use null for missing strings, numbers, booleans
- summary: NEVER null, always a string (minimum 10 chars)

**STRING FIELDS (null or string, NEVER an array):**
- dietary_changes, exercise_frequency, dosage_progression, switching_drugs
- side_effect_timing, location, support_system, mental_health_impact
- For dietary_changes: combine multiple items into single string ("low carb, calorie counting")
- For switching_drugs: describe as string ("switched from Wegovy to Zepbound") or null

**INTEGER/NUMBER FIELDS (plain number, NEVER an object):**
- duration_weeks: 12 (NOT {"value": 12, "confidence": "high"})
- cost_per_month: 150.50 (NOT {"value": 150.50})
- age: 28 (plain integer)
- All sentiment scores: 0.85 (plain float 0-1)

**BOOLEAN FIELDS (true/false/null, NEVER a string):**
- has_insurance, plateau_mentioned, rebound_weight_gain, pharmacy_access_issues

**VALIDATION CHECK - Before responding, verify:**
✓ drugs_mentioned is [] or ["Drug1", "Drug2"], NOT null
✓ side_effects is [] or [{"name": "...", "severity": "...", "confidence": "..."}], NOT null
✓ summary is a string, NOT null
✓ All list fields are arrays [], NOT null
"""


def build_post_prompt(title: str, body: str, author_flair: str = "") -> str:
    """
    Build extraction prompt for a Reddit post (no comment chain).

    Args:
        title: Post title
        body: Post body text (selftext)
        author_flair: Author flair text (may contain structured data)

    Returns:
        Formatted user prompt for Claude
    """
    flair_section = f"\nAUTHOR FLAIR: {author_flair}\n" if author_flair else ""

    return f"""Extract structured data from this Reddit post.

POST TITLE: {title}
{flair_section}
POST BODY:
{body}

Extract the data and return JSON.
"""


def build_comment_prompt(
    post_title: str,
    post_body: str,
    comment_chain: list[dict],
    target_comment_id: str,
    post_author_flair: str = ""
) -> str:
    """
    Build extraction prompt for a Reddit comment with full context chain.

    The comment chain provides context from the original post down to the target comment.
    This allows Claude to understand the full conversation context.

    Args:
        post_title: Original post title
        post_body: Original post body
        comment_chain: List of comments from top-level to target, each dict with:
                      - comment_id: str
                      - author: str
                      - body: str
                      - depth: int
                      - author_flair: str (optional)
        target_comment_id: ID of the comment we're extracting from
        post_author_flair: Author flair from original post

    Returns:
        Formatted user prompt for Claude
    """
    # Format the comment chain with indentation for readability
    chain_text = []
    for comment in comment_chain:
        indent = "  " * (comment["depth"] - 1)
        marker = "TARGET → " if comment["comment_id"] == target_comment_id else ""
        flair = f" [Flair: {comment.get('author_flair', '')}]" if comment.get("author_flair") else ""
        chain_text.append(
            f"{indent}[Depth {comment['depth']} - u/{comment['author']}]{flair} {marker}\n{indent}{comment['body']}"
        )

    chain_str = "\n\n".join(chain_text)
    post_flair_section = f"\nORIGINAL POST AUTHOR FLAIR: {post_author_flair}\n" if post_author_flair else ""

    return f"""Extract structured data from the TARGET comment in this Reddit conversation.

ORIGINAL POST TITLE: {post_title}
{post_flair_section}
ORIGINAL POST BODY:
{post_body}

COMMENT CHAIN (from top-level to target):
{chain_str}

Extract data from the TARGET comment only, but use the full context to understand references.
For example, if the target comment says "I'm on week 8 now" and an earlier comment mentions "I started Ozempic", include "Ozempic" in drugs_mentioned.
Check the TARGET comment's author flair for structured data (SW, CW, age, sex, etc.).

Return JSON.
"""


def build_context_summary(
    post_title: str,
    num_comments: int,
    subreddit: str
) -> str:
    """
    Build a brief context summary for logging/debugging.

    Args:
        post_title: Post title
        num_comments: Number of comments in chain
        subreddit: Subreddit name

    Returns:
        Human-readable context summary
    """
    return f"r/{subreddit} - '{post_title[:50]}...' ({num_comments} comments in chain)"


# Drug name mappings for normalization
KNOWN_DRUGS = {
    "ozempic": "Ozempic",
    "wegovy": "Wegovy",
    "mounjaro": "Mounjaro",
    "zepbound": "Zepbound",
    "semaglutide": "Semaglutide",
    "tirzepatide": "Tirzepatide",
    "liraglutide": "Liraglutide",
    "saxenda": "Saxenda",
    "victoza": "Victoza",
    "trulicity": "Trulicity",
    "rybelsus": "Rybelsus",
    "byetta": "Byetta",
    "bydureon": "Bydureon",
    "adlyxin": "Adlyxin",
    "compound": "Compounded Semaglutide",
    "compounded": "Compounded Semaglutide",
}


def normalize_drug_name(drug: str) -> str:
    """
    Normalize drug name to standard capitalization.

    Args:
        drug: Drug name (any case)

    Returns:
        Normalized drug name
    """
    drug_lower = drug.lower().strip()
    return KNOWN_DRUGS.get(drug_lower, drug.strip().title())
