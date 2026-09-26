"""Rounding-aware bounds for rank 68 (DAmageNet, arXiv 2001.06325v3) Table 5.

Clean ImageNet and adversarial DAmageNet top-1 error rates are reported for the
same 50,000 validation images without conditioning (see reviews/68.json), so the
fixed-predictor identity applies per victim. The VGG19 source row is excluded;
defense columns lack a matched clean error and are excluded.

Run: python survey/rank68_bounds.py --output survey/analytic_bounds_rank68.json
"""
import argparse
import json
import statistics
from decimal import Decimal
from pathlib import Path

from rounding_bounds import bounds

PAPER_ID = "0ab0b3cf5811a219339ad3715ce719f550122a62"
SOURCE = "VGG19"
# Victim: (ImageNet error %, DAmageNet error %) as printed in Table 5, PDF p. 8.
# Text-layer extraction and a 200-dpi render of p. 8 agree for every value below.
TABLE5 = {
    "VGG16": ("38.51", "99.85"), "VGG19": ("38.60", "99.99"),
    "RN50": ("36.65", "93.94"), "RN101": ("29.38", "88.13"), "RN152": ("28.65", "86.78"),
    "NASNetM": ("27.03", "92.81"), "NASNetL": ("17.77", "86.32"),
    "IncV3": ("22.52", "89.84"), "IncRNV2": ("24.60", "88.09"), "Xception": ("21.38", "90.57"),
    "DN121": ("26.85", "96.14"), "DN169": ("25.16", "94.09"), "DN201": ("24.36", "93.44"),
    "IncV3adv": ("22.86", "82.23"), "IncV3advens3": ("24.12", "80.72"),
    "IncV3advens4": ("24.45", "79.26"), "IncRNV2adv": ("20.03", "76.42"),
    "IncRNV2advens": ("20.35", "70.70"), "RNXt101den": ("32.20", "35.40"),
}


def accuracy(error_display: str) -> str:
    """100 - displayed error, keeping the displayed precision exactly."""
    return str(Decimal(100) - Decimal(error_display))


def build():
    rows = []
    for victim, (clean_err, adv_err) in TABLE5.items():
        if victim == SOURCE:
            continue
        rows.append(dict(paper_id=PAPER_ID, source=SOURCE, target=victim, attack="SI-AoA (DAmageNet)",
                         clean_error_display_percent=clean_err, attacked_error_display_percent=adv_err,
                         nominal_induced_mass_percent=float(max(Decimal(0), Decimal(adv_err) - Decimal(clean_err))),
                         **bounds(accuracy(clean_err), accuracy(adv_err))))
    lower = [r["induced_mass_lower_percent"] for r in rows]
    return dict(
        scope="Single-paper extraction for rank 68; one source (VGG19), 18 victims; correlated observations",
        evidence="Chen et al., arXiv 2001.06325v3, Section 4.4 and Table 5, PDF p. 8; population: all 50,000 ImageNet validation images",
        rounding_assumption="Nearest displayed unit (0.01 percentage points); closed intervals include ties. Not sampling uncertainty.",
        extraction_status="Same-auditor text-layer extraction and 200-dpi visual recheck agree; no independent second person",
        caveats=[
            "Section 4.4 also says the originals 'come from ImageNet training set'; the population match relies on the stated generation 'from all 50000 samples from ImageNet validation set'.",
            "Victims are Keras Applications models whose errors may differ from original references (Table 5 note in the paper).",
            "Defense columns are excluded because no clean error is reported for the defended pipelines.",
        ],
        papers_extracted=1, rates_bounded=len(rows),
        summary=dict(minimum_percent=min(lower), median_percent=statistics.median(lower),
                     maximum_percent=max(lower), mean_percent=statistics.mean(lower)),
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
