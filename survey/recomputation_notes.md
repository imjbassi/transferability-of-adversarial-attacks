# Recomputation notes

Five papers met the preregistered artifact-availability rule. Each repository was
checked out at the immutable commit in `recomputation_ledger.csv`. The ledger
distinguishes an artifact being available from a complete execution in the
current environment.

One released pipeline was rerun end to end on its 1,000-image evaluation set.
The original aggregate evaluator was extended to retain clean and attacked
predictions for the source and every target. This permits direct calculation of
PTR, CTR, \(a_{st}\), and \(b_{st}\). For the six Table 1 target models, the
recomputed unconditional attacked-error rate differs from the published rate by
-2.0 to +0.7 percentage points. These differences are reported descriptively;
they are not characterized as errors. Exact per-example outputs and all nine
target summaries are in `recomputation/`.

The other four releases require legacy TensorFlow/PyTorch environments, external
model/data bundles, or fresh model-extraction training. Their checkouts and
requirements were verified, but complete executions were not finished for this
release. Accordingly, their metric and delta cells are blank rather than
estimated. For those papers, the available reporting remains insufficient to
reconstruct CTR directly.
