# Survey artifacts

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
