# Extraction eval

Scores post-extraction variants against gold labels on real posts, so a change to the
prompt, schema, model, or reasoning effort is measured before it ships. Everything it
reads and writes lives in `backups/extraction-eval/` (gitignored: it holds Reddit text).

Run from the repository root with the venv active.

1. **Sample posts** (read-only against Supabase):
   `python3 scripts/extraction-eval/sample.py --recent 50 --long 30 --seed 7`
   writes `posts.json`: recent posts plus older long ones, which carry the weight, cost,
   and duration details the hard fields depend on.
2. **Label gold.** One object per post in `gold-chunks/gold_*.json`, with the keys
   `score.py` reads: `post_id`, `post_type`, `treatment_status`, `primary_drug`,
   `drug_source`, `beginning_weight`, `end_weight`, `weight_lost`, `duration_weeks`,
   `cost_per_month`, `has_insurance`, `side_effects` (canonical names), `sentiment_post`,
   `recommendation_score`, `age`, `sex`, `country`, `notes`. Label with a stronger model
   applying the definitions in `apps/post-extraction/prompts.py`, and spot-check the
   labels against the posts yourself. Do not run the labeler on the pipeline's OpenRouter
   key: it has a small daily cap that production shares. Relabel when a definition changes.
3. **Run variants**, each writing `runs/<variant>-<effort>.json`:
   `python3 scripts/extraction-eval/run.py v2 --effort low`
   `python3 scripts/extraction-eval/run.py v1 --effort minimal` (the legacy prompt and schema, as a baseline)
4. **Score**: `python3 scripts/extraction-eval/score.py v1-minimal v2-low`

`score.py` reduces every run to the values downstream consumers read, computed the way
they compute them (weight loss in lbs, canonical drug and side-effect names), and reports
per field: agreement, precision of the values the run gave, and recall of the values
gold has. Sentiment fields report how often the run scored an opinion the gold says was
never expressed. At 80 posts, a one- or two-post difference is noise; read the
disagreements (not only the totals) before concluding a variant is better.
