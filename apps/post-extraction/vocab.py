"""
Controlled vocabularies for post extraction.

The extraction schema constrains drug names, side effects, post types, and treatment
status to these values, so the model's output is enforced during decoding (strict JSON
schema) instead of being normalized after the fact. Add a value here rather than
teaching a downstream consumer a new spelling.
"""

from typing import Dict, Literal, get_args

# GLP-1 drugs (and close relatives) as they are stored. "Semaglutide"/"Tirzepatide"
# mean the generic was named without saying brand or compounded; "Other" carries the
# free-text name in DrugUse.other_name.
CanonicalDrug = Literal[
    "Ozempic",
    "Wegovy",
    "Wegovy Pill",
    "Rybelsus",
    "Semaglutide",
    "Compounded Semaglutide",
    "Mounjaro",
    "Zepbound",
    "Tirzepatide",
    "Compounded Tirzepatide",
    "Saxenda",
    "Victoza",
    "Liraglutide",
    "Trulicity",
    "Retatrutide",
    "Orforglipron",
    "Other",
]
CANONICAL_DRUGS = get_args(CanonicalDrug)

# Canonical names that settle the source on their own. Generic names ("Semaglutide",
# "Tirzepatide", "Liraglutide") and "Other" leave it to the post.
BRAND_DRUGS = frozenset({
    "Ozempic", "Wegovy", "Wegovy Pill", "Rybelsus", "Mounjaro", "Zepbound", "Saxenda", "Victoza", "Trulicity",
})
COMPOUNDED_DRUGS = frozenset({"Compounded Semaglutide", "Compounded Tirzepatide"})

# How the author relates to a drug. Only "current" and "previous" are drugs the author
# has actually taken; sentiment is recorded only for those.
DrugRelation = Literal["current", "previous", "planned", "mentioned_only"]
TAKEN_RELATIONS = ("current", "previous")

PostType = Literal[
    "experience_report",  # the author describes their own use or results
    "question",  # asks for help; may still contain first-hand facts
    "advice",  # answers or guidance aimed at others
    "news_or_discussion",  # news, policy, pricing, general talk with no first-hand use
    "other",
]

TreatmentStatus = Literal["taking", "paused", "stopped", "not_started", "unknown"]

# Canonical side-effect names. Synonyms map onto one name (see SIDE_EFFECT_GUIDE), so
# "fatigue", "exhaustion", and "low energy" are counted once, as "fatigue".
SideEffectName = Literal[
    "nausea",
    "vomiting",
    "diarrhea",
    "constipation",
    "acid reflux",
    "burping",
    "bloating",
    "gas",
    "abdominal pain",
    "fatigue",
    "headache",
    "dizziness",
    "dehydration",
    "hair loss",
    "injection site reaction",
    "reduced appetite",
    "food aversion",
    "increased hunger",
    "muscle loss",
    "low blood sugar",
    "gallbladder problem",
    "pancreas problem",
    "allergic reaction",
    "skin sensitivity",
    "feeling cold",
    "fast heart rate",
    "insomnia",
    "anxiety",
    "depression",
    "other",
]
SIDE_EFFECT_NAMES = get_args(SideEffectName)

# What each canonical side effect absorbs. Rendered into the system prompt.
SIDE_EFFECT_GUIDE: Dict[str, str] = {
    "acid reflux": "heartburn, GERD, reflux",
    "burping": "burps, belching, sulfur burps",
    "abdominal pain": "stomach pain, cramps, upset stomach, gastroparesis-type pain",
    "fatigue": "tiredness, exhaustion, low energy, lethargy",
    "headache": "headache, migraine",
    "dizziness": "lightheadedness, vertigo, feeling faint",
    "hair loss": "shedding, thinning hair",
    "injection site reaction": "redness, itching, swelling, rash, or bruising at the injection site",
    "reduced appetite": "loss of appetite, can't eat enough, forgetting to eat",
    "food aversion": "specific foods now repulsive or not tolerated",
    "increased hunger": "hunger or food noise returning or worsening",
    "low blood sugar": "hypoglycemia, shaky from low sugar",
    "gallbladder problem": "gallstones, gallbladder attack or removal",
    "pancreas problem": "pancreatitis, elevated lipase or amylase",
    "allergic reaction": "hives, body rash, swelling not at the injection site",
    "skin sensitivity": "skin hurts to touch, allodynia, burning skin",
    "insomnia": "trouble sleeping, sleep disruption",
    "anxiety": "anxiety, panic attacks",
    "depression": "low mood, anhedonia, apathy, suicidal thoughts",
}

# Subreddits whose name settles which drug a post is about when the text only says
# "it", "my shot", or "the med". Keys are lowercase subreddit names; subreddits in
# apps/post-ingestion/recent_ingest.py that are not about one drug are left out.
SUBREDDIT_DRUG_HINTS: Dict[str, str] = {
    "ozempic": "Ozempic",
    "ozempicforweightloss": "Ozempic",
    "wegovy": "Wegovy",
    "wegovyweightloss": "Wegovy",
    "mounjaro": "Mounjaro",
    "zepbound": "Zepbound",
    "tirzepatidecompound": "Compounded Tirzepatide",
    "semaglutide": "Semaglutide",
    "liraglutide": "Liraglutide",
}
