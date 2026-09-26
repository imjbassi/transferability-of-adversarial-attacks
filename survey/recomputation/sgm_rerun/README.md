# Manifested SGM rerun (rank 13)

Run date: 26 September 2026 (UTC timestamps are in `run1/manifest.json`). Status: **Table 3 of the paper was reproduced with the released code on the released data, for two sources and two attacks. This is not full-paper replication.** Review: [rank 13](../../evidence_audit/reviews/13.json). A correction to that review's step-size description is recorded in [`post_freeze_errata.md`](../../evidence_audit/post_freeze_errata.md).

## What was run

- **Release.** [csdongxian/skip-connections-matter](https://github.com/csdongxian/skip-connections-matter) at `9b2e5cca9b673efcac253e16b2f55f6cda1a8692`, clean checkout. `attack_sgm.py` ran unchanged through [`shimmed_attack.py`](shimmed_attack.py) in an isolated venv.
  - The venv holds advertorch 0.2.2, the version the release README names. It also holds [`shim/zero_gradients_shim.py`](shim/zero_gradients_shim.py), loaded through a one-line `.pth`. This shim restores `torch.autograd.gradcheck.zero_gradients`, which modern torch removed and which advertorch imports at package load. `LinfPGDAttack` never calls it.
- **Data.** The released 5,000-image `SubImageNet224` from the README's Google Drive link. The zip SHA-256 and the digest of the extracted images are in the manifest. Labels come from the release's `imagenet_class_to_idx.npy`, which was first inspected with a restricted unpickler ([`safe_npy.py`](safe_npy.py)).
- **Configurations.** These follow Section 4.1: 10 steps, α = 2/255 (the release default), ε = 16/255, no random start, so the attack is deterministic.

  | Name | Source | γ |
  | --- | --- | --- |
  | `rn152_pgd` | ResNet-152 | 1.0 (plain PGD) |
  | `rn152_sgm` | ResNet-152 | 0.2 |
  | `dn201_pgd` | DenseNet-201 | 1.0 (plain PGD) |
  | `dn201_sgm` | DenseNet-201 | 0.5 |

  The README's example commands swap these source labels; the γ values used here follow the paper.
- **Evaluation.** [`run.py`](run.py) stores per-example top-1 predictions on the clean images and all four adversarial sets for each target.
  - The `pretrainedmodels` targets use the release's `evaluate.py` preprocessing.
  - Two cells were cross-checked with the release's own `evaluate.py` and matched exactly: `rn152_sgm` on VGG19-BN gives accuracy 19.32 = 100 − 80.68, and `dn201_pgd` on SENet-154 gives 60.06 = 100 − 39.94. The only change was one `.view(-1)` to `.reshape(-1)`, in a copy outside the checkout, because modern torch rejects the original on a non-contiguous tensor.
- **Inception targets (proxy).** The paper uses TF-slim checkpoints for the Inception targets. Here they are the ylhz PyTorch conversions of those slim checkpoints, the same files as in [`../ssa_rerun`](../ssa_rerun), loaded without arbitrary unpickling. This is a proxy, not the original runtime.
- **Weights.** Sources and integrity checks are in [`WEIGHT_SOURCES.md`](WEIGHT_SOURCES.md). DenseNet-201 and SENet-154 came from Internet Archive captures because the original mirror's certificate has expired. Every checkpoint passes `weights_only` loading except the legacy-format ResNet-152 from `download.pytorch.org`.
- **Environment.** Windows 11, Python 3.14.2, torch 2.14.0+cu126, advertorch 0.2.2, RTX 4070.

## Results against Table 3 (success % = 1 − top-1 accuracy over all 5,000 images; published means over 5 runs)

| Source / attack | VGG19-BN | VGG19 (plain) | Table 3 "VGG19" | RN152 | DN201 | SE154 | IncV3* | IncV4* | IncResV2* |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RN152 PGD | 45.68 | 39.34 | 45.03 | 99.98 / 99.91 | 51.74 / 51.49 | 29.86 / 29.35 | 25.42 / 26.56 | 21.02 / 21.03 | 18.82 / 19.10 |
| RN152 SGM | 80.68 | 77.68 | 79.90 | 99.98 / 99.87 | 82.24 / 81.56 | 62.68 / 61.83 | 56.30 / 57.22 | 49.30 / 48.57 | 45.96 / 45.44 |
| DN201 PGD | 57.66 | 48.84 | 57.61 | 59.66 / 59.84 | 99.94 / 99.89 | 39.94 / 39.78 | 35.60 / 36.01 | 31.46 / 31.76 | 26.46 / 25.92 |
| DN201 SGM | 82.86 | 75.00 | 82.66 | 86.68 / 86.65 | 99.84 / 99.67 | 72.54 / 72.03 | 65.70 / 65.48 | 59.08 / 58.77 | 55.62 / 54.97 |

Cells show rerun / published. `*` marks the converted TF-slim proxy targets.

- **Non-VGG cells.** All 24 are within 1.14 points of the published means, including the proxy Inception targets.
- **VGG19 column.** The paper's "VGG19" column agrees with torchvision's VGG19 with batch normalisation (`vgg19_bn`) to within 0.78 points. It disagrees with plain `vgg19` by 2.2–8.8 points, and the release README evaluates `vgg19_bn`. The column therefore most likely reports VGG19-BN. That is an inference from agreement, not stated in the paper.

## Relevance to the audit

- **Clean-correct data.** Four of the five `pretrainedmodels` targets (VGG19-BN, ResNet-152, DenseNet-201 and SENet-154) classify 100% of the released clean images correctly. Plain VGG19 gets 98.8%, and the converted Inception proxies get 99.76–99.80%. Section 3.3 describes the 5,000 images as correctly classified by all source models. So for the 100% targets the released data already contains only clean-correct images, and the unconditional success rate equals the clean-correct-conditioned rate. For the others the two rates differ slightly; `summary.json` reports both.
- **Source-success conditioning.** None is applied; the evaluator counts all 5,000 images. The per-example file gives exact counts for any other conditioning.

## Reproduce and verify

```text
<venv python> survey/recomputation/sgm_rerun/run.py --sgm-root <checkout> --data <SubImageNet224> \
    --work-dir <new dir> --tf-weights <dir with tf2torch_*.npy> --ssa-root <SSA checkout> --record-dir <out> all
python -m pytest -q survey/test_audit_tools.py -k Sgm
```

The test recomputes `run1/summary.json` from the per-example CSV. Adversarial PNGs are not committed; their digests are in the manifest.

Not run:
- the one-step FGSM results (Table 2), MI/DI/TI and their combinations, and the γ sweeps;
- the other six source models (Table 1, Figure 2);
- the ensemble attacks and the secured targets (Table 5).
