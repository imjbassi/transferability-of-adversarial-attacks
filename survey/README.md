# Survey artifacts

Machine-readable record for the 80-paper survey in the manuscript.

**File paths here are fixed on purpose.** The preregistration tag, the freeze manifest (`evidence_audit/freeze_manifest.json`) and the frozen evidence reviews all cite files in this directory by path. Files are therefore grouped by the map below rather than moved into subfolders.

## Status

- The repaired first pass is complete for all 80 papers and frozen: tag `repaired-first-pass-2026-09-25`, `evidence_audit/freeze_manifest.json`.
- It is non-blind and single-auditor. Corrections found afterwards are recorded in `evidence_audit/post_freeze_errata.md`.
- An independent blind recode of the preregistered 16-paper sample is still outstanding; the packet is in `blind_recode/`.
- **Historical correction (22 September 2026).** The historical generator filled both "passes" from the same judgment constants, so its reported kappa of 1 is invalid. `reliability.json` withdraws it. `first_pass.json`, `recode_16.csv` and `coding_sheet.csv` are kept as provenance only, not as evidence of a blind recode or a full-text audit.

## File map

### Corpus, preregistered at tag `survey-preregistration`

| File | Purpose |
|---|---|
| `query.json` | Exact retrieval specification and UTC run time |
| `semantic_scholar_raw.json` | Complete paginated Semantic Scholar response |
| `corpus.csv` | Citation-sorted, text-filtered top-80 list (frozen) |
| `query_semantic_scholar.py` | Reruns the query; this creates a new time-indexed corpus and does not reproduce the frozen one |
| `download_papers.py` | Downloads openly accessible corpus PDFs and extracts text; the cache stays outside the repository |

### Coding scheme and codes

| File | Purpose |
|---|---|
| `coding_scheme.md` | Preregistered six-field scheme (frozen) |
| `coding_amendment_2026-09-23.md` | Retrospective clarification of result scope, aggregation and applicability; not preregistered (frozen) |
| `evidence_audit/` | Per-paper evidence reviews, ledger, repaired exports, freeze manifest and errata. See its README |
| `build_repaired_coding_sheet.py`, `validate_evidence_audit.py` | Build and validate the repaired exports from the reviews (frozen) |
| `freeze_first_pass.py` | Writes and checks the freeze manifest |
| `coding_sheet.csv`, `first_pass.json`, `recode_16.csv`, `reliability.json` | Historical records, kept for provenance (see Status) |
| `build_coding_outputs.py` | Structural validation of the historical sheet only; it generates no judgments |

### Reliability (blind recode)

| File | Purpose |
|---|---|
| `blind_recode/` | Judgment-free packet for an independent recoder |
| `build_blind_recode_packet.py` | Regenerates and checks that packet |
| `compute_reliability.py` | Cohen's kappa per field, once a genuine blind recode exists |

### Bounds: max(0, attacked error − clean error)

| File | Purpose |
|---|---|
| `compute_bounds.py`, `analytic_bounds.csv`, `analytic_bounds_summary.json` | Historical nominal worked case: 96 rates from rank 38 (72 single-model plus 24 against an ensemble containing the source) |
| `rounding_bounds.py`, `analytic_bounds_rounding.json` | The same case with displayed-value rounding |
| `rank38_bounds_strata.py`, `analytic_bounds_rank38_strata.json` | Rank 38 split into single-model and ensemble rates, plus the Table 3 cells |
| `rank68_bounds.py`, `analytic_bounds_rank68.json` | Rank 68 (DAmageNet), 18 victims |
| `rank20_bounds.py`, `analytic_bounds_rank20.json` | Rank 20 (ILA), 108 CIFAR-10 rates |
| `bounds_distribution.py`, `analytic_bounds_distribution.json` | Per-paper and pooled distribution over the extracted papers; not a corpus prevalence |
| `count_reconstruction.py` | Candidate integer counts from displayed percentages |

### Recomputation (field 6)

| File | Purpose |
|---|---|
| `recomputation/` | Manifested reruns of released code and the feasibility table. See `recomputation/PROVENANCE.md` and `recomputation/FEASIBILITY.md` |
| `recomputation_ledger.csv`, `build_recomputation_ledger.py`, `recomputation_notes.md` | Ledger regenerated from the archived metric files of the earlier SI-NI, VMI and SSA runs, with notes |
| `artifact_audit.csv` | Early artifact inspection of five candidates, superseded by the evidence reviews |

### Tests

`test_audit_tools.py` covers the bounds, counts, reliability, evidence records, repaired exports and every rerun archive.

## Checks

Run these from the repository root:

```text
python -m pytest -q survey/test_audit_tools.py
python survey/freeze_first_pass.py --check
python survey/build_repaired_coding_sheet.py --check
python survey/build_blind_recode_packet.py --check
python survey/recomputation/verify_predictions.py
```

These checks cover arithmetic, schema and frozen-file identity. They do not establish that the evidence judgments are correct.
