# Survey artifacts

## Audit correction, 22 September 2026

This is an unvalidated working record, not a publication-ready survey.
The historical generator populated both passes from the same judgment constants;
the reported kappa of 1 is invalid. `reliability.json` withdraws it. The retained
`recode_16.csv` and `first_pass.json` are historical records, not evidence of a
blind recode or completed full-text audit. All 480 judgments need evidence review.
The artifact audit inspected five candidates, not all 80 releases. The 96 bounds
come from one paper and are nominal calculations from rounded table values.
Recomputation covers selected configurations; ports are not validated replications.
These qualifications supersede the historical descriptions below.

`build_coding_outputs.py` now only validates structure and reports provisional
counts. It does not generate judgments, recodes, completion times, or kappa.
Use `recomputation/verify_predictions.py` for dependency-free arithmetic checks.
The original corpus, scheme, coding sheet and historical recode are preserved.

This directory is the machine-readable record for the 80-paper survey in the
manuscript.

- `query.json` records the exact retrieval specification and UTC run time.
- `semantic_scholar_raw.json` is the complete paginated Semantic Scholar API
  response used to build the corpus.
- `corpus.csv` is the citation-sorted, text-filtered top-80 list frozen at tag
  `survey-preregistration`.
- `coding_scheme.md` is the preregistered six-field scheme.
- `coding_sheet.csv` contains one paper per row, all six judgments, and evidence
  locators. Silence and unresolved ambiguity are coded `unclear`.
- `first_pass.json`, `recode_16.csv`, and `reliability.json` record the immediate
  20% repeatability check. The originally planned seven-day interval was waived
  by explicit user instruction, so these values are not presented as delayed
  intra-rater stability.
- `analytic_bounds.csv` and `analytic_bounds_summary.json` contain every
  equation-1 bound that could be aligned at the required source-target-attack
  granularity.
- `recomputation_ledger.csv` records immutable release commits, execution status,
  published comparators, and any recomputed PTR, CTR, \(a_{st}\), and \(b_{st}\).

Regenerate the derived coding and bounds files from the repository root with:

```text
python survey/build_coding_outputs.py
python survey/compute_bounds.py
```

The coding script expects the downloaded full-text cache named in the script;
the archived coding sheet remains the portable study record. The corpus query
can be rerun separately with `query_semantic_scholar.py`, but doing so creates a
new time-indexed corpus rather than reproducing the frozen one.
