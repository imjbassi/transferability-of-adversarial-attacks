# Manifested PNA+PatchOut rerun (rank 47)

Run date: 26 September 2026 (UTC timestamps in `run1/manifest.json`). Status: **the "Ours" row of Table 1 (ViT → ViT) was reproduced with the released code and clean images. This is not full-paper replication.** Review: [rank 47](../../evidence_audit/reviews/47.json).

## What was run

- **Release.** [zhipeng-wei/PNA-PatchOut](https://github.com/zhipeng-wei/PNA-PatchOut) at `85f23c78284556057422abe395d0e1229a13156a`, clean checkout. `our_attacks.py` (`--attack OurAlgorithm --batch_size 1`, as in the README) and `evaluate.py` were run unchanged in-process by [`run.py`](run.py).
- **Runtime-only adaptations** (all recorded in the manifest):
  - `utils.ROOT_PATH`, which the README tells users to edit, is set at runtime.
  - `glob` results and `AdvDataset.paths` use `/` separators, because `dataset.py` splits paths on `/` and the release assumes POSIX.
  - An empty [`cnns_method`](shim/cnns_method.py) placeholder is importable. The release imports this module but ships only compiled `.pyc` for it; the attack path never uses it, and the bytecode was not executed.
- **Attack.** Release defaults: PNA gradient skip on attention, PatchOut with 130 of 196 patches, L2 term λ = 0.1, ε = 16/255, 10 steps, step ε/10. Patch sampling is seeded by step index, so the attack is deterministic.
- **Surrogates and victims.** Surrogates are ViT-B/16, PiT-B, CaiT-S-24 and Visformer-S. Victims are all eight Table 1 ViTs, evaluated on the released 1,000 `clean_resized_images` and each adversarial set. Per-example predictions come from the release's own prediction CSVs.
- **Cross-check.** All 32 attack-success values match `100 − top1` from the release's `prediction-model_*-top1_*.csv` file names.
- **timm version.** The release pins `timm==0.4.13`, which was never published on PyPI. timm 0.4.12 was used instead. The weight URLs for all eight models are identical in 0.4.12 and 0.5.4, so the development version between them very likely used the same weights.
- **ViT-B/16 weights (ambiguous).** In 0.4.12 onwards, `vit_base_patch16_224` loads the AugReg in21k→in1k weights, while timm ≤ 0.4.9 loads the original JAX weights (`jx_vit_base_p16_224-80ecf9dd`). `model.py`'s unused `CORR_CKPTS` lists `jx_vit_base_p16_224-4ee7a4dc.pth`, but `4ee7a4dc` is the hash of `jx_vit_large_p16_224` in timm, so that list does not identify the base checkpoint. Which ViT-B/16 weights produced Table 1 is therefore not established. The rerun uses the AugReg weights implied by the pinned timm version.
- **Checkpoint loading.** timm 0.4.12 loads `.pth` checkpoints with a full unpickle. Every checkpoint used was checked **after the run** with `torch.load(weights_only=True)`, and all passed. The ViT `.npz` loads with `allow_pickle=False`. Sources: `dl.fbaipublicfiles.com`, GitHub releases and `storage.googleapis.com`, as timm 0.4.12 specifies. SHA-256 hashes of the shared torch-hub cache are in the manifest.
- **Environment.** Isolated venv, Windows 11, Python 3.14.2, torch 2.14.0+cu126, timm 0.4.12, RTX 4070.

## Results against Table 1, row "Ours" (MASR %, mean over surrogates other than the victim)

| Victim | Rerun | Published | Δ |
| --- | --- | --- | --- |
| ViT-B/16 | 46.97 | 46.10 | +0.87 |
| PiT-B | 53.60 | 52.40 | +1.20 |
| CaiT-S-24 | 61.00 | 59.87 | +1.13 |
| Visformer-S | 59.97 | 58.60 | +1.37 |
| DeiT-B | 66.00 | 63.85 | +2.15 |
| TNT-S | 69.80 | 67.25 | +2.55 |
| LeViT-256 | 57.80 | 57.62 | +0.18 |
| ConViT-B | 66.05 | 63.70 | +2.35 |

All eight rerun values are within 2.55 points of the published ones and all are higher. This is a consistent offset, not scatter. Candidate causes (library versions, the ViT-B/16 weight identity, GPU nondeterminism) were not tested, and none is asserted.

## Relevance to the audit

- **Clean-correct data.** All eight victims classify 100% of the released clean images correctly. This matches the paper's statement that the images are "correctly classified by all models" and is consistent with the AugReg ViT-B/16 weights having been used for that selection. So the released unconditional success rate equals the clean-correct-conditioned rate, which fits the frozen review's field-2 `yes` for these groups. `summary.json` reports both.
- **Source-success conditioning.** None: every image counts, whether or not it fooled the surrogate.
- **Not run.** The CNN victims (Table 2, TF-slim and ensemble-adversarial checkpoints), the MI/SGM combinations (Table 3) and the 2,000-image ablations.

## Reproduce and verify

```text
<venv python with timm 0.4.12 and shim/ on its path> survey/recomputation/pna_rerun/run.py \
    --pna-root <checkout> --root <dir with clean_resized_images/ and transformer/image_name_to_class_id_and_name.json> \
    --record-dir <out>
python -m pytest -q survey/test_audit_tools.py -k Pna
```

The test recomputes `run1/summary.json` from the per-example CSV. Adversarial PNGs are not committed; their digests are in the manifest.
