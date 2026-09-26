# Blind 16-paper recode packet

This packet is for an **independent recoder who has not seen the first pass**. The Claude session that produced the first pass has seen every judgment and cannot act as the recoder. Waiving the waiting period does not waive independence.

## Give the recoder only

- `recode_template.csv`: the preregistered 16-paper sample (ranks 3, 4, 8, 9, 12, 13, 18, 36, 41, 44, 45, 50, 52, 55, 69, 72; seed 20260919), with identifiers only;
- `coding_scheme.md` (frozen scheme) and `coding_amendment_2026-09-23.md` (dated retrospective clarification, not preregistered);
- the papers and their linked supplements, obtained independently;
- `provenance_template.json`.

Do **not** give access to `survey/evidence_audit/`, `survey/coding_sheet.csv`, `survey/recode_16.csv`, any `repaired_*` file, the repository history, or the paper manuscript.

## Recoding rules

For each paper and each of the six fields, enter `yes`, `no` or `unclear`, following the scheme and amendment (inventory result scopes first; unanimous aggregation for fields 2-3; `unclear` with a non-applicability note when no original cross-model evaluation exists). In `evidence`, write six markers `f1=... | f2=... | ... | f6=...`, each with a locator (section/table/page) and a short rationale.

## Comparison (after recoding)

1. Fill in `provenance_template.json`, including `first_pass_sha256` equal to the SHA-256 of `survey/evidence_audit/repaired_first_pass.csv` in the frozen tag, and save it as a new file.
2. Run `python survey/compute_reliability.py --first-pass survey/evidence_audit/repaired_first_pass.csv --blind-recode <recode.csv> --provenance <provenance.json>`.
3. Archive the recode, provenance and output. A kappa below 0.7 in any field requires a dated tightening amendment and a full recode of all 80 papers. Single-category (undefined) kappa stays null.

Provenance is an attestation, not proof of blinding.
