"""Validate the preserved provisional coding sheet without manufacturing judgments.

The v1.2.0 generator used identical constants for both coding passes.
Those outputs cannot establish reliability. This replacement never rewrites
the coding sheet, recode, or completion timestamps.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "clean_accuracy_source_target_separate",
    "transfer_denominator_clean_correct",
    "conditions_on_source_attack_success",
    "reports_absolute_counts",
    "numeric_linf_or_l2_budget",
    "artifacts_sufficient_to_recompute",
]

def main():
    with (ROOT / "survey/coding_sheet.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with (ROOT / "survey/corpus.csv").open(encoding="utf-8", newline="") as handle:
        corpus = list(csv.DictReader(handle))
    ids = [row["paper_id"] for row in rows]
    if len(ids) != 80 or len(set(ids)) != 80:
        raise ValueError("Expected 80 unique paper IDs")
    if ids != [row["paper_id"] for row in corpus]:
        raise ValueError("Coding sheet order/IDs differ from the frozen corpus")
    for row in rows:
        for field in FIELDS:
            if row[field] not in {"yes", "no", "unclear"}:
                raise ValueError(f"Invalid judgment: {row['paper_id']} {field}")
        if not all(f"f{i}=" in row["evidence"] for i in range(1, 7)):
            raise ValueError(f"Missing evidence field: {row['paper_id']}")
    print(json.dumps({
        "status": "provisional_unvalidated",
        "paper_count": len(rows),
        "counts": {field: dict(Counter(r[field] for r in rows)) for field in FIELDS},
        "warning": "Structural checks do not validate substantive evidence or reliability."
    }, indent=2))

if __name__ == "__main__":
    main()
