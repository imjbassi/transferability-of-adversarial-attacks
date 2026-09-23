"""Structural validation only; never promotes partial evidence to completed coding."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def validate():
    data = json.loads((ROOT / "evidence_audit/ledger.json").read_text(encoding="utf-8"))
    with (ROOT / "corpus.csv").open(encoding="utf-8-sig", newline="") as handle:
        corpus = list(csv.DictReader(handle))
    papers = data["papers"]
    if len(papers) != 80 or len({p["paper_id"] for p in papers}) != 80:
        raise ValueError("Audit must retain all 80 distinct frozen papers")
    for expected, actual in zip(corpus, papers):
        if (expected["paper_id"], int(expected["rank"]), expected["title"]) != (
            actual["paper_id"], actual["rank"], actual["title"]
        ):
            raise ValueError("Audit order or identity differs from frozen corpus")
        if actual["evidence_audit"] not in {"pending", "partial", "complete"}:
            raise ValueError("Invalid audit workflow state")
        if actual["evidence_audit"] == "partial" and not actual["notes"]:
            raise ValueError("Partial review requires an evidence locator")
        if actual["evidence_audit"] == "complete":
            raise ValueError("Complete status requires a future substantive evidence schema; not supported by this partial ledger")
    counts = Counter(p["evidence_audit"] for p in papers)
    return {
        "papers": len(papers),
        "partial": counts["partial"],
        "pending": counts["pending"],
        "complete": counts["complete"],
        "warning": "Validates identities and workflow states, not evidence correctness. No survey prevalence is calculated."
    }

if __name__ == "__main__":
    print(json.dumps(validate(), indent=2))
