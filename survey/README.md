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
The historical files below are retained for provenance, not endorsed as validated results.

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
- `coding_amendment_2026-09-23.md` records retrospective clarification of result
  scope, aggregation and applicability; it is not preregistered.
- `coding_sheet.csv` preserves the historical, unvalidated six-field judgments.
  The repair reviews live in `evidence_audit/reviews/` until all 80 are complete.
- `first_pass.json` and `recode_16.csv` preserve the invalid historical check;
  `reliability.json` withdraws it. Waiving a delay did not waive independent
  blinding. A new blind pass and valid kappa remain outstanding.
- `analytic_bounds.csv` and `analytic_bounds_summary.json` preserve 96 nominal
  calculations from one paper, not an exhaustive corpus-wide eligibility audit.
  `analytic_bounds_rounding.json` separately handles displayed-value rounding.
- `recomputation_ledger.csv` records immutable release commits, execution status,
  published comparators, and any recomputed PTR, CTR, \(a_{st}\), and \(b_{st}\).

Run non-mutating validation from the repository root with:

```text
python survey/build_coding_outputs.py
python survey/validate_evidence_audit.py
python survey/test_audit_tools.py
```

These checks do not establish evidence correctness or generate a new coding
sheet. The historical `compute_bounds.py` regenerates the nominal worked case,
not new corpus coverage. The corpus query can be rerun separately with
`query_semantic_scholar.py`, but doing so creates a new time-indexed corpus
rather than reproducing the frozen one.
