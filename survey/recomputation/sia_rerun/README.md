# Manifested SIA rerun (rank 57)

Run date: 26 September 2026 (UTC timestamps are in `run1/manifest.json`). Status: **Figure 3(a), the ResNet-18 source, was reproduced with the released code at the paper's stated momentum. This is not full-paper replication.** Review: [rank 57](../../evidence_audit/reviews/57.json).

## What was run

- **Release.** [xiaosen-wang/SIT](https://github.com/xiaosen-wang/SIT) at `6d5432d4165a85753c8ae8fdee5cfd3362509a97`, clean checkout. The unchanged `main.py` ran through [`seeded_main.py`](seeded_main.py), which seeds the Python, NumPy and torch RNGs because the release seeds nothing. Both paths were used: the attack, and the `--eval` branch that produces the release's own numbers.
- **Dependency.** `torch-dct` 0.1.6, imported by `attack.py`, is not listed in the README requirements. It is installed in an isolated venv.
- **Data.** The 1,000 Admix images (299 × 299 JPEG) and `val_rs.csv` from the Google Drive folder the README links. The digest and label hash are in the manifest. The folder download hit a Drive quota once and was resumed; all 1,000 images open cleanly.
- **Attack.** SIA from ResNet-18: ε = 16/255, α = 1.6/255, T = 10, N = 20 copies, s = 3 blocks. Two momentum settings were run:
  - **μ = 1** (`--momentum 1.0`), as stated in Section 4.1.
  - **μ = 0**, the release's `main.py` default.
- **Batch size.** The attack batch size was reduced from 64 to 8 because 64 × 20 copies do not fit a 12 GB GPU. Block splits and operations are drawn per batch, so this changes which images share random draws, not the algorithm.
- **Adversarial image format.** The release saves adversarial images under their `.JPEG` names, so PIL writes lossy JPEG. This was kept unchanged.
- **Evaluation.** The eight torchvision models with `weights='DEFAULT'`, as the release uses. For ResNet-101, ResNeXt-50 and MobileNet-v2 these are the IMAGENET1K_V2 weights, which were already the defaults in 2023. Each checkpoint's SHA-256 matches its filename prefix and passes `weights_only` loading. Per-example predictions use the release's own `load_images`/`wrap_model`. For μ = 1 they agree exactly with the release's `--eval` output.
- **Environment.** Windows 11, Python 3.14.2, torch 2.14.0+cu126, torchvision 0.29, RTX 4070.

## Comparator

The paper reports the single-model results only as bar charts. The Figure 3(a) SIA values were read from the PDF's vector bar rectangles against the axis tick lines, so they are exact plotted values, not visual estimates. They come out as clean one-decimal numbers: 100.0, 89.4, 92.1, 92.3, 99.3, 98.4, 65.9 and 84.2.

## Results (attack success % = 1 − top-1 accuracy over all 1,000 images)

| Target | μ = 1 (paper) | μ = 0 (release default) | Figure 3(a) |
| --- | --- | --- | --- |
| ResNet-18 (source) | 100.0 | 100.0 | 100.0 |
| ResNet-101 | 88.9 | 69.5 | 89.4 |
| ResNeXt-50 | 92.7 | 75.9 | 92.3 |
| DenseNet-121 | 99.1 | 96.2 | 99.3 |
| MobileNet-v2 | 98.5 | 93.3 | 98.4 |
| ViT-B/16 | 65.5 | 39.3 | 65.9 |
| Swin-T | 83.7 | 66.7 | 84.2 |
| Inception-v3 | 92.6 | 76.9 | 92.1 |

- **μ = 1.** All eight targets are within 0.5 points of the plotted values.
- **μ = 0.** Results are 3–27 points lower. Reproducing Figure 3 therefore requires the paper's momentum, passed explicitly, rather than the release's CLI default. This is a difference between the release default and the paper, not a defect in the attack code, whose `SIA` class defaults to decay 1.0.

## Relevance to the audit

- **Clean accuracy.** Section 4.1 describes the images as "correctly classified by the adopted models". Under the release's own pipeline (resize to 224, `weights='DEFAULT'`), clean top-1 accuracy on the released images is:

  | Model | Clean accuracy (%) |
  | --- | --- |
  | ResNet-18 | 89.5 |
  | ResNet-101 | 98.2 |
  | ResNeXt-50 | 98.4 |
  | DenseNet-121 | 94.1 |
  | MobileNet-v2 | 92.7 |
  | ViT-B/16 | 97.8 |
  | Swin-T | 98.3 |
  | Inception-v3 | 90.1 |

  So 1.6–10.5% of images per model are already misclassified before attack, and the released success metric counts them as successes.
- **What this does and does not show.** It does not establish how the paper's selection was performed: preprocessing and weights at selection time may have differed. It does show that the released artifacts and evaluator do not reproduce the clean-correct property. `summary.json` gives both unconditional and clean-correct-conditioned rates. The frozen first pass codes field 2 `yes` for this group from the paper's statement; that coding is unchanged, and the observation is logged in [`post_freeze_errata.md`](../../evidence_audit/post_freeze_errata.md).
- **Not run.** The other seven source models, the ensemble settings (Figure 6), the defenses (Figure 7), the SGM/LinBP combinations and the ablations.

## Reproduce and verify

```text
<venv python with torch-dct> survey/recomputation/sia_rerun/run.py --sit-root <checkout> \
    --input-dir <dir with data/ and val_rs.csv> --work-dir <new dir> --record-dir <out> --seed 0
python -m pytest -q survey/test_audit_tools.py -k Sia
```

The test recomputes `run1/summary.json` from the per-example CSV and checks the μ = 1 rates against the release evaluator output recorded in the manifest.
