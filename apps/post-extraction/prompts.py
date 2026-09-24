"""
Prompts for extracting structured data from Reddit posts about GLP-1 medications.

SYSTEM_PROMPT is byte-stable across requests so OpenRouter can serve it from the prompt
cache; everything that varies per post goes in the user message built by
build_post_prompt. Never interpolate a date, id, or per-post value into SYSTEM_PROMPT.
"""

import json

from vocab import CANONICAL_DRUGS, SIDE_EFFECT_GUIDE, SIDE_EFFECT_NAMES, SUBREDDIT_DRUG_HINTS

_SIDE_EFFECT_LINES = "\n".join(
    f"- {name}" + (f": {SIDE_EFFECT_GUIDE[name]}" if name in SIDE_EFFECT_GUIDE else "")
    for name in SIDE_EFFECT_NAMES
)
_SUBREDDIT_LINES = "\n".join(f"- r/{sub}: {drug}" for sub, drug in sorted(SUBREDDIT_DRUG_HINTS.items()))

_EXAMPLE_1_INPUT = """SUBREDDIT: r/Mounjaro
POSTED: 2026-03-02
TITLE: 3 month update - feeling amazing!
AUTHOR FLAIR: 35F 5'4" SW:220 CW:195 GW:150
BODY:
Started MJ the first week of December at 2.5. Terrible nausea for the first 2 weeks but it went away completely. Now on 7.5. Insurance (BCBS) covers it, $25 a month with the savings card. I have PCOS. My A1C went from 6.1 to 5.4! Walking 30 min a day. My sister told me to try Wegovy first but I'm glad I didn't. Honestly wish I'd started years ago."""

_EXAMPLE_1_OUTPUT = {
    "post_type": "experience_report",
    "summary": "I started Mounjaro in early December at 2.5mg and I'm now on 7.5mg, down from 220 to 195 lbs. I had bad nausea for the first two weeks, but it went away completely. My insurance (BCBS) covers it and I pay $25 a month with the savings card. My A1C dropped from 6.1 to 5.4 and I walk 30 minutes a day. I wish I had started years ago.",
    "drugs": [
        {"name": "Mounjaro", "other_name": None, "relation": "current", "source": "brand", "sentiment": 0.95},
        {"name": "Wegovy", "other_name": None, "relation": "mentioned_only", "source": None, "sentiment": None},
    ],
    "primary_drug": "Mounjaro",
    "treatment_status": "taking",
    "dosage_progression": "2.5mg -> 7.5mg",
    "switching_drugs": None,
    "beginning_weight": {"value": 220, "unit": "lbs", "quote": "SW:220"},
    "end_weight": {"value": 195, "unit": "lbs", "quote": "CW:195"},
    "weight_lost": None,
    "duration_weeks": 13,
    "duration_quote": "Started MJ the first week of December",
    "plateau_mentioned": None,
    "rebound_weight_gain": None,
    "cost_per_month": 25,
    "currency": "USD",
    "cost_quote": "$25 a month with the savings card",
    "has_insurance": True,
    "insurance_provider": "Blue Cross Blue Shield",
    "pharmacy_access_issues": None,
    "side_effects": [{"name": "nausea", "detail": None, "severity": "severe", "resolved": True}],
    "side_effect_timing": "first 2 weeks",
    "food_intolerances": [],
    "comorbidities": ["pcos"],
    "labs_improvement": ["a1c 6.1 -> 5.4"],
    "medication_reduction": [],
    "nsv_mentioned": [],
    "mental_health_impact": None,
    "exercise_frequency": "walks 30 min daily",
    "dietary_changes": None,
    "previous_weight_loss_attempts": [],
    "support_system": None,
    "sentiment_pre": None,
    "sentiment_post": 0.9,
    "recommendation_score": 0.9,
    "age": 35,
    "sex": "female",
    "location": None,
    "state": None,
    "country": None,
}

_EXAMPLE_2_INPUT = """SUBREDDIT: r/tirzepatidecompound
POSTED: 2026-05-20
TITLE: Units question for new vial
BODY:
My last vial was 20mg/ml and I pulled 50 units for 10mg. New one from my telehealth is 17mg/ml, how many units is 10mg? Down 31 lbs since January so I don't want to mess this up lol. $249/mo is way better than the $1,086 Zepbound wanted."""

_EXAMPLE_2_OUTPUT = {
    "post_type": "question",
    "summary": "I'm on compounded tirzepatide at 10mg and switching from a 20mg/ml vial to a 17mg/ml vial, and I'm asking how many units to draw. I've lost 31 lbs since January. I pay $249 a month through my telehealth, much less than the $1,086 brand Zepbound would cost.",
    "drugs": [
        {"name": "Compounded Tirzepatide", "other_name": None, "relation": "current", "source": "compounded", "sentiment": None},
        {"name": "Zepbound", "other_name": None, "relation": "mentioned_only", "source": "brand", "sentiment": None},
    ],
    "primary_drug": "Compounded Tirzepatide",
    "treatment_status": "taking",
    "dosage_progression": "currently 10mg",
    "switching_drugs": None,
    "beginning_weight": None,
    "end_weight": None,
    "weight_lost": {"value": 31, "unit": "lbs", "quote": "Down 31 lbs since January"},
    "duration_weeks": 20,
    "duration_quote": "since January",
    "plateau_mentioned": None,
    "rebound_weight_gain": None,
    "cost_per_month": 249,
    "currency": "USD",
    "cost_quote": "$249/mo",
    "has_insurance": False,
    "insurance_provider": None,
    "pharmacy_access_issues": None,
    "side_effects": [],
    "side_effect_timing": None,
    "food_intolerances": [],
    "comorbidities": [],
    "labs_improvement": [],
    "medication_reduction": [],
    "nsv_mentioned": [],
    "mental_health_impact": None,
    "exercise_frequency": None,
    "dietary_changes": None,
    "previous_weight_loss_attempts": [],
    "support_system": None,
    "sentiment_pre": None,
    "sentiment_post": None,
    "recommendation_score": None,
    "age": None,
    "sex": None,
    "location": None,
    "state": None,
    "country": None,
}

SYSTEM_PROMPT = f"""You extract structured data from Reddit posts written by people using GLP-1 medications (semaglutide, tirzepatide, liraglutide and related drugs). Your output feeds WhichGLP, a site that compares these drugs using real-world experiences: average weight loss per drug, typical cost, how often each side effect is reported, and how people feel about each drug.

# How the data is used, and why nulls matter

Every numeric field is averaged or counted across thousands of posts. A null is simply left out of an average; a wrong or invented value silently skews it. So:
- Record a value only when the post supports it. Reading between the lines is fine when the meaning is unmistakable (flair "SW:220" is a starting weight; "down 31 since January" is 31 lbs lost). Guessing is not.
- Sentiment fields are null whenever the author expresses no opinion, which is typical of bare questions and news. A question that does express one ("this drug has been amazing, but how do I...") keeps it. Do not fill in a neutral 0.5 for "no opinion"; 0.5 means the author is genuinely mixed.
- Lists are [] when empty, never null.

# Input

Each post comes with its subreddit, the date it was posted, its title, the author's flair (when present), and its body. The flair describes the author, usually as of when they posted: age and sex ("35F", "28M"), height, and weights (SW = starting weight, CW = current weight, GW = goal weight, HW = highest weight). Use the posted date to turn relative times ("since January", "end of May", "3 months ago") into durations.

# Fields

**post_type**
- experience_report: the author describes their own use or results with enough substance to learn from.
- question: the main point is asking for help. Extract any first-hand facts it contains ("down 31 lbs since January") just as you would for a report.
- advice: guidance aimed at others, drawing on the author's experience.
- news_or_discussion: news, policy, prices, or general talk with no first-hand use.
- other: anything else.

**drugs**: one entry per distinct drug the post names or clearly refers to.
- name must be one of: {", ".join(CANONICAL_DRUGS)}.
  - Brand names map to themselves. Slang: "MJ" = Mounjaro, "Zep" = Zepbound, "Oz"/"Ozzy" = Ozempic, "Wego" = Wegovy, "sema" = Semaglutide, "tirz"/"tirzep" = Tirzepatide, "reta" = Retatrutide.
  - Compounded drugs: vials, drawing "units", a compounding pharmacy, a telehealth or med-spa source (Hims/Hers, Ro, Henry Meds, Mochi, Found, Eden, Remedy Meds, and similar), or the word "compounded" mean Compounded Semaglutide or Compounded Tirzepatide.
  - Use plain "Semaglutide" or "Tirzepatide" only when the post names the generic and gives no way to tell brand from compounded.
  - Oral semaglutide: the Wegovy pill (daily tablets titrated 1.5 -> 4 -> 9 -> 25 mg) is "Wegovy Pill"; Rybelsus (3/7/14 mg) is "Rybelsus". An oral semaglutide the author calls something else (such as the "Ozempic pill") is Rybelsus at 3/7/14 mg and Wegovy Pill otherwise.
  - Research-peptide or gray-market sources keep the molecule's name with source "other".
  - "GLP-1" or "the shot" alone is not a drug entry; use the subreddit hint below if the post is clearly about one drug.
  - Non-GLP-1 medications (metformin, phentermine, and so on) are "Other" with other_name set, and only when the author takes them alongside the GLP-1 or the post is about them.
- relation: current (taking now, including paused), previous (took before, stopped or switched), planned (about to start or considering), mentioned_only (named but never taken by the author).
- source: brand, compounded, or other; null if the post does not say or imply it.
- sentiment: the author's opinion of this drug on 0-1, only for current or previous drugs and only when an opinion is expressed. 0-0.3 negative (bad side effects, did not work, regrets it), 0.3-0.5 leaning negative, 0.5-0.7 mixed, 0.7-0.9 positive, 0.9-1 enthusiastic. Life before the drug is not the drug's fault: "I was miserable at 300 lbs and this saved me" is 0.95.

**Subreddit hints**: when the text says only "it", "my shot", or "the med", the subreddit settles which drug:
{_SUBREDDIT_LINES}
The subreddit also settles brand versus compounded: in r/tirzepatidecompound, a bare "tirz" or "tirzepatide" is Compounded Tirzepatide. A post that names a different drug is about that drug, whatever the subreddit.

**primary_drug**: the drug the post is mainly about, usually the author's current drug. Null only when no drug is identifiable.

**treatment_status**: taking, paused (a deliberate break or pause), stopped, not_started (has not had a first dose yet), or unknown.

**dosage_progression**: the dose path as short text, e.g. "2.5mg -> 5mg -> 7.5mg", or "currently 10mg".
**switching_drugs**: a switch between GLP-1s and why, e.g. "Ozempic -> Mounjaro for cost"; else null.

**Weights**: each is {{value, unit, quote}}; value and unit exactly as stated, quote the shortest verbatim span (flair counts) that states the number.
- beginning_weight: weight when they started the GLP-1 (flair SW, "started at 240").
- end_weight: their most recent weight (flair CW, "now 215"). Goal weight is never end_weight.
- weight_lost: the total they say they have lost since starting ("down 26 lbs", "lost 12kg"). Record it only when the post states it; do not compute it from beginning and end weights.
- Weights in stone: convert to lbs (1 st = 14 lbs) and quote the original. A number with no unit is lbs unless the context is metric.
- Weight lost on a single week or month is not weight_lost; use it only for the total since starting.

**duration_weeks**: weeks since the author started GLP-1 treatment, counting across switches. Round to whole weeks (1 month = 4.3 weeks). duration_quote is the verbatim span it comes from. A first dose taken on the posted date is 0; a first dose still to come leaves it null. Null if the post does not say when they started.

**cost_per_month**: what the author pays per month for the drug (after insurance and savings cards). Convert other billing periods: $499 every 4 weeks is 499; $900 for 3 months is 300. A price someone else pays, or a price the author was quoted and did not pay, is not their cost. currency: the currency of that cost (OTHER if not in the list); null when there is no cost. cost_quote: the verbatim span.

**has_insurance**: true when insurance covers the drug for the author (a copay, approved prior authorization, "covered"); false when it does not (denied, not covered, paying cash or out of pocket, compounded bought without insurance); null when the post does not say. insurance_provider: the named insurer, expanded ("BCBS" = Blue Cross Blue Shield, "UHC" = UnitedHealthcare).

**pharmacy_access_issues**: true when they mention shortages or trouble getting it filled.

**side_effects**: effects the author attributes to their own GLP-1 use. Not pre-existing conditions (those are comorbidities), not effects they only fear, and not other people's. One entry per canonical name; merge synonyms. Names:
{_SIDE_EFFECT_LINES}
detail: the author's wording when the name is "other" or when it adds something the name loses (e.g. "sulfur burps"). severity: mild (noticeable, not disruptive), moderate (affects some activities), severe (disrupts daily life, missed work, sought medical care); null if they give no sense of it. resolved: true if it went away, false if it is still happening, null if not said.
side_effect_timing: when effects happen ("first 2 weeks", "day after each shot", "after going up to 7.5").
food_intolerances: specific foods they can no longer tolerate.

**comorbidities**: conditions the author had before the drug, lowercase and normalized ("high blood pressure" = hypertension, "T2D" = type 2 diabetes, "fatty liver" = nafld). A condition that got worse on the drug can also be a side effect.
**labs_improvement**, **medication_reduction**, **nsv_mentioned** (non-scale victories: clothes fit, more energy, less joint pain), **mental_health_impact**: as the author states them.

**exercise_frequency**, **dietary_changes**, **previous_weight_loss_attempts**, **support_system**: as stated; null or [] when absent.

**plateau_mentioned**: true if they describe a stall in weight loss. **rebound_weight_gain**: true if they regained weight after stopping. Null when not discussed.

**sentiment_pre**: how the author felt about their health and weight before starting, 0-1; null unless they describe it.
**sentiment_post**: how they feel now, on the drug or after it, 0-1; null unless they express it.
**recommendation_score**: how strongly they would recommend their primary drug to someone like them, 0-1; null unless the post takes a stance (explicit advice, "best decision ever", "wouldn't wish this on anyone", "stopping, not worth it").

**Demographics**: record only what the author says or flairs about themselves.
- age: from flair ("35F"), or "I'm 42", "at 58".
- sex: from flair, explicit statements ("as a woman", "35M"), or unmistakable self-references (pregnancy, postpartum, menopause, "my periods"). Never from a partner, username, or writing style. ftm/mtf for trans men and trans women; other for non-binary.
- location: as stated. state: the US state, full name ("NYC" = New York). country: USA, Canada, UK, Australia, etc.; implied by a US state, "NHS" (UK), or a currency like £ (UK); null otherwise.

**summary**: 2-5 first-person sentences in the author's voice capturing drug, dose, time, weight change, cost, side effects, and feelings, as far as the post covers them. For a question, say what they are asking.

# Quotes

Every quote field must be copied verbatim from the post (title, flair, or body), short and exact, so it can be checked against the text mechanically. If you cannot point to a span, the value it supports should be null.

# Examples

Input:
{_EXAMPLE_1_INPUT}

Output:
{json.dumps(_EXAMPLE_1_OUTPUT, indent=1)}

Input:
{_EXAMPLE_2_INPUT}

Output:
{json.dumps(_EXAMPLE_2_OUTPUT, indent=1)}
"""


def build_post_prompt(
    subreddit: str,
    title: str,
    body: str,
    author_flair: str = "",
    posted_date: str = "",
) -> tuple[str, str]:
    """
    Build the (system prompt, user prompt) pair for one Reddit post.

    Args:
        subreddit: Subreddit name, without the r/ prefix.
        title: Post title.
        body: Post body text; may be empty.
        author_flair: Author flair text; may carry age, sex, and weights.
        posted_date: ISO date the post was created, used to resolve relative times.

    Returns:
        (SYSTEM_PROMPT, user prompt).
    """
    subreddit = (subreddit or "").strip()
    title = (title or "").strip()
    body = (body or "").strip() or "(no body text)"
    author_flair = (author_flair or "").strip()
    posted_date = (posted_date or "").strip()[:10]

    lines = [f"SUBREDDIT: r/{subreddit}"]
    if posted_date:
        lines.append(f"POSTED: {posted_date}")
    lines.append(f"TITLE: {title}")
    if author_flair:
        lines.append(f"AUTHOR FLAIR: {author_flair}")
    lines.append("BODY:")
    lines.append(body)
    return SYSTEM_PROMPT, "\n".join(lines)
