# Scope and label conventions

## Manifested SSA rerun, 2026-09-25

Rank 23 now has a [manifested rerun](ssa_rerun/README.md): the unchanged released attack at the pinned commit, two seeds, hashed source and target checkpoints loaded without arbitrary pickle execution, and per-example predictions. All six published Table 1 cells for the Inc-v3 source (S²I-FGSM) lie within 1.5 points of at least one seed, and the seeds differ by up to 1.8 points. It covers one selected configuration, not full-paper replication. It also shows that the release's source and its 'white-box' target are different Inception-v3 checkpoints.

## Selected original-runtime run, 2026-09-24

Rank 10 now has a separately archived [original TensorFlow 1.8 FGSM rerun](su18_original/README.md), with unchanged released attack/model classes, downloaded checkpoint/data hashes and per-example predictions. This is one selected configuration, not validation of the historical ports below or full-paper replication. Published seed/objective correspondence remains unresolved. Its operational target-clean filtering is a positive finding; no benchmark-clean-error subtraction is warranted on that filtered cohort.

## Configuration reconciliation, 2026-09-23

SI-NI Section 4.1 states 16 iterations and step size 1.6, while released
si_ni_fgsm.py at commit 4464fcd55b5f0a109f7c0190819856d449cc01b5 defaults
to 10 iterations and computes alpha = epsilon / iterations. The archived port
used 10, matching the code default. Which configuration generated the Table 4
comparators has not been established. Do not describe those deltas as a matched
paper-configuration replication. Both code and port attack a predicted label;
ground-truth labels are used separately for evaluation correctness.

Future calls to modern_legacy_attack.py require --steps explicitly. Choose a
new or empty output directory; the adapter rejects nonempty destinations to
preserve archived runs. For example, --steps 10 describes the historical code
default, while --steps 16 with this port's epsilon/steps rule uses a 1-pixel
step and does not silently reproduce the paper's stated 1.6-pixel step. A
16-iteration run alone therefore does not resolve the configuration discrepancy.
No new GPU runs or original-runtime parity tests were performed in this batch.

The pinned SI-NI `simple_eval.py` (lines 138-158) counts ground-truth
misclassification for each loaded adversarial image without source-success
filtering, then divides by the constant 1,000, not the processed-file count.
It does not load clean predictions. This establishes the released evaluator's
operation, not whether the dataset was prefiltered or which evaluator produced
each published table. A faithful run manifest must verify input membership and
count, not merely inherit that denominator. The linked original data and model
downloads were not verified during this audit; web-tool access failures do not
establish that the artifacts are absent. See `../evidence_audit/reviews/04.json`.

These archives support three selected ImageNet attack configurations, each with
one source and nine targets. They do not constitute full replication of every
experiment in the three papers. The SI-NI-FGSM and VMI-FGSM runs use PyTorch
ports of TensorFlow 1 update loops; numerical equivalence of the ports has not
been established against the original runtimes. The common images and converted
target weights were obtained through the SSA checkout. An identical model family
name is not proof that the original studies used identical checkpoint bytes.

## Variance-tuning evidence reconciliation, 2026-09-23

The inspected VT release is pinned to
`9c87680732108fefa0d3cb5f22d76715c3010a6c`; the reviewed paper is arXiv
`2103.15571v3`, not an unspecified interchangeable conference version.
Its `third_party/README.md` explicitly distinguishes the original Table 4
Bit-Red/FD/NRP target choices from the revised arXiv targets. The root README
uses Resnet_101 for ComDefend, while Section 4.1 broadly assigns Inc-v3_ens3
to that defense category. Resolve target identity before a defense comparison;
this does not change the archived basic VMI Table 1 comparison.

The released `vmi_fgsm.py` defaults match the stated 16-pixel radius, 10 steps,
1.6-pixel step size, momentum 1, 20 neighborhood samples and beta 1.5. It fixes
the attack label to the initial source prediction, whereas Algorithm 1 names
a ground-truth label. Matching these hyperparameters alone does not establish
numerical port parity, image identity or post-encoding perturbation compliance.

Like the SI-NI evaluator, VT `simple_eval.py` counts target misclassification
without source-success filtering and divides by a fixed 1,000. Public HTTP
inspection reached the linked data and model folders and found the expected
checkpoint filenames; no checkpoint bytes or runtime were verified. The
randomized-smoothing wrapper references external conversion/evaluation helpers
and a skip parameter, so its population cannot be inferred from the basic
evaluator. See `../evidence_audit/reviews/05.json` for all seven result groups,
source hashes, supplementary coverage and access checks.

## Archived prediction conventions

The raw CSV files are preserved with their original prediction indices:

| Run | Source | CSV label/source indexing | Target indexing |
| --- | --- | --- | --- |
| si_ni | converted TF Inception-v3 | 1-based (background at 0) | 1-based |
| vmi | converted TF Inception-v3 | 1-based (background at 0) | 1-based |
| ssa | pretrainedmodels Inception-v3, 1000 outputs | 0-based | converted TF, 1-based |

For SSA compare target predictions to `label + 1`. Its TF Inception-v3 target is
a different checkpoint/implementation from the source, so it is not a white-box
diagonal despite sharing an architecture name. For the other two runs the
Inception-v3 target is the source and is a white-box control. This distinction
must be preserved in any pooled summary.

`python survey/recomputation/verify_predictions.py` reconstructs every published
JSON count and conditioning rate from the CSVs without a GPU. Empty conditioning
populations produce `null`. This arithmetic check cannot certify the attack
implementation, input-image hashes, perturbation budgets after image encoding,
or equivalence to a paper's original evaluation population. Those require a
complete run manifest and original-runtime comparison before replication claims.

The archived adapters accept `--ssa-root PATH`, where PATH is a checkout of
https://github.com/yuyang-long/SSA at c955cf07c8372bfc4e9f17e647042e027f9f3b1d
with its `dataset/images.csv`, `dataset/images/`, `models/`, `loader.py`,
`Normalize.py`, and `torch_nets/` dependencies populated. Third-party checkpoint
loaders deserialize pickle-backed weights; use only independently verified files.
The archived CSV-to-metric verification requires none of those dependencies.
