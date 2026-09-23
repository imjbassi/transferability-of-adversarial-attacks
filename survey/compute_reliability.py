"""Compare separately supplied blind recoding; provenance cannot prove blinding."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from build_coding_outputs import FIELDS

ROOT = Path(__file__).resolve().parent
SAMPLE = [3, 4, 8, 9, 12, 13, 18, 36, 41, 44, 45, 50, 52, 55, 69, 72]

def kappa(a, b):
    if len(a) != len(b) or not a:
        raise ValueError("Nonempty equal-length inputs required")
    observed = sum(x == y for x, y in zip(a, b)) / len(a)
    ca, cb = Counter(a), Counter(b)
    expected = sum(ca[c] * cb[c] for c in set(a) | set(b)) / len(a) ** 2
    return {"n": len(a), "agreement": observed,
            "kappa": None if expected == 1 else (observed - expected) / (1 - expected)}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len({r["paper_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate paper IDs")
    for row in rows:
        for field in FIELDS:
            if row[field] not in {"yes", "no", "unclear"}:
                raise ValueError("All judgments must be completed")
        if not all(f"f{i}=" in row.get("evidence", "") for i in range(1, 7)):
            raise ValueError("Six field-specific evidence markers required")
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--first-pass", type=Path, required=True)
    parser.add_argument("--blind-recode", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    args = parser.parse_args()
    if args.blind_recode.resolve() == (ROOT / "recode_16.csv").resolve():
        raise ValueError("Historical recode is invalid")
    if sha(args.blind_recode) == sha(ROOT / "recode_16.csv"):
        raise ValueError("Historical recode cannot be reused under another filename")
    provenance = json.loads(args.provenance.read_text(encoding="utf-8"))
    for key in ("coder", "completed_at_utc", "blinding_method"):
        if not provenance.get(key):
            raise ValueError(f"Missing provenance: {key}")
    if provenance.get("first_pass_hidden") is not True:
        raise ValueError("Blind recode attestation required")
    if provenance.get("first_pass_evidence_audited") is not True:
        raise ValueError("Freeze an evidence-audited first pass before reliability assessment")
    if provenance.get("first_pass_sha256") != sha(args.first_pass):
        raise ValueError("Provenance must identify the frozen first pass")
    first, second = read_rows(args.first_pass), read_rows(args.blind_recode)
    with (ROOT / "corpus.csv").open(encoding="utf-8-sig", newline="") as handle:
        corpus = list(csv.DictReader(handle))
    if [r["paper_id"] for r in first] != [r["paper_id"] for r in corpus]:
        raise ValueError("First pass must match the frozen corpus")
    sample_ids = {corpus[i - 1]["paper_id"] for i in SAMPLE}
    if len(second) != 16 or {r["paper_id"] for r in second} != sample_ids:
        raise ValueError("Blind recode must contain the fixed 16-paper sample")
    by_id = {r["paper_id"]: r for r in first}
    result = {f: kappa([by_id[r["paper_id"]][f] for r in second],
                       [r[f] for r in second]) for f in FIELDS}
    print(json.dumps({
        "status": "calculated_from_supplied_records_not_independently_verified",
        "first_pass_sha256": sha(args.first_pass),
        "recode_sha256": sha(args.blind_recode),
        "provenance": provenance,
        "by_field": result,
        "requires_tightening_and_full_recode": any(
            r["kappa"] is not None and r["kappa"] < 0.7 for r in result.values()),
        "undefined_fields": [f for f, r in result.items() if r["kappa"] is None],
        "warning": "Provenance is an attestation, not proof of blinding or valid evidence."
    }, indent=2))

if __name__ == "__main__":
    main()
