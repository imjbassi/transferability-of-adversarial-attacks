# Selected original-runtime rerun: Su et al.

Run date: 24 September 2026. Status: **selected configuration, not a matched published-table replication**. Review: [rank 10](../../evidence_audit/reviews/10.json).

The unchanged attack and model classes from release commit `353ef696f594631f3577e94c01882c67e19aa3df` were instrumented by [the probe](../su18_original_probe.py). Source Inception-v1, target Inception-v2, untargeted FGSM, unit-pixel L-infinity epsilon 0.1, seed 1216, 1,000 selected images. Both models use 224-pixel inputs and 1,001 outputs, avoiding padding and label-offset adaptations. The original `use_zvalue` branch ascends the negative true-class logit. Serial loading replaces multiprocessing; attack and predictor implementations are unchanged.

## Recorded results

The source-clean filter retains 692 inputs; 645 are also target-clean correct. All reported PTR/CTR quantities below use that joint-clean cohort, not the full ImageNet validation set.

| Quantity | Exact counts | Rate |
| --- | --- | --- |
| PTR | 345 / 645 | 0.5348837209 |
| CTR | 334 / 539 | 0.6196660482 |
| a_st | 539 / 645 | 0.8356589147 |
| b_st | 11 / 106 | 0.1037735849 |

The identity holds: 345 = 334 + 11, and PTR = a_st CTR + (1-a_st) b_st. Maximum measured L-infinity distortion is 0.10000000149 (float32 tolerance).

Figure 3, top-left panel, source Inception-v1 / target Inception-v2 prints **0.36**. The selected rerun's PTR differs by **+17.4884 percentage points**. This is a descriptive, unmatched-configuration difference, not a replication-error estimate: the release README uses seed 1215 while the generation CLI defaults to 1216, the published seed is unidentified, and correspondence between the paper's training-loss description and the release's logit-objective branch is unresolved. The displayed comparator is rounded. Do not choose a seed/objective to fit the printed value or interpret the difference as a claim that the paper is wrong.

The released transfer evaluator explicitly skips target-clean mistakes before increasing its denominator, a positive conditioning finding. Benchmark clean errors in Table 1 must not be subtracted from this clean-correct cohort. The newly generated records are not original published counts.

## Reproduce and verify

Use an isolated legacy environment, not a network service. Executed on Windows CPU with Python 3.6.8, TensorFlow 1.8.0, NumPy 1.16.6, SciPy 1.2.3, Pillow 5.4.1 and protobuf 3.6.1. Other installed dependencies: pandas 0.24.2, h5py 2.10.0, absl-py 0.15.0, astor 0.8.1, gast 0.2.2, termcolor 1.1.0, grpcio 1.48.2, tensorboard 1.8.0, Werkzeug 0.16.1, Markdown 3.1.1, bleach 1.5.0, html5lib 0.9999999, six 1.17.0, python-dateutil 2.9.0.post0, pytz 2026.4. Python's official 3.6.8 Windows embeddable archive SHA-256: `efadf25a090c8438b3cbe27574fb36bd40c80e20a03939188a1d5051685495dd`.

Clone [the release](https://github.com/huanzhang12/Adversarial_Survey) at the pinned commit. Extract the [model archive](https://download.huan-zhang.com/models/adv/imagenet/frozen_imagenet_models_v1.1.tar.gz) under `tmp/imagenet/` and [image archive](https://download.huan-zhang.com/datasets/adv/img.tar.gz) under `imagenetdata/` as documented upstream. Archive SHA-256 values, respectively:

- `493533fb8c4ed957e5ea575833310e61512a177571fb352692dc4992dec891a7`
- `217c3776db6d53ffca5b232703def0c38221a899d7f1205b4eb5730c7d3a983e`

From the release checkout, invoke the legacy interpreter with:

```text
python /path/to/survey/recomputation/su18_original_probe.py --release . --output /new/output/directory --seed 1216 --epsilon 0.1 --images 1000
```

`manifest.json` and `predictions.jsonl` are copied byte-for-byte from the completed run. They preserve source/checkpoint/harness hashes, the 1,000 selected IDs, skipped inputs, and all 692 per-example prediction records before target-clean filtering. Model/data archives are not duplicated in Git. Source accuracy in the metrics summary is 100% by selection, not benchmark accuracy. Verify with a modern Python from the repository root:

```text
python survey/recomputation/test_su18_original.py
```

This single run does not cover the other model pairs, budgets, targeted attacks, I-FGSM, EAD or C&W. Full-paper recomputation and published-configuration reconciliation remain outstanding.
