# Evidence audit: first repair batch

Started 23 September 2026. This is a non-blind evidence audit, not the independent recode.

## Current scope

The ledger retains all 80 frozen paper IDs: ten documented reviews are complete (ranks 2, 3, 4, 5, 6, 7, 8, 9, 11 and 31), three have partial metric-specific checks, and 67 remain pending. No historical categorical judgment has been overwritten. Pending is a workflow state, not a new coding category. Complete means a documented non-blind review, not validated replication or independent agreement; unclear judgments may remain after review.

[Rank 2's full review](reviews/02.json) separates the main seven-model clean-correct cohort, the C&W subset, ensemble/ablation experiments and the competition-defense experiment. Main-cohort filtering must not be silently extended to additional defenses. Its pinned demo code is a candidate artifact, not a verified transfer evaluator; attack-label and default-budget details are recorded for later reconciliation.

[Rank 3's full review](reviews/03.json) includes the appendix and separately retrieved CVF supplement, retaining L2 Tables 9-12 and normal-target Tables 6-8. The overlapping appendix and supplement are counted once. Source checkpoint links respond to HEAD requests, but this does not verify checkpoint contents or a complete target evaluation path. Neither review adds a numerical bound or promotes artifact sufficiency to yes without verification.

The dated [retrospective amendment](../coding_amendment_2026-09-23.md) now specifies scope inventory, mixed-metric aggregation, applicability and completion requirements. It was adopted after inspecting evidence and must not be described as preregistered. [Rank 31's review](reviews/31.json) records all six judgments, source hashes, supplementary clean-accuracy evidence, four distinct metrics and bounds/artifact checks. Its source-success field is explicitly mixed, not missing reporting. Its supplement Table 5 budget and exact count recovery remain unclear. The artifact search does not establish a sufficient original release.

The third batch covers ranks 1 and 6–10 in [batch_01_06_10.md](batch_01_06_10.md). It documents explicit source-success conditioning for LLM jailbreak transfer, distinguishes transfer learning from attack transfer, flags a test/attacker-set population mismatch, and identifies two further bounds candidates requiring population alignment and extraction.

The second batch covers ranks 2–5 in [batch_02_05.md](batch_02_05.md). It confirms explicit clean-correct filtering in rank 2, distinguishes that from almost-correct wording in ranks 4–5, and records the rank-4 paper/code iteration discrepancy without assigning blame or assuming which configuration produced the published table.

- Rank 31, Inkawhich et al. 2019: Section 3 (PDF pp. 2-3) defines joint clean correctness and successful-source denominators for uTR/tTR. Section 5 (p. 4) reports model-specific clean errors, supplemented by all six SVHN models in supplement Table 3. The same paper reports error and targeted success without successful-source filtering. All four definitions are retained in the review.
- Rank 38, Wu et al. 2020: Section 5.1 (pp. 5-6) defines the common 1,000-image dataset and top-1 target accuracy metric. Table 1 contains five clean accuracies and 120 attacked accuracies. Its 96 off-diagonal entries were checked against the cached text. Table 2 and the supplement are not yet fully reviewed.

[Rank 4's full review](reviews/04.json) includes both arXiv appendices, advanced defenses, classic baselines and the iteration ablation. The released evaluator retains source failures and divides by a fixed 1,000; this operational finding is not silently generalized to every published table. Original data/checkpoint contents and paper/code configuration correspondence remain unverified. No numerical bound or verified recomputation was added.

[Rank 5's full review](reviews/05.json) includes arXiv v3 and the separately retrieved CVF supplement, retaining all transformation and hyperparameter ablations. Released notes distinguish conference and arXiv defense targets; preserve that version identity in any future comparison. The public data/model folder listings are accessible despite web-tool failures, but checkpoint bytes and execution are unverified. The numerical L-infinity budget is explicit across reviewed scopes; no aligned clean-accuracy bound was established.

[Rank 6's full review](reviews/06.json) separates fifteen targeted/untargeted result groups, including numerical results in prose and matching-architecture source/target pairs. The paper states an all-seed transfer population, supporting no source-success restriction as reported, not a verified implementation claim. Its target clean accuracies use a disjoint test set, so no bound is extracted. The pinned public code supplies a defense wrapper requiring user-provided models, not a verified bundle for the original transfer experiments.

## Source identification

[Rank 11's full review](reviews/11.json) covers the graph-attack survey and both appendices. Its metric definitions and tables summarize other works, with no original cross-model attack experiment located. The author-linked bibliography is accessible. The paper remains in the corpus with non-applicability reasons, not missing-reporting or artifact-failure judgments.

[Rank 9's full review](reviews/09.json) retains MNIST and malware evasion separately from transferred poisoning. The evasion matrices include useful clean-target reference rows, but population alignment and the malware operating-point mapping remain unresolved. Loss-based transferability, derived ratios and poisoning outcomes are not substituted into the fixed-predictor misclassification identity. The pinned SecML transfer tutorial cites the paper but trains on synthetic blobs; no original-configuration artifact sufficiency or numerical bound is inferred.

[Rank 8's full review](reviews/08.json) covers the 31-page arXiv paper and separate 16-page NeurIPS supplement. Its experiments evaluate transfer learning, not cross-model attack transfer. It stays in the frozen corpus with non-applicability reasons for all six fields, distinct from missing-reporting judgments. The original GitHub URL is unavailable on the review date, but the authors' Hugging Face model collection is accessible. No attack-transfer recomputability failure or bound is inferred. Validation now enforces the amendment's non-applicability rule for all six fields on empty result inventories and requires a documented bounds exclusion.

[Rank 7's full review](reviews/07.json) includes all arXiv appendices and the separately retrieved PMLR supplement. Table 1 reports separate clean errors for all six transfer members, supporting field 1 yes. Figure 3 has eight targeted/untargeted groups; its attack-cohort alignment and conditioning remain unresolved. The numerical epsilon is explicit, but the reported clipping/neighborhood norm is not explicitly identified. The released standard ADP checkpoint was downloaded, hashed and structurally inspected; the iterative evaluator attacks and scores the averaged ensemble, not member-to-member transfer. No numerical bound or verified recomputation is added.

Rank 31 PDF SHA-256: 737c264424564caf7f39b6e9ddc487227cf141f8c6d7511ef0e8e9420d7ffa7d.
Rank 38 PDF SHA-256: fb8dff58f38b94dde6bcf8597a1f239ce3a30b23a640868905a833bf526f46ee.

The cached text includes PDF-page delimiters. These hashes identify the source PDFs. Earlier partial batches used extracted text; the completed rank-31 record also identifies the pages visually checked and the newly retrieved supplement hash.

## Scheme clarification and its limits

The frozen scheme codes a paper, while several rules refer to every surveyed result and field 3 refers to the reported transfer denominator. The dated amendment preserves scope-level judgments and uses unanimous aggregation for fields 2 and 3, with a distinct mixed-explicit reason and an any-explicit-yes indicator. Apply it to all 80, report reason strata, and retain the original scheme/tag. This is a retrospective repair, not evidence that the convention predated observation.

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
suite includes boundary tests, review-schema/aggregation tests and all 27 archived metric checks.

Finish the paper/supplement evidence audit and artifact/bounds decisions, with explicit metric populations and section/table locators. Freeze the audited first pass before a separate blind 16-paper recode. This context has seen first-pass judgments and must not be represented as blind. No valid kappa is available yet.
