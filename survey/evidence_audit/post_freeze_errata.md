# Post-freeze errata to the repaired first pass

The repaired first pass is frozen (`freeze_manifest.json`, tag `repaired-first-pass-2026-09-25`).
Frozen review files are not edited. Errors found afterwards are listed here with dates; any
that would change a coded value require a dated amendment and a new freeze before counts are
reported. None listed so far changes a coded value.

## 25 September 2026

### Rank 13 (SGM): released step size misdescribed

- **Frozen text.** The f6 evidence and the artifact check describe the released step size as "epsilon/steps (1.6 for 10 steps)", which "differs from the stated alpha = 2".
- **Correction.** At pinned commit `9b2e5cca9b673efcac253e16b2f55f6cda1a8692`, both `attack_sgm.py` and `attack_iter.py` define `--step-size` with default `2`. They use `step_size = args.step_size / 255.0`, and fall back to `epsilon / num_steps` only when a negative step size is passed. So the released default is 2/255, which matches the paper's stated alpha = 2.
- **Effect.** f6 remains `unclear` (candidate, sufficiency unverified); the reason and value are unchanged. The README's swapped source-architecture labels (the text says "ResNet-152 as the source" above `--arch densenet201`) remain as recorded.

## 26 September 2026

### Rank 57 (SIA): rerun observation on the clean-correct image set (observation, no coding change)

- **Frozen coding.** Group `normal_model_transfer` has field 2 = `yes`, based on Section 4.1's statement that the 1,000 images "are correctly classified by the adopted models". That coding records what the paper reports and is unchanged.
- **Rerun observation** (`survey/recomputation/sia_rerun/`). With the released image set, the release's evaluator (resize to 224) and torchvision `weights='DEFAULT'`, clean top-1 accuracy is 89.5–98.4% across the eight models. So 1.6–10.5% of images per model are misclassified before attack and count as successes in the released metric.
- **Interpretation.** The paper's selection may have used different preprocessing or weights; this is not established. The observation shows only that the released artifacts do not reproduce the clean-correct property. It should be reported alongside the field-2 coding, not in place of it.
- **Momentum default.** The paper states decay μ = 1, but `main.py` defaults to `--momentum 0`. Figure 3(a) is reproduced within 0.5 points only with μ = 1.
