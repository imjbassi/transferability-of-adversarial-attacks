"""Per-paper and pooled distributions of rounding-aware lower bounds across extracted papers.

Inputs are the separate per-paper outputs; nothing historical or frozen is read
for values. Only disjoint single-target transfer rates are pooled (rank 38's
ensemble-containing-source stratum is reported but not pooled). Pooled rates
are correlated within papers; the paper-level summary weights papers equally.
This is a distribution over the papers extracted so far, not a corpus prevalence.

Run: python survey/bounds_distribution.py --output survey/analytic_bounds_distribution.json
"""
import argparse
import json
import statistics
from pathlib import Path

from rank20_bounds import build as build20
from rank38_bounds_strata import build as build38
from rank68_bounds import build as build68


def describe(values):
    return dict(rates=len(values), minimum_percent=min(values), median_percent=round(statistics.median(values), 6),
                maximum_percent=max(values), mean_percent=round(statistics.mean(values), 6))


def build():
    r38 = build38()["rows"]
    papers = {
        20: [r for r in build20()["rows"]],
        38: [r for r in r38 if r["target"] != "Ensemble"],
        68: [r for r in build68()["rows"]],
    }
    per_paper = {rank: describe([r["induced_mass_lower_percent"] for r in rows]) for rank, rows in papers.items()}
    pooled = [r["induced_mass_lower_percent"] for rows in papers.values() for r in rows]
    medians = [s["median_percent"] for s in per_paper.values()]
    return dict(
        scope="Papers with extracted matched-population unconditional rates so far (ranks 20, 38, 68); not a corpus prevalence",
        status="Same-auditor extractions; no independent second extraction; other candidate papers unresolved (see evidence_audit reviews)",
        per_paper=per_paper,
        rank38_ensemble_contains_source_not_pooled=describe(
            [r["induced_mass_lower_percent"] for r in r38 if r["target"] == "Ensemble"]),
        pooled_single_target=describe(pooled),
        paper_level=dict(papers=len(medians), median_of_paper_medians=round(statistics.median(medians), 6),
                         minimum_paper_median=min(medians), maximum_paper_median=max(medians)),
        pooled_share_by_paper={rank: round(len(rows) / len(pooled), 6) for rank, rows in papers.items()},
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.dumps(build(), indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
