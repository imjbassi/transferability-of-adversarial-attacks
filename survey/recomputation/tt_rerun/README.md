# Manifested targeted-transfer rerun (rank 44)

Run date: 26 September 2026 (UTC timestamps are in `seed0/manifest.json`). Status: **Table 1's ResNet-50-source block was reproduced with the released script. This is not full-paper replication.** Review: [rank 44](../../evidence_audit/reviews/44.json).

## What was run

- **Release.** [ZhengyuZhao/Targeted-Transfer](https://github.com/ZhengyuZhao/Targeted-Transfer) at `2e0b6d0b581a14bc43836f69b04dc431cabcd05f`, clean checkout. `eval_single.py` was executed unchanged in-process by [`run.py`](run.py).
  - The script is a notebook export: it prints nothing and leaves its counts in module variables, which `run.py` reads.
- **Runtime-only adaptations**, recorded in the manifest:
  - `numpy.int` is restored as `int`, because NumPy 1.24 removed it.
  - `tqdm.tqdm_notebook` is aliased to `tqdm.tqdm`.
  - NumPy's global RNG is seeded with 0. The script sets `torch.manual_seed(42)` itself, but its DI transform draws from NumPy.
- **Settings (the release's).** ResNet-50 source. Three losses: CE, Po+Trip and Logit, each with MI, TI (5 × 5 kernel) and DI (p = 0.7). Step size 2/255, ε = 16/255, 300 iterations, batch size 20.
- **Targets.** Targeted success is counted every 20 iterations on Inception-v3, DenseNet-121 and VGG16-BN. The release's "VGG16" target is `vgg16_bn`.
- **Data and weights.** The released 1,000 images and `images.csv` with its official target labels; hashes are in the manifest. The torchvision `pretrained=True` weights (IMAGENET1K_V1) come from `download.pytorch.org`. Each SHA-256 matches the hash prefix in its filename, and each file passes `weights_only` loading.
- **Environment.** Windows 11, Python 3.14.2, torch 2.14.0+cu126, torchvision 0.29, NumPy 2.4.2, RTX 4070.

## Results against Table 1 (source Res50; targeted success % at 20/100/300 iterations)

| Loss | →DenseNet-121: rerun / Table 1 | →VGG16 (BN): rerun / Table 1 | →Inception-v3: rerun / Table 1 |
| --- | --- | --- | --- |
| CE | 25.7/37.6/41.3 vs 26.9/39.4/42.6 | 17.4/28.8/30.3 vs 17.3/27.3/30.4 | 2.6/4.2/4.8 vs 2.4/3.8/4.1 |
| Po+Trip | 27.8/52.8/54.8 vs 26.7/53.0/54.7 | 18.5/34.1/34.8 vs 18.8/34.2/34.4 | 3.5/5.7/6.4 vs 2.9/6.0/5.9 |
| Logit | 30.5/64.2/71.3 vs 29.3/63.3/72.5 | 25.1/55.5/62.5 vs 24.0/55.7/62.7 | 2.9/7.6/8.7 vs 3.0/7.2/9.4 |

All 27 cells are within 1.8 points of the published values. The differences have mixed signs, so there is no consistent offset. Only one seed was run, so run-to-run spread from the unseeded DI randomness in the original is not measured here. [`seed0/success_counts.csv`](seed0/success_counts.csv) keeps the count at every 20-iteration checkpoint.

## Relevance to the audit

- **Outcome.** Targeted success (prediction equals the target label) over all 1,000 images. It is neither untargeted misclassification nor error on clean-correct images, which matches the frozen review's "different outcome" treatment.
- **Denominator.** The released script counts over all images, with no clean-correct or source-success filter.
- **Per-example outcomes.** The script records only aggregate counts, so conditioned rates cannot be computed from this rerun without extra instrumentation, which was not added.
- **Not run.** Other sources (DenseNet-121, VGG16, Inception-v3), ensemble and hold-out settings (Table 2), low-ranked targets (Table 3), the Google Cloud Vision results (Table 4, which cannot be regenerated against the 2021 service), the TTP and FDA comparisons (Tables 5–6), and the other evaluation scripts.

## Reproduce and verify

```text
python survey/recomputation/tt_rerun/run.py --tt-root <checkout> --record-dir <out> --seed 0
python -m pytest -q survey/test_audit_tools.py -k Targeted
```

The test recomputes `seed0/summary.json` from `seed0/success_counts.csv`.
