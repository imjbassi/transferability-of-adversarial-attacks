# Retrospective coding clarification, 23 September 2026

Status: adopted for the repair audit, after inspection of the historical coding and several papers. This is **not preregistration** and does not replace `coding_scheme.md` or the `survey-preregistration` tag. Freeze this amendment with the repaired first pass and give it to the independent recoder. Any later change requires another dated amendment and consistent reassessment of all 80 papers.

## Result scope before paper-level coding

Inventory all original empirical cross-model attack evaluations in the main paper and its linked supplement, including baselines, ablations, targeted and untargeted outcomes; do not select only a headline table or results yielding nonzero bounds. Group results only when they share the metric definition, evaluation population and reporting policy. Record figure/table/section locators for every group. Exclude literature summaries and purely white-box results from transfer judgments, while retaining their relevant setup evidence.

Keep every frozen corpus member. Record task applicability separately: cross-model classification attack, other attack outcome, or no original cross-model attack evaluation located. Transfer learning, poisoning and jailbreak outcomes must not silently be interpreted as classification misclassification probabilities. Applicability is metadata, not a seventh categorical answer or permission to remove a corpus member.

## Aggregation

- Fields 1, 4 and 5 retain the frozen requirement covering every surveyed result/model. Use `yes` only with complete affirmative coverage. Use `no` only when an explicit counterexample meets the original negative rule; otherwise use `unclear`. A missing entry or failed search is not an explicit counterexample.
- Fields 2 and 3: retain metric-level `yes` / `no` / `unclear`. At paper level use `yes` only if every in-scope group is yes, `no` only if every group is explicitly no, and `unclear` otherwise. Additionally report `mixed_explicit` when both yes and no are observed; never describe that reason as absent or insufficient reporting. Preserve an `any_explicit_yes` indicator so a paper defining a conditional metric is visible even when it also reports unconditional metrics.
- No in-scope result yields paper-level `unclear`, with reason `not_applicable_to_located_results`, not a vacuous yes. Report this stratum separately from ambiguous reporting.
- Field 6 keeps the frozen existence criterion: an accessible, verifiably sufficient release for at least one identified original transfer configuration supports yes, with coverage recorded. It does not establish full-paper reproducibility. A general training implementation, newly trained substitute weights or an unrelated reimplementation does not establish availability of the paper's trained models. Access failures or unsuccessful searches yield unclear. Record access date, URL, version/hash where available and the exact inspected components. Full recomputation remains a separate task for every yes paper.

## Interpretation safeguards

For field 2 preserve the original allowance for correctly-classified-images wording, but separately record which models the wording covers. Source-only filtering is not evidence that target-clean errors were excluded. A formal denominator definition can establish a reporting judgment without proving the implementation followed it; flag unresolved setup/definition tensions separately.

For field 4 distinguish literal count reporting from unique count reconstruction. The latter can qualify under the original equivalent-count rule only with a known denominator, known aggregation policy and documented rounding assumption yielding one integer numerator. Do not multiply an averaged percentage by a dataset size or assume that a nominal dataset size survived filtering. Keep both modes visible in the audit.

For field 5 distinguish a numerical input-space radius from optimizer steps, confidence, a feature-space loss norm or a measured perturbation norm. An unconstrained/non-norm attack is no only when explicit; missing details are unclear. State pixel scaling when found.

Bounds require a fixed target/checkpoint, the same population and denominator for clean and attacked outcomes, and an attacked misclassification probability without source-success conditioning on that population. Clean-correct cohorts have zero baseline error by construction. Do not subtract full-test clean error from a filtered or different test subset. Target-label success is not interchangeable with untargeted misclassification. Record excluded and unresolved groups, not only eligible ones. Aggregate across papers as well as rates so prolific tables do not dominate a corpus claim.

## Completion and reporting

`complete` in the evidence ledger means the available main paper and linked supplement were reviewed, all result groups and six field judgments have locators/rationales, and bounded artifact and bounds checks are recorded. It does **not** mean every answer is known, artifacts execute, bounds are extractable, or the study is independently validated. A missing supplement remains partial. A validator checks record structure, not scholarly correctness.

Keep the historical CSV untouched during repair. Store dated replacement judgments in `evidence_audit/reviews/`; only export a replacement sheet after all 80 reviews are complete. Report mixed, non-applicable and unresolved reasons separately. Never equate `unclear` with a paper being wrong, and do not compute a new corpus headline from a partial audit.
