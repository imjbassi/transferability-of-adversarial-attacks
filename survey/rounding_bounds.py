"""Conservative equation-1 bounds from displayed percentages.

The existing nominal CSV is preserved. This emits a separate JSON worked case.
Rounding is an explicit nearest-displayed-unit assumption, not a confidence interval.
"""
import argparse
import json
import statistics
from decimal import Decimal
from pathlib import Path
from compute_bounds import ATTACKS, CLEAN, PAPER_ID, TARGETS, VALUES

D = Decimal

def interval(displayed):
    value = D(displayed)
    if not value.is_finite() or not D(0) <= value <= D(100):
        raise ValueError("Percentage must be finite and between 0 and 100")
    unit = D(1).scaleb(value.as_tuple().exponent)
    half = unit / 2
    return max(D(0), value - half), min(D(100), value + half)

def bounds(clean_display, attacked_display):
    c_lo, c_hi = interval(clean_display)
    a_lo, a_hi = interval(attacked_display)
    # newly induced mass = clean-and-attacked-wrong joint probability.
    lower = max(D(0), c_lo - a_hi)
    upper = min(c_hi, D(100) - a_lo)
    q_lower = None if c_lo == 0 else 100 * max(D(0), 1 - a_hi / c_lo)
    # Maximum persistent-clean-error share of unconditional attacked error.
    u_lo = D(100) - a_hi
    share = None if u_lo == 0 else min(D(1), (100 - c_lo) / u_lo)
    return dict(clean_accuracy_interval_percent=[float(c_lo), float(c_hi)],
                attacked_accuracy_interval_percent=[float(a_lo), float(a_hi)],
                induced_mass_lower_percent=float(lower),
                induced_mass_upper_percent=float(upper),
                target_clean_conditional_lower_percent=None if q_lower is None else float(q_lower),
                persistent_error_share_upper=None if share is None else float(share))

def build():
    clean_strings = ["89.6", "96.4", "97.6", "100", "99.8"]
    rows = []
    for source, matrix in VALUES.items():
        for attack, accuracies in zip(ATTACKS, matrix):
            for target, clean, accuracy in zip(TARGETS, clean_strings, accuracies):
                if source == target:
                    continue
                # Table 1's only two-decimal entry is diagonal and excluded.
                display = "0.01" if accuracy == 0.01 else f"{accuracy:.1f}"
                rows.append(dict(paper_id=PAPER_ID, source=source, target=target,
                                 attack=attack, clean_display_percent=clean,
                                 attacked_display_percent=display,
                                 **bounds(clean, display)))
    values = [row["induced_mass_lower_percent"] for row in rows]
    return dict(
        scope="Single-paper worked case; not exhaustive corpus extraction",
        evidence="Wu et al. CVPR 2020, Section 5.1 and Table 1, PDF pp. 5-6",
        rounding_assumption="Nearest displayed unit; closed intervals conservatively include rounding ties. 100% uses a one-percentage-point unit. Not sampling uncertainty.",
        extraction_status="Table 1 transcription checked against cached full text; no independent second extraction",
        papers_extracted=1, rates_bounded=len(rows),
        summary=dict(minimum_percent=min(values), median_percent=statistics.median(values),
                     maximum_percent=max(values), mean_percent=statistics.mean(values)),
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
