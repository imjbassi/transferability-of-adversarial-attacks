# Recomputation notes

## Historical record: claims under evidence review

The narrative below describes the earlier run record and is retained for provenance, not as a current validation claim. The repair audit has not established original-runtime parity, original checkpoint/population identity, or matched published comparators for all archived configurations. In particular, the SI-NI iteration settings differ between the paper and release, and the TensorFlow-to-PyTorch ports have not passed numerical equivalence checks. The historical claim that three papers met the artifact-sufficiency rule is being reassessed across the complete corpus. See [current provenance qualifications](recomputation/PROVENANCE.md), [survey status](README.md), and [evidence reviews](evidence_audit/README.md). Do not cite the historical deltas below as validated replications.

## Earlier narrative (superseded where qualified above)

Three papers met the preregistered artifact-sufficiency rule after the linked
releases were audited. Each repository was checked out at the immutable commit
in `recomputation_ledger.csv`, and all three qualifying releases were rerun on
the authors' 1,000-image evaluation set.

The SSA pipeline was run from its released PyTorch implementation. The two
TensorFlow 1 pipelines were run through an equation-preserving PyTorch adapter
using the authors' linked converted checkpoints and the same attack equations,
budgets, iteration counts, and released evaluation images. The adapters and
metric evaluator are archived in `recomputation/`.

Each aggregate evaluator was extended to retain clean and attacked predictions
for the source and every target. The 27 source--target summaries therefore
contain PTR, CTR, \(a_{st}\), and \(b_{st}\), with an undefined value retained as
blank rather than replaced by zero. Per-example prediction CSVs are archived for
all three runs.

Twenty entries have an aligned comparator in the cited result table. Their
recomputed unconditional attacked-error rates differ from the published rates
by -3.9 to +5.5 percentage points (median -0.65). These differences are
descriptive portability results; they are not characterized as errors.

`artifact_audit.csv` documents two releases that initially appeared plausible
but were coded `unclear` under the preregistered rule after inspection. One did
not supply the full checkpoint set used for the surveyed transfer experiment;
the other did not establish a complete adversarial-transfer evaluation path or
provide per-example transfer outcomes. Neither paper was removed from the
corpus.
