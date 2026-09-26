"""Export the repaired (non-blind, first-pass) coding sheet from the 80 evidence reviews.

The historical ``coding_sheet.csv`` is never touched. Outputs are written to
``evidence_audit/`` and are deterministic given the review files, so the
freeze manifest hashes can be re-derived by anyone.

Run: python survey/build_repaired_coding_sheet.py [--check]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

from validate_evidence_audit import validate_review  # noqa: F401  (import guarantees schema module exists)

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "survey" / "evidence_audit"
FIELDS = {
    "f1": "clean_accuracy_source_target_separate",
    "f2": "transfer_denominator_clean_correct",
    "f3": "conditions_on_source_attack_success",
    "f4": "reports_absolute_counts",
    "f5": "numeric_linf_or_l2_budget",
    "f6": "artifacts_sufficient_to_recompute",
}
NOT_APPLICABLE = "not_applicable_to_located_results"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_reviews():
    ledger = json.loads((AUDIT / "ledger.json").read_text(encoding="utf-8"))
    entries = sorted(ledger["papers"], key=lambda e: e["rank"])
    if len(entries) != 80:
        raise ValueError("Ledger must list 80 papers")
    reviews = []
    for entry in entries:
        if entry["evidence_audit"] != "complete":
            raise ValueError(f"Rank {entry['rank']} is not complete; export refused")
        path = AUDIT / "reviews" / f"{entry['rank']:02d}.json"
        raw = path.read_bytes()
        review = json.loads(raw.decode("utf-8"))
        if review["paper_id"] != entry["paper_id"]:
            raise ValueError(f"Paper ID mismatch at rank {entry['rank']}")
        reviews.append((entry, review, sha256_bytes(raw.replace(b"\r\n", b"\n")), path))
    return reviews


def row_for(entry, review, digest):
    j = review["judgments"]
    groups = review["result_groups"]
    row = {
        "rank": review["rank"],
        "paper_id": review["paper_id"],
        "title": entry.get("title", ""),
        "applicability": review["coverage"]["applicability"],
        "in_scope_groups": len(groups),
    }
    for key, name in FIELDS.items():
        row[name] = j[key]["value"]
        row[f"{key}_reason"] = j[key]["reason"]
    for key in ("f2", "f3"):
        values = {g[key] for g in groups}
        row[f"{key}_any_explicit_yes"] = "yes" in values
        row[f"{key}_any_explicit_no"] = "no" in values
    row["artifact_review"] = entry.get("artifact_review", "")
    row["bounds_review"] = entry.get("bounds_review", "")
    row["review_file_sha256"] = digest
    return row


def summarise(rows):
    applicable = [r for r in rows if r["f1_reason"] != NOT_APPLICABLE]
    summary = {
        "status": "repaired_first_pass_non_blind_unvalidated",
        "paper_count": len(rows),
        "non_applicable_papers": [r["rank"] for r in rows if r["f1_reason"] == NOT_APPLICABLE],
        "applicable_paper_count": len(applicable),
        "fields": {},
        "applicability_strata": dict(sorted(Counter(r["applicability"] for r in rows).items())),
        "warning": (
            "Non-blind single-auditor first pass under the retrospective 23 September 2026 amendment. "
            "Counts are not validated by an independent recode and must be reported with reason strata; "
            "unclear is never evidence that a paper is wrong."
        ),
    }
    for key, name in FIELDS.items():
        summary["fields"][name] = {
            "all_papers": dict(sorted(Counter(r[name] for r in rows).items())),
            "applicable_papers": dict(sorted(Counter(r[name] for r in applicable).items())),
            "value_by_reason": dict(sorted(Counter(f"{r[name]}|{r[key + '_reason']}" for r in rows).items())),
        }
    for key in ("f2", "f3"):
        summary["fields"][FIELDS[key]]["papers_with_any_explicit_yes_group"] = sum(r[f"{key}_any_explicit_yes"] for r in rows)
        summary["fields"][FIELDS[key]]["papers_with_any_explicit_no_group"] = sum(r[f"{key}_any_explicit_no"] for r in rows)
    return summary


def first_pass_row(entry, review, corpus_row):
    """Row in the historical coding_sheet.csv format consumed by compute_reliability.py."""
    j = review["judgments"]
    row = {k: corpus_row[k] for k in ("paper_id", "title", "venue", "year", "citations")}
    parts = []
    for key, name in FIELDS.items():
        row[name] = j[key]["value"]
        text = f"{j[key]['reason']}; {j[key]['locator']}; {j[key]['evidence']}"
        parts.append(f"{key}=" + " ".join(text.replace("|", "/").split()))
    row["evidence"] = " | ".join(parts)
    return row


def render(rows):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify outputs match without writing")
    args = parser.parse_args()
    reviews = load_reviews()
    rows = [row_for(e, r, d) for e, r, d, _ in reviews]
    with (ROOT / "survey" / "corpus.csv").open(encoding="utf-8-sig", newline="") as handle:
        corpus = list(csv.DictReader(handle))
    if [c["paper_id"] for c in corpus] != [r["paper_id"] for r in rows]:
        raise ValueError("Review order must match the frozen corpus order")
    first_pass = [first_pass_row(e, r, c) for (e, r, _, _), c in zip(reviews, corpus)]
    sheet = render(rows)
    summary = json.dumps(summarise(rows), indent=2, ensure_ascii=False) + "\n"
    outputs = {
        AUDIT / "repaired_coding_sheet.csv": sheet,
        AUDIT / "repaired_first_pass.csv": render(first_pass),
        AUDIT / "repaired_summary.json": summary,
    }
    if args.check:
        for path, text in outputs.items():
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                raise SystemExit(f"Out of date: {path.relative_to(ROOT)}")
        print("repaired outputs up to date")
        return
    for path, text in outputs.items():
        path.write_text(text, encoding="utf-8", newline="")
    print(summary)


if __name__ == "__main__":
    main()
