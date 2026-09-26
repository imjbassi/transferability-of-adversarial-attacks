# Manifested ILA rerun (rank 20)

Run date: 26 September 2026 (UTC timestamps are in each `manifest.json`). Status: **two selected CIFAR-10 configurations reproduced with the released code and checkpoints. This is not full-paper replication.** Review: [rank 20](../../evidence_audit/reviews/20.json).

## What was run

- **Release.** [CUVL/Intermediate-Level-Attack](https://github.com/CUVL/Intermediate-Level-Attack) at `25271f84f74a9ee02b9ba0e707cc02680ab236dd`, clean checkout. `all_in_one_cifar10.py` and its configuration ran unchanged through [`run.py`](run.py), with three runtime-only adaptations recorded in each manifest:
  - checkpoint paths, which were hard-coded to the authors' cluster, are pointed at the downloaded files;
  - a concat shim restores `pandas.DataFrame.append`, which pandas 2 removed;
  - stubs that raise replace `scipy.misc.imread/imresize/imsave`. Only the ImageNet `DI_2_fgsm_tf` path uses these functions; the CIFAR-10 path never calls them.
- **Checkpoints.** The four CIFAR-10 models from the Google Drive folder linked in the release README. Their file names embed test accuracy (`resnet18_epoch_347_acc_94.77.pth` and so on), and their SHA-256 hashes are in the manifests. All four load as plain state dicts with `weights_only=True`.
- **Data.** The CIFAR-10 test batch via torchvision. The archive MD5 is `c58f30108f718f92721af3b95e74349a`, as torchvision expects, and the test batch SHA-256 is in the manifests. The runs used 100 batches of 100, which covers all 10,000 test images in order.
- **Configurations.** ResNet18 source, all four models as targets. Two attacks: I-FGSM (Table 4) and MI-FGSM (Table 2), each as a 20-iteration baseline plus ILAP at every layer index.
  - Released hyperparameters: learning rate 0.002, ε = 0.03 on the release's [-1, 1] input scale, which equals the paper's ε = 0.015 on [0, 1]. ILAP uses learning rate 0.006. MI-FGSM momentum decay is 0.9 in the release config; the paper does not state this value.
- **Environment.** Windows 11, Python 3.14.2, torch 2.14, RTX 4070.

## Results (accuracy after attack %, all 10,000 test images)

The clean accuracies logged by the release on the same images are 94.77 (ResNet18), 94.59 (SENet18), 95.61 (DenseNet121) and 94.86 (GoogLeNet). They equal the checkpoint file names, and they round to the Section 4 values.

| Target | I-FGSM 20 itr: rerun / Table 4 | ILAP l=4: rerun / Table 4 | MI-FGSM 20 itr: rerun / Table 2 | ILAP l=4: rerun / Table 2 |
| --- | --- | --- | --- | --- |
| ResNet18 (source) | 3.27 / 3.3 | 7.65 / 7.6 | 4.87 / 5.7 | 10.54 / 11.3 |
| SENet18 | 44.27 / 44.4 | 27.46 / 27.5 | 33.05 / 33.8 | 29.74 / 30.6 |
| DenseNet121 | 46.01 / 45.8 | 27.83 / 27.7 | 34.55 / 35.1 | 29.84 / 30.4 |
| GoogLeNet | 58.79 / 58.6 | 36.12 / 35.8 | 44.66 / 45.1 | 37.34 / 37.7 |

- **I-FGSM.** All eight cells are within 0.32 points of Table 4. The target-selected "Opt ILAP" entries are also reproduced at the stated layers; for example, ResNet18 at l = 5 gives 1.86 against the published 1.8 (5).
- **MI-FGSM.** All eight cells are within 0.86 points of Table 2. However, every rerun value is 0.36–0.86 points below the published one. That is a consistent offset, not scatter. Its cause is not established: momentum decay, library versions and GPU nondeterminism are all possible, and none was tested. It is described here, not attributed.

## Relevance to the audit

- **Released metric.** The release logs `acc_after_attack` and `original_acc` per batch for the same images and the same fixed model. It uses no source-success or clean-correct filtering. This matches the frozen review's explicit `no` codes for fields 2 and 3 in the `cifar10_full_test_transfer` group.
- **Bounds population.** Clean and attacked accuracies share the full 10,000-image test set here. That supports the population match assumed by `../../rank20_bounds.py` for the I-FGSM and MI-FGSM columns. It does not test the FGSM, DeepFool, TAP or C&W columns; the C&W lattice anomaly remains unexplained.
- **Per-example outcomes.** The release outputs batch aggregates only. PTR, CTR and b_st therefore cannot be computed from these outputs without additional instrumentation, which was not added.

## Reproduce and verify

```text
python survey/recomputation/ila_rerun/run.py --ila-root <checkout> --weights-dir <checkpoints> \
    --work-dir <new dir containing data/cifar-10-python.tar.gz> --attack ifgsm --num-batches 100 --batch-size 100
python survey/recomputation/ila_rerun/summarize.py <work dir> --attack ifgsm --output <work dir>/summary.json
python -m pytest -q survey/test_audit_tools.py -k Ila
```

The test checks that each archived `release_output.csv` matches its manifest hash byte for byte, which is why the file is stored with `-text` in `.gitattributes`. It also checks that each `summary.json` is exactly reproducible from it.

Not run: the other sources, FGSM, DeepFool, C&W, TAP, ILAF, the ε and learning-rate ablations, and the ImageNet experiments.
