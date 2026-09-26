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
