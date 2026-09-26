"""Write the blind-recode packet for the preregistered 16-paper sample.

The packet contains paper identities, the frozen coding scheme and the dated
retrospective amendment, a blank judgment template and a provenance template.
It deliberately contains no first-pass judgment, reason, locator or evidence.

Run: python survey/build_blind_recode_packet.py [--check]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path

from build_coding_outputs import FIELDS
from compute_reliability import SAMPLE

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "survey" / "blind_recode"


def template_text() -> str:
    with (ROOT / "survey" / "corpus.csv").open(encoding="utf-8-sig", newline="") as handle:
        corpus = list(csv.DictReader(handle))
    buffer = io.StringIO(newline="")
    columns = ["paper_id", "rank", "title", "arxiv", "doi", *FIELDS, "evidence"]
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for rank in SAMPLE:
        paper = corpus[rank - 1]
        row = {"paper_id": paper["paper_id"], "rank": rank, "title": paper["title"],
               "arxiv": paper["arxiv"], "doi": paper["doi"], "evidence": ""}
        row.update({field: "" for field in FIELDS})
        writer.writerow(row)
    return buffer.getvalue()


PROVENANCE = {
    "coder": "",
    "completed_at_utc": "",
    "blinding_method": "",
    "first_pass_hidden": False,
    "first_pass_evidence_audited": True,
    "first_pass_sha256": "",
    "materials_used": ["coding_scheme.md", "coding_amendment_2026-09-23.md", "paper PDFs and linked supplements"],
    "note": "Fill in after recoding. Set first_pass_hidden to true only if you never saw survey/evidence_audit/, repaired_* files, coding_sheet.csv or any first-pass judgment.",
}


def outputs():
    return {
        PACKET / "recode_template.csv": template_text(),
        PACKET / "provenance_template.json": json.dumps(PROVENANCE, indent=2) + "\n",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = outputs()
    copies = {PACKET / "coding_scheme.md": ROOT / "survey" / "coding_scheme.md",
              PACKET / "coding_amendment_2026-09-23.md": ROOT / "survey" / "coding_amendment_2026-09-23.md"}
    if args.check:
        for path, text in files.items():
            if path.read_text(encoding="utf-8") != text:
                raise SystemExit(f"Out of date: {path}")
        for dst, src in copies.items():
            if dst.read_bytes().replace(b"\r\n", b"\n") != src.read_bytes().replace(b"\r\n", b"\n"):
                raise SystemExit(f"Out of date: {dst}")
        print("blind recode packet up to date")
        return
    PACKET.mkdir(exist_ok=True)
    for path, text in files.items():
        path.write_text(text, encoding="utf-8", newline="")
    for dst, src in copies.items():
        dst.write_bytes(src.read_bytes().replace(b"\r\n", b"\n"))
    print(f"wrote {len(files) + len(copies)} files to {PACKET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
