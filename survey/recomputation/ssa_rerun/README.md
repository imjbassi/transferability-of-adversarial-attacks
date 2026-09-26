# Manifested SSA rerun (rank 23)

Run date: 25–26 September 2026 (UTC timestamps in each `manifest.json`). Status: **one selected configuration reproduced with the released code; not full-paper replication.** Review: [rank 23](../../evidence_audit/reviews/23.json).

## What was run

- **Release.** [yuyang-long/SSA](https://github.com/yuyang-long/SSA) at `c955cf07c8372bfc4e9f17e647042e027f9f3b1d`, clean checkout. `attack.py` was executed unchanged through [`seeded_attack.py`](seeded_attack.py), which only seeds `random`, NumPy and torch and sets cuDNN to deterministic mode.
- **Attack.** The release defaults: S²I-FGSM, ε = 16/255, 10 iterations, N = 20, ρ = 0.5, σ = 16. The momentum, DI and TI lines are commented out in the release.
- **Source model.** `pretrainedmodels.inceptionv3`, the torchvision Inception-v3 checkpoint `inception_v3_google-1a9a5a14.pth`. Its SHA-256 is recorded, and its prefix matches the filename.
- **Targets.** The nine converted TF-slim models from the [ylhz/tf_to_pytorch_model v1.0 release](https://github.com/ylhz/tf_to_pytorch_model/releases), which the SSA README links. Bytes and SHA-256 for each are in the manifests.
  - These are `.npy` object pickles. They were loaded by [`run.py`](run.py) with a restricted unpickler that admits only numpy dtype/ndarray reconstruction and `_codecs.encode`. The release's `np.load(allow_pickle=True)` was not used.
- **Evaluation.** Equivalent to the release's `verify.py`: `argmax != label + 1` over the 1,000 released images. `run.py` also stores per-example clean and adversarial predictions for the source and every target.
- **Seeds.** Two runs, seed 0 and seed 1, in [`seed0/`](seed0) and [`seed1/`](seed1). Adversarial PNGs are not committed; their SHA-256 digests over `name sha256` lines are in the manifests.
- **Environment.** Windows 11, Python 3.14.2, torch 2.14.0+cu126, RTX 4070.

## Results against Table 1 (Inc-v3 row, S²I-FGSM, PDF p. 10)

| Target | Seed 0 | Seed 1 | Published |
| --- | --- | --- | --- |
| Inc-v3 (paper: white-box *) | 99.7 | 99.7 | 99.7 |
| Inc-v4 | 63.5 | 62.7 | 65.0 |
| IncRes-v2 | 59.4 | 57.6 | 58.9 |
| Res-50 | 56.3 | 56.8 | 56.2 |
| Res-101 | 52.0 | 51.8 | 53.3 |
| Res-152 | 49.1 | 48.9 | 50.3 |
| Inc-v3 ens3 | 31.2 | 31.1 | — (Table 2 defense setting not compared) |
| Inc-v4 ens4 | 31.9 | 32.0 | — |
| IncRes-v2 ens | 17.9 | 17.9 | — |

Seed-to-seed differences reach 1.8 points (IncRes-v2). Every published cell lies within 1.5 points of at least one seed. With two seeds this is a descriptive spread, not a confidence interval.

## Findings relevant to the audit

- **Unconditional metric.** The released metric is unconditional attacked error over all 1,000 images: no clean-correct filter and no source-success filter. Target clean error on these images ranges from 0.0% (IncRes-v2) to 8.3% (Inc-v3 ens4). The per-example files give PTR, CTR, a_st and b_st exactly. For example, seed 0 Inc-v4 has CTR 576/930 = 61.9%, against 63.5% unconditional.
- **The white-box cell uses two checkpoints.** The paper marks Inc-v3 as white-box, but the release attacks the torchvision Inception-v3 and evaluates the converted TF-slim Inception-v3, which is a different checkpoint of the same architecture. The 99.7% cell is therefore strictly a transfer between checkpoints in this release. Which source produced the published row is not established.
- **Consistency with the earlier archive.** The archived historical run (`../ssa_per_example_predictions.csv`) is within about 1 point of both seeds, which is consistent with it having used the same release.

## Reproduce and verify

```text
python survey/recomputation/ssa_rerun/run.py --ssa-root <SSA checkout> --weights-dir <dir with tf2torch_*.npy> \
    --work-dir <new empty dir> --record-dir <output dir> --seed 0 all
python -m pytest -q survey/test_audit_tools.py -k Ssa
```

The test recomputes every metric in both `conditioned_metrics.json` files from the per-example CSVs. It checks arithmetic and manifest identity only. It cannot certify GPU determinism or equivalence to the authors' original environment.

This covers one source (Inc-v3) and one attack (S²I-FGSM). The paper's other sources, S²I-MI-FGSM, the combined attacks and the defense evaluations (HGD, R&P, NIPS-r3, RS, JPEG, NRP) were not run.
