"""Stratified rounding-aware bounds for rank 38 (Wu et al., CVPR 2020).

The historical analytic_bounds.csv/summary and analytic_bounds_rounding.json mix
72 single-target transfer rates with 24 rates against an ensemble that contains
the source model. This separate output reports the two strata apart and adds the
Table 3 cells (Inception V4 source) that the historical files omit. Nothing in
the historical files or the frozen first pass is changed.

Run: python survey/rank38_bounds_strata.py --output survey/analytic_bounds_rank38_strata.json
"""
import argparse
import json
import statistics
from pathlib import Path

from compute_bounds import PAPER_ID, TARGETS
from rounding_bounds import bounds, build as build_table1

CLEAN = dict(zip(TARGETS, ["89.6", "96.4", "97.6", "100", "99.8"]))
SOURCE_TABLE3 = "Inception V4"
# Table 3, PDF p. 8, undefended columns, as printed (accuracy %). The TAP row
# duplicates Table 1 and the Inception V4 column is white-box; both are omitted.
TABLE3 = {
    "TAP+ATA": {"ResNet V2": "53.6", "Inception V3": "22.7", "Inception-ResNet V2": "19.8", "Ensemble": "48.1"},
    "TI": {"ResNet V2": "57.1", "Inception V3": "30.9", "Inception-ResNet V2": "26.9", "Ensemble": "58.3"},
    "TI+ATA": {"ResNet V2": "56.2", "Inception V3": "24.9", "Inception-ResNet V2": "24.2", "Ensemble": "50.1"},
}


def summary(rows):
    lower = [r["induced_mass_lower_percent"] for r in rows]
    return dict(rates=len(rows), minimum_percent=min(lower), median_percent=round(statistics.median(lower), 6),
                maximum_percent=max(lower), mean_percent=round(statistics.mean(lower), 6))


def build():
    table1 = [dict(r, table="Table 1") for r in build_table1()["rows"]]
    table3 = []
    for attack, cells in TABLE3.items():
        for target, accuracy in cells.items():
            table3.append(dict(paper_id=PAPER_ID, source=SOURCE_TABLE3, target=target, attack=attack,
                               table="Table 3", clean_display_percent=CLEAN[target],
                               attacked_display_percent=accuracy, **bounds(CLEAN[target], accuracy)))
    rows = table1 + table3
    single = [r for r in rows if r["target"] != "Ensemble"]
    ensemble = [r for r in rows if r["target"] == "Ensemble"]
    return dict(
        scope="Single-paper stratification for rank 38; correlated rates from one paper, one image population",
        evidence="Wu et al. CVPR 2020, Table 1 (PDF p. 6) and Table 3 (PDF p. 8); 1,000 ImageNet images; accuracy = 100 - unconditional misclassification",
        rounding_assumption="Nearest displayed unit; closed intervals include ties; 100% uses a one-point unit. Not sampling uncertainty.",
        extraction_status="Same-auditor extraction; Table 3 values checked against the PDF text layer; no independent second person",
        strata_definition=dict(
            single_target="Disjoint cross-model transfer to one undefended target",
            ensemble_contains_source="Target is the paper's ensemble, which includes the source model; arithmetic holds but this is not disjoint transfer"),
        excluded=["White-box diagonal cells", "Table 3 TAP row (duplicates Table 1)",
                  "Defended columns (no clean accuracy on this population)", "Figure 4 (graphical only)"],
        summaries=dict(
            single_target_table1=summary([r for r in single if r["table"] == "Table 1"]),
            single_target_all=summary(single),
            ensemble_contains_source_table1=summary([r for r in ensemble if r["table"] == "Table 1"]),
            ensemble_contains_source_all=summary(ensemble)),
        rows=rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.dumps(build(), indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
