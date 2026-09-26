"""Record (or verify) SHA-256 hashes of the frozen repaired first pass.

Run: python survey/freeze_first_pass.py [--check]
After freezing, any change to a listed file requires a dated amendment,
a consistent reassessment and a new freeze; the blind recode must compare
against the hashes recorded here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "survey" / "evidence_audit" / "freeze_manifest.json"
FROZEN_ON = "2026-09-25"
FILES = [
    "survey/coding_scheme.md",
    "survey/coding_amendment_2026-09-23.md",
    "survey/corpus.csv",
    "survey/evidence_audit/ledger.json",
    "survey/evidence_audit/repaired_coding_sheet.csv",
    "survey/evidence_audit/repaired_first_pass.csv",
    "survey/evidence_audit/repaired_summary.json",
    "survey/build_repaired_coding_sheet.py",
    "survey/validate_evidence_audit.py",
] + [f"survey/evidence_audit/reviews/{rank:02d}.json" for rank in range(1, 81)]


def digest(path: str) -> str:
    # CRLF is normalised to LF so hashes do not depend on core.autocrlf checkouts.
    return hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def manifest() -> dict:
    return {
        "status": "frozen_repaired_first_pass_non_blind",
        "frozen_on": FROZEN_ON,
        "review_mode": "non_blind_evidence_audit (single auditor, retrospective amendment)",
        "not_claimed": [
            "independent or blind agreement",
            "full-paper replication or recomputation",
            "correctness of evidence beyond documented locators",
            "preregistration of the 2026-09-23 amendment",
        ],
        "blind_recode_sample_ranks": [3, 4, 8, 9, 12, 13, 18, 36, 41, 44, 45, 50, 52, 55, 69, 72],
        "hash_policy": "sha256 of file bytes with CRLF normalised to LF",
        "sha256": {path: digest(path) for path in FILES},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    current = manifest()
    if args.check:
        recorded = json.loads(MANIFEST.read_text(encoding="utf-8"))
        changed = [p for p, h in recorded["sha256"].items() if current["sha256"].get(p) != h]
        if changed:
            raise SystemExit("Frozen files changed: " + ", ".join(changed))
        print(f"frozen first pass intact ({len(recorded['sha256'])} files)")
        return
    MANIFEST.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8", newline="")
    print(f"wrote {MANIFEST.relative_to(ROOT)} with {len(FILES)} hashes")


if __name__ == "__main__":
    main()
