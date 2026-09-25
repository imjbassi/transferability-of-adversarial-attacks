# Publication-readiness work remaining

Status at 25 September 2026, after completing first-pass reviews for all 80 ranks. The manuscript is **not publication-ready**.

## Completed current batch

- Full non-blind evidence reviews for ranks 1 and 38, replacing both partial records.
- Rank 38: a rendered-page re-extraction by the same non-blind auditor reproduces all 96 historical rates and nominal bounds. 24 of them use an ensemble target containing the source, leaving 72 disjoint single-model transfers. Nine further eligible Table 3 cells are recorded in `survey/evidence_audit/reviews/38.json`. Both manuscript versions now state the 72/24 split; the historical CSV/summary are unchanged.
- Earlier: ranks 2-11 and 31, and rank 10's selected original-runtime FGSM rerun archived in `survey/recomputation/su18_original/`.
- Ranks 12-21 reviewed; ranks 13, 16, 20 and 21 flagged as recomputation candidates (`artifact_review: candidate_release_sufficiency_unverified`). Rank 20 (ILA) logs clean and attacked accuracy per batch with released CIFAR-10 checkpoints and is CPU-feasible.
- Ranks 22-26 reviewed; rank 23 (SSA) is the highest-priority field-6 verification: its release was executed historically but needs a manifest with checkpoint hashes.
- Ranks 27-30 and 32 reviewed.
- Ranks 33-37 and 39 reviewed; ranks 34 and 39 flagged as recomputation candidates.
- Ranks 40-45 reviewed; rank 44 flagged as a recomputation candidate for its model-to-model scopes.
- Ranks 46-50 reviewed; ranks 46, 47 and 48 flagged as recomputation candidates (rank 48 has code plus a Zenodo deposit of all trained models).
- Ranks 51-55 reviewed; rank 55 (DEEPSEC) Tables VIII/XVII need cell-by-cell count reconstruction before field 4 can move from unclear.
- Ranks 56-60 reviewed; ranks 57, 58 and 60 flagged as recomputation candidates (rank 58's 5,000-instance selection lists are not released).
- Ranks 61-66 reviewed (ranks 62, 65 and 66 non-applicable with documented reasons).
- Ranks 67-70 reviewed. Rank 68 (DAmageNet) Table 5 supplies a second bounds source: 18 non-source victims with clean and adversarial error on the same 50,000 images (first-pass nominal bounds in `reviews/68.json`; second extraction, rounding and wording check pending).
- Ranks 71-75 reviewed (ranks 71 and 75 non-applicable with documented reasons).
- Ranks 76-80 reviewed (rank 79 non-applicable).
- All 80 first-pass evidence reviews complete and validated; none partial or pending. These are non-blind, same-auditor records; the replacement coding sheet has not yet been exported or frozen. These are workflow counts, not survey findings.

## Required before defensible survey claims

1. **Evidence reviews (done for first pass):** all 80 papers now have documented reviews. Before freezing, a consistency sweep across reviews is still advisable (e.g., the field-3 wording rule applied to ranks 47, 53 and 76 versus 5, 21 and 80). The original task was to review the remaining papers, including supplements, all result scopes, six judgments, evidence locators, applicability, artifact checks and bounds eligibility. Preserve unclear versus explicit no and all positive conditioning evidence. Keep the original corpus/scheme/tag immutable; the September 23 amendment is retrospective.
2. **Export and freeze the repaired first pass:** only after all 80 reviews, generate the replacement coding sheet and stratified results. Distinguish mixed explicit reporting, non-applicable tasks and unresolved evidence. Report whatever the validated corpus shows, including a null result and the recomputability rate.
3. **Obtain genuinely blind reliability data:** draw and archive a reproducible random 16-paper sample, recode without first-pass access, and compute Cohen's kappa per field with counts and uncertainty/limitations. The previous copied recode is invalid. This context has seen the first pass and cannot act as the blind recoder. The author waived waiting, not independence. Any kappa below 0.7 requires a documented tightening pass and full recode under the revised scheme.
4. **Complete qualified-paper recomputation:** verify code, checkpoints, data and evaluators for every field-6 yes paper; execute the required configurations and archive PTR, CTR, a_st, b_st and counts. Existing SI-NI/VMI ports need original-runtime parity and configuration reconciliation; other historical runs need checkpoint/cohort matching. Rank 10 now has an executable selected original-runtime configuration, but historical seed/objective correspondence, other attacks/pairs and full-paper coverage remain unresolved. Do not report unmatched deltas as replication errors.
5. **Finish the corpus-wide bounds assessment:** establish same-model, same-population, unconditional misclassification rates before applying max(0, reported rate - clean error). Rank 38's extraction has a same-auditor visual recheck; a check by a different person is still required. Separate its 24 ensemble-containing-source rows from the 72 single-model rows, add its eligible Table 3 cells, propagate rounding, and report exclusions plus both per-paper and corpus distributions. The current 96 rates come from one paper, not 96 independent studies. Target-label, jailbreak and poisoning outcomes must not be silently substituted into the fixed-predictor error identity.

## Required before submission/release

6. **Finalize manuscript from validated outputs:** replace provisional headline percentages, integrate reliability and recomputability results, incorporate supported recomputations/bounds, and verify the requested section order, roughly two-page CIFAR demonstration, retained conditioning table and appendix moves. Check all main/anonymous versions, references, applicability/selection limitations and language: reporting insufficient to reconstruct CTR, never a claim that a paper is wrong.
7. **Rebuild and inspect final artifacts:** regenerate tables/figures/PDFs, run the full relevant test suite, check every rendered page and cross-reference, and ensure each headline number traces to versioned evidence. Current unit/record checks do not establish scholarly correctness or submission readiness.
8. **Publish a consistent new release:** reconcile and bump the repository's three version-locked files together, build and verify artifact manifests/bundles, tag and push the final release, and verify the new Zenodo archive/DOI and links. Existing concept DOIs and the earlier v1.2.0 archive are not evidence that this repaired survey has been deposited. Do not overwrite preregistration or relabel retrospective decisions as preregistered.
9. **Author submission check:** confirm venue requirements, authorship/contact/disclosures, anonymization, artifact access and final claim approval. Preserve the user-owned untracked anonymous PDF until intentionally rebuilt or replaced.

No new valid kappa, final corpus prevalence, corpus-wide bounds distribution or full-paper replication claim is available at this stopping point.
