#!/usr/bin/env python3
"""
Score extraction runs against the gold labels, field by field.

Gold labels are backups/extraction-eval/gold-chunks/gold_*.json: one object per post
with the comparable fields (see eval_lib.comparable), labeled by a stronger model
applying the definitions in apps/post-extraction/prompts.py.

For each field, over every post:
    acc   the run and gold agree (both null counts as agreement)
    prec  of the posts where the run gave a value, the share that matches gold
    rec   of the posts where gold has a value, the share the run matched
Sentiment fields also report MAE where both have a value and `invented`, the number of
posts where the run scored an opinion the gold says was never expressed.
weight_loss_lbs_view is weight loss as the site computes it today (start minus end
weight); weight_loss_lbs also counts the weight_lost column.

Usage (from the repository root, venv active):
    python3 scripts/extraction-eval/score.py v1-minimal v2-low
"""

import argparse
import glob
import sys
from typing import Any, Callable, Dict, List, Optional

from eval_lib import DATA_DIR, read_json, to_comparable, to_lbs

COUNTRY_ALIASES = {"us": "USA", "united states": "USA", "usa": "USA", "united kingdom": "UK", "uk": "UK", "england": "UK"}


def load_gold() -> Dict[str, Dict[str, Any]]:
    gold: Dict[str, Dict[str, Any]] = {}
    for path in sorted(glob.glob(str(DATA_DIR / "gold-chunks" / "gold_*.json"))):
        for label in read_json(path):
            row = dict(label)
            row["side_effects"] = [{"name": n} for n in label.get("side_effects") or []]
            # Gold states only a total the post gives, as the pipeline does; derive the
            # rest from start and end weights the same way rows.derive_weight_lost does.
            start, end = row.get("beginning_weight"), row.get("end_weight")
            if row.get("weight_lost") is None and start and end:
                lost_lbs = to_lbs(start["value"], start["unit"]) - to_lbs(end["value"], end["unit"])
                if lost_lbs > 0:
                    row["weight_lost"] = {"value": lost_lbs, "unit": "lbs"}
            gold[label["post_id"]] = to_comparable(row)
    return gold


def make_near_matcher(tolerance: Callable[[float], float]) -> Callable[[Any, Any], bool]:
    return lambda a, b: abs(a - b) <= tolerance(b)


def _normalize_country(v: Optional[str]) -> Optional[str]:
    return COUNTRY_ALIASES.get(v.strip().lower(), v.strip()) if isinstance(v, str) else None


FIELDS: Dict[str, Callable[[Any, Any], bool]] = {
    "post_type": lambda a, b: a == b,
    "treatment_status": lambda a, b: a == b,
    "primary_drug": lambda a, b: a == b,
    "drug_source": lambda a, b: a == b,
    "weight_loss_lbs_view": make_near_matcher(lambda g: max(2.0, 0.05 * g)),
    "weight_loss_lbs": make_near_matcher(lambda g: max(2.0, 0.05 * g)),
    "beginning_weight_lbs": make_near_matcher(lambda g: 1.0),
    "end_weight_lbs": make_near_matcher(lambda g: 1.0),
    "duration_weeks": make_near_matcher(lambda g: max(2.0, 0.15 * g)),
    "cost_per_month": make_near_matcher(lambda g: max(1.0, 0.05 * g)),
    "has_insurance": lambda a, b: a == b,
    "age": lambda a, b: a == b,
    "sex": lambda a, b: a == b,
    "country": lambda a, b: _normalize_country(a) == _normalize_country(b),
}
SENTIMENT_FIELDS = ("sentiment_post", "recommendation_score")
# Fields v1 has no column for; reported as n/a for a run that never fills them.
V2_ONLY_FIELDS = ("post_type", "treatment_status")


def score_run(run: Dict[str, Any], gold: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    preds = {pid: to_comparable(r["row"]) if "row" in r else None for pid, r in run.items()}
    ids = [pid for pid in gold if pid in preds]
    if not ids:
        sys.exit("No post in this run has a gold label: were they sampled from the same posts.json?")
    failed = sum(1 for pid in ids if preds[pid] is None)
    out: Dict[str, str] = {"posts": f"{len(ids)} ({failed} failed)"}

    for field, match in FIELDS.items():
        if field in V2_ONLY_FIELDS and all(preds[p] is None or preds[p].get(field) is None for p in ids):
            out[field] = "n/a"
            continue
        agree = pred_n = pred_ok = gold_n = gold_ok = 0
        for pid in ids:
            g = gold[pid].get(field)
            p = preds[pid].get(field) if preds[pid] else None
            ok = p is not None and g is not None and match(p, g)
            agree += ok or (p is None and g is None)
            pred_n += p is not None
            pred_ok += ok
            gold_n += g is not None
            gold_ok += ok
        out[field] = f"acc {agree / len(ids):.0%}  prec {pred_ok / max(pred_n, 1):.0%} ({pred_n})  rec {gold_ok / max(gold_n, 1):.0%} ({gold_n})"

    for field in SENTIMENT_FIELDS:
        agree_null = invented = 0
        errors: List[float] = []
        for pid in ids:
            g = gold[pid].get(field)
            p = preds[pid].get(field) if preds[pid] else None
            agree_null += (g is None) == (p is None)
            invented += g is None and p is not None
            if g is not None and p is not None:
                errors.append(abs(p - g))
        mae = sum(errors) / len(errors) if errors else float("nan")
        out[field] = f"null-agree {agree_null / len(ids):.0%}  invented {invented}  MAE {mae:.2f} (n={len(errors)})"

    tp = fp = fn = 0
    for pid in ids:
        g = set(gold[pid]["side_effects"]) - {"other"}
        p = set(preds[pid]["side_effects"]) - {"other"} if preds[pid] else set()
        tp, fp, fn = tp + len(p & g), fp + len(p - g), fn + len(g - p)
    precision, recall = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
    out["side_effects"] = f"P {precision:.0%}  R {recall:.0%}  F1 {2 * precision * recall / max(precision + recall, 1e-9):.0%}  (gold {tp + fn})"

    costs = [r["meta"].get("cost_usd", 0) for pid, r in run.items() if "row" in r]
    out["cost/post"] = f"${sum(costs) / max(len(costs), 1):.6f}"
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+", help="Run names under backups/extraction-eval/runs/")
    args = parser.parse_args()
    gold = load_gold()
    print(f"gold labels: {len(gold)}")
    scores = {name: score_run(read_json(f"runs/{name}.json"), gold) for name in args.runs}
    for field in next(iter(scores.values())):
        print(f"\n{field}")
        for name, s in scores.items():
            print(f"  {name:22s} {s[field]}")


if __name__ == "__main__":
    main()
