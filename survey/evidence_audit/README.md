# Evidence audit: first repair batch

Started 23 September 2026. This is a non-blind evidence audit, not the independent recode.

## Current scope

The ledger retains all 80 frozen paper IDs. Twelve papers have partial, metric-specific evidence checks; 68 remain pending. No paper is marked fully audited and no historical categorical judgment has been overwritten. Pending is a workflow state, not a new coding category.

The third batch covers ranks 1 and 6–10 in [batch_01_06_10.md](batch_01_06_10.md). It documents explicit source-success conditioning for LLM jailbreak transfer, distinguishes transfer learning from attack transfer, flags a test/attacker-set population mismatch, and identifies two further bounds candidates requiring population alignment and extraction.

The second batch covers ranks 2–5 in [batch_02_05.md](batch_02_05.md). It confirms explicit clean-correct filtering in rank 2, distinguishes that from almost-correct wording in ranks 4–5, and records the rank-4 paper/code iteration discrepancy without assigning blame or assuming which configuration produced the published table.

- Rank 31, Inkawhich et al. 2019: Section 3 (PDF pp. 2-3) defines joint clean correctness and successful-source denominators for uTR/tTR. Section 5 (p. 4) reports model-specific clean errors. The same paper also reports error and targeted success without successful-source filtering. Thus the existence of both conditioned and unconditioned metrics must be recorded, rather than interpreting one as a contradiction of the other.
- Rank 38, Wu et al. 2020: Section 5.1 (pp. 5-6) defines the common 1,000-image dataset and top-1 target accuracy metric. Table 1 contains five clean accuracies and 120 attacked accuracies. Its 96 off-diagonal entries were checked against the cached text. Table 2 and the supplement are not yet fully reviewed.

## Source identification

Rank 31 PDF SHA-256: 737c264424564caf7f39b6e9ddc487227cf141f8c6d7511ef0e8e9420d7ffa7d.
Rank 38 PDF SHA-256: fb8dff58f38b94dde6bcf8597a1f239ce3a30b23a640868905a833bf526f46ee.

The cached text includes PDF-page delimiters. These hashes identify the source PDFs; this batch used extracted text, not a new visual PDF transcription.

## Scheme issue requiring transparent resolution

The frozen scheme codes a paper, while several rules refer to every surveyed result and field 3 refers to the reported transfer denominator. A paper may explicitly report several different metrics. Before completing the new pass, specify the surveyed metric/result set and a paper-level aggregation convention. Retain the original scheme/tag, record any clarification as a dated amendment, and apply it to all 80. Do not choose a convention after seeing which yields a larger reporting-insufficiency percentage.

The audit must also distinguish:
- an explicitly unconditioned rate from silence about conditioning;
- missing exact counts from recoverable integer counts;
- clean accuracy on the full dataset from accuracy on a filtered evaluation population;
- artifact existence from verified checkpoint/data/evaluator sufficiency;
- tangential task applicability from exclusion from the frozen corpus.

## Rounding-aware worked case

Run: `python survey/rounding_bounds.py --output survey/analytic_bounds_rounding.json`.

The separate JSON preserves displayed precision and supplies conservative bounds assuming rounding to the nearest displayed unit. The clean entry printed as 100% is treated as [99.5%,100%], not an exact zero-error claim. Under that assumption the 96 lower bounds range from 0.95 to 77.35 percentage points, with median 34.175 and mean 35.1427083333. These bounds are on all-input newly induced error mass, not CTR. They are not confidence intervals, and the 96 rates are correlated observations from one paper.

The nominal historical CSV is unchanged. A separate second extraction and corpus-wide eligibility assessment are still required.

## Next work

The count-reconstruction helper is tested independently of the coding sheet:
`count_reconstruction.count_candidates('23.5', 1000)` yields the unique count
235, whereas a denominator of 5,000 yields possible counts 1,173–1,177. This
requires a known, unaveraged denominator and nearest-unit rounding; it is not
permission to infer a denominator from the dataset name. The current audit test
suite contains 17 passing tests, including all 27 archived metric checks.

Finish the paper/supplement evidence audit and artifact/bounds decisions, with explicit metric populations and section/table locators. Freeze the audited first pass before a separate blind 16-paper recode. This context has seen first-pass judgments and must not be represented as blind. No valid kappa is available yet.
