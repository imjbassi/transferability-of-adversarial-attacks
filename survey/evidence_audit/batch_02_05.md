# Metric-level audit batch: ranks 2–5

Audit date: 2026-09-23. Scope: the cached primary-text experimental sections, selected tables and locally available released code. This is not blind recoding. These are scoped evidence decisions, not completed paper-level judgments. Missing linked supplements and full artifact checks remain explicit.

## Rank 2: Improving Transferability of Adversarial Examples With Input Diversity

PDF SHA-256: 9062fb35d0afb05ac292a5be825545d483a79837d4dfadc9c5fba7e0cc925a94.

- Result scope: Section 4.1–4.2, Table 1 (PDF pp. 4–5), seven evaluated models.
- Field 2: **yes for this scope**. Section 4.1 selects 5,000 ImageNet validation images classified correctly by all tested networks. This explicitly excludes target-clean errors, rather than merely saying that the inputs are clean.
- Field 3: **unclear in the reviewed passages**. Section 4.2 says generated attacks are tested on all seven networks, but does not explicitly define a source-success-filtered denominator. A diagonal success rate below 100% alone does not prove how off-diagonal denominators are formed.
- Field 4: **unclear, not an automatic no**. Table 1 prints one-decimal percentages for a 5,000-image cohort. For example, 23.5% is compatible with multiple integer numerators under nearest-tenth rounding. This establishes non-unique reconstruction from that cell, not a paper-wide negative judgment before other records are checked.
- Field 5: **yes for the Table 1 gradient-sign scope**. Section 4.1 specifies a maximum per-pixel perturbation of 15; this must not be silently extended to the separately evaluated C&W results.
- Other scope: Section 4.2 (p. 5) separately evaluates C&W and diverse-input C&W on 1,000 correctly classified images, giving optimizer settings and confidence. The reviewed passage does not establish a numeric L2 radius, so field 5 remains unresolved for that scope.
- Bounds: on the explicitly jointly clean-correct Table 1 cohort, target clean error is zero by selection. No positive pre-existing-error contribution should be asserted. Do not subtract a full-ImageNet clean error from this filtered population.
- Artifact: paper links DI-2-FGSM and TensorFlow model repositories. Links establish candidates, not verified recomputability. No new release sufficiency decision is made.

## Rank 3: Evading Defenses to Transferable Adversarial Examples by Translation-Invariant Attacks

PDF SHA-256: b31f73a1480c8170ddbbe1cd5c771f17a3bbc19516c3b242d8ad777b06899cb3.

- Result scope: Sections 4.1 and 4.3, Table 1 (PDF pp. 5–6).
- Field 2: **unclear**. Section 4.1 specifies the 1,000-image competition dataset, but the inspected setup does not state exclusion of target-clean errors.
- Field 3: **unclear**. Section 4.3 defines success as target misclassification on generated images without an explicit source-success denominator rule.
- Field 4: **unclear pending denominator/aggregation confirmation**. A percentage rounded to one decimal on exactly 1,000 deterministic outcomes can uniquely identify an integer numerator. Therefore percentages plus a known cohort must not automatically be coded no. Randomized defenses and averaging require separate checks.
- Field 5: **yes for the reviewed experiments**. Section 4.1 specifies maximum perturbation 16 on pixel values in [0,255], 10 iterations and step size 1.6.
- Bounds: pending aligned target clean accuracies. Do not borrow clean errors from another paper simply because model names or dataset names match.
- Artifact: repository and model references are candidates; checkpoints, population identity and stochastic-defense handling remain to be checked.

## Rank 4: Nesterov Accelerated Gradient and Scale Invariance for Adversarial Attacks

PDF SHA-256: 7632f7d292cbdfb677f49b050e062a3a73a82a6b82294b81c84b3c103a2dcbdc.

- Result scope: Section 4.1 (PDF p. 6), Section 4.6 / Table 4 (p. 9), and Algorithm 2 (p. 12).
- Field 2: **unclear**. The setup calls the 1,000 images almost correctly classified by all testing models. This is not an exclusion rule. Do not turn almost into all, or infer no without the evaluation denominator.
- Field 3: **unclear**. The inspected descriptions and Table 4 do not establish whether source failures are filtered from transfer denominators.
- Fields 1 and 4: unresolved for the full paper. Near-perfect clean classification is not a numerical per-model clean accuracy, and numerical count recovery depends on the actual denominator.
- Field 5: numerical budget 16 is stated, but attack-configuration reconciliation is required before comparing the archived rerun with Table 4.
- Concrete reconciliation issue: Section 4.1 states 16 iterations and step size 1.6. Algorithm 2 uses alpha = epsilon/T. The released si_ni_fgsm.py at commit 4464fcd55b5f0a109f7c0190819856d449cc01b5 defaults to 10 iterations and computes alpha = epsilon/T. The archived port also used 10. Thus its setting follows that code default, not the paper's stated 16-iteration setup. No assumption is made about which setting generated Table 4.
- Label policy: released code takes a first-iteration model prediction as the attack label. The port also attacks the clean prediction. Evaluation correctness uses ground truth. These are distinct roles and should be recorded separately.
- Bounds: pending aligned numerical clean accuracies and confirmed unconditional denominator.
- Artifact: existing selected run remains a port with unvalidated numerical parity, not a full replication.

## Rank 5: Enhancing the Transferability of Adversarial Attacks through Variance Tuning

PDF SHA-256: 143ba295f909ee64acd6087705adb188ee02a573374e02c519728dff5784aa54.

- Result scope: Sections 4.1–4.2 and Table 1 (PDF p. 5).
- Field 2: **unclear**. The 1,000 clean images are described as almost correctly classified. No explicit target-clean-error exclusion is established by this wording.
- Field 3: **unclear in the reviewed scope**. Section 4.2 defines success as model misclassification on adversarial examples, but does not explicitly state the source-success conditioning population.
- Field 5: **yes for this scope**. Section 4.1 specifies perturbation 16, 10 iterations, step size 1.6, momentum 1, 20 neighborhood samples and beta 1.5.
- Fields 1 and 4: unresolved pending complete clean-accuracy and denominator/aggregation review. One-decimal percentages on 1,000 examples may be recoverable counts, so percentages alone do not establish no.
- Bounds: pending aligned target clean accuracies and denominator confirmation.
- Artifact: released VT code and the existing port are not interchangeable evidence of original-runtime equivalence; the prior selected rerun remains qualified.

## Consequences for the survey

Do not update aggregate counts from this batch. These cases show why the audit needs metric/result scopes, rounding-aware count reconstruction, and explicit treatment of mixed metrics. The historical coding sheet and preregistered scheme remain intact. An artifact status of pending is not a judgment that the paper is insufficiently reported.
