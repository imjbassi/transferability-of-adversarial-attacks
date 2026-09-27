# Manifested RAP rerun (rank 67)

Run dates: 26–27 September 2026 (UTC timestamps are in `run1/manifest.json`). Status: **the ResNet-50 "I / +RAP / +RAP-LS" cells of Table 1 (untargeted, CE) were reproduced with the released code at the paper's stated settings. This is not full-paper replication.** Review: [rank 67](../../evidence_audit/reviews/67.json).

## What was run

- **Release.** [SCLBD/Transfer_attack_RAP](https://github.com/SCLBD/Transfer_attack_RAP) at `2112d8892136f8009392076e2193bb4031cc9b97`, clean checkout. The unchanged `rap_attack.py` ran through [`shimmed_rap.py`](shimmed_rap.py), which only restores `numpy.int`.
- **Seed.** The script seeds torch and NumPy itself; `--seed 9018` is the README's value.
- **Data.** The script hard-codes `/targeted_attack/dataset/`. On Windows that resolves on the current drive, so `D:\targeted_attack\dataset` is a junction to the Targeted-Transfer release's dataset. That is the same 1,000 NIPS 2017 images and `images.csv`, and its hash is in the manifest.
- **Weights.** torchvision `pretrained=True` (IMAGENET1K_V1). The same four hash-verified, `weights_only`-checked checkpoints as [`../tt_rerun`](../tt_rerun) were used.
- **Settings (Section 4.1).** CE loss, ε = 16/255, α = 2/255, K = 400, batch 50.
  - K_LS = 100 for RAP-LS.
  - α_n = 2/255.
  - ε_n = 12/255 for I (and TI) in untargeted attacks, which gives 6 inner steps: `--adv_epsilon 12/255 --adv_steps 6`.
- **Environment.** Windows 11, Python 3.14.2, torch 2.14.0+cu126, torchvision 0.29, RTX 4070. The +RAP runs took about 10 hours each.

## Release facts recorded

- **RAP flag.** RAP is only active with `--adv_perturbation`. The README's "RAP" and "RAP-LS" example commands omit that flag, so run as written they execute the baseline.
- **Inner-loop defaults.** The release defaults are ε_n = 16/255 with 8 steps. That is the paper's setting for attacks other than I and TI, not for this row.
- **Output folder.** The output directory name omits ε_n, so runs that differ only in ε_n overwrite each other. `run.py` moves each run to a folder named after its configuration.
- **Required flags.** `--save` is required, because `logging()` writes into a path that only `--save` creates. `--source_model` takes `resnet50`, not the README's `resnet_50`.

## Results (untargeted success % at K = 400, all 1,000 images; ResNet-50 source)

| Configuration | →DenseNet-121 | →VGG16 (BN) | →Inception-v3 |
| --- | --- | --- | --- |
| I (rerun / Table 1) | 77.1 / 79.2 | 78.1 / 78.0 | 35.6 / 34.6 |
| +RAP, paper ε_n = 12/255 | 92.2 / 91.5 | 92.2 / 91.1 | 56.9 / 57.0 |
| +RAP-LS, paper ε_n = 12/255 | 92.7 / 91.9 | 92.6 / 92.9 | 58.2 / 57.2 |
| +RAP, release default ε_n = 16/255 | 81.4 | 80.5 | 46.2 |
| +RAP-LS, release default ε_n = 16/255 | 79.0 | 79.1 | 45.5 |

- **Paper settings.** All nine cells are within 2.1 points of Table 1, and the RAP cells are within 1.1.
- **Release defaults.** With ε_n = 16/255 and 8 steps, +RAP and +RAP-LS are 10–14 points lower, and RAP-LS is slightly below RAP. The published gains depend strongly on this inner-loop setting, and the release default is not the setting the paper states for this row.
- **Scope.** This is one seed; run-to-run spread is not measured.

## Relevance to the audit

- **Denominator.** Success counts target top-1 ≠ true label over all 1,000 images, with no clean-correct or source-success filter.
- **Per-example outcomes.** The script records only counts, every 10 iterations (`run1/counts.json`), so conditioned rates cannot be computed without further instrumentation.
- **Not run.** Other sources and baselines (MI, TI, DI, SI, Admix), the targeted attacks, the defenses and the Google Cloud Vision experiment.

## Reproduce and verify

```text
# from the drive holding targeted_attack/dataset (a junction to the Targeted-Transfer dataset)
python survey/recomputation/rap_rerun/run.py --rap-root <checkout> --dataset <Targeted-Transfer dataset> --record-dir <out>
python -m pytest -q survey/test_audit_tools.py -k Rap
```

Each configuration's full log is archived as `run1/log_<config>.txt`. The saved 400-iteration adversarial tensors (about 1 GB each) are kept outside Git, and their hashes are in the manifest.
