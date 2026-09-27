# Recomputation feasibility for field-6 candidates

Assessed 25–26 September 2026 on the available machine: Windows 11, an RTX 4070 (Ada, 12 GB), Python 3.14 and torch 2.14. Local storage for weights and data is under `D:\transfer_recompute` and is not in Git.

"Feasible" means the released code can be run here without accounts, terms acceptance or undisclosed data. It says nothing about whether the paper's results are correct. "Blocked" is about practical access, not a judgment on the release.

| Rank | Release | Status | Reason |
| --- | --- | --- | --- |
| 23 SSA | PyTorch | **Run**: `ssa_rerun/` | One configuration, two seeds. |
| 20 ILA | PyTorch, CIFAR-10 | **Run**: `ila_rerun/` | I-FGSM and MI-FGSM. |
| 13 SGM | PyTorch + advertorch | **Run**: `sgm_rerun/` | Four configurations; Inception targets proxied by converted TF-slim weights. |
| 57 SIA | PyTorch, torchvision | **Run**: `sia_rerun/` | Images from the Admix Drive folder; `weights='DEFAULT'` may differ from 2023 weights. |
| 67 RAP | PyTorch, torchvision | **Run**: `rap_rerun/` | Table 1 ResNet-50 I/+RAP/+RAP-LS; about 10 h per RAP configuration on this GPU. |
| 32 Patch-wise | TF1 (plus a PyTorch variant) | No comparable configuration here | The TF release needs TF1; the PyTorch variant evaluates torchvision ResNet-152, ResNeXt-50 and DenseNet-169 rather than the paper's TF-slim targets. |
| 4 SI-NI, 5 VMI, 21 Admix | TF1 | Not feasible here | TF1 GPU limit (earlier PyTorch ports of 4 and 5 exist in this archive). |
| 24, 69, 72, 73, 77, 78 | various | Not attempted | 24: Table 2 not packaged and the adaptive attack needs 128 GB RAM; 69: Bard target not recomputable; 72, 73, 77: checkpoints or trained models not released (training from scratch would not match published numbers); 78: evaluated ImageNet validation images need an account and terms acceptance. |
| 68 DAmageNet | Keras | Not feasible here | The clean baseline needs ImageNet validation images (account and terms); Keras victims would run on CPU only. |
| 47 PNA | PyTorch, timm | **Run**: `pna_rerun/` | Table 1 ViT to ViT; the pinned timm 0.4.13 was never published (0.4.12 used); ViT-B/16 weight identity ambiguous; CNN victims (TF-slim) not run. |
| 44 | PyTorch, torchvision | **Run**: `tt_rerun/` | Table 1 ResNet-50 block; Table 4 commercial-API outcomes cannot be regenerated. |
| 10 | TF 1.8 | Run earlier (`su18_original/`) | CPU-only legacy runtime. |
| 16 FIA | TF 1.12 + Keras | Not feasible here | TF1 GPU builds need CUDA 9/10 and cannot drive an Ada GPU. The CPU estimate is about 17 h for one 1,000-image configuration (ens = 30). |
| 46 Ghost | TF1 | Not feasible here | Same TF1/GPU limit; SharePoint-hosted data and checkpoints also unverified. |
| 48 | TF 1.4/1.14 + Keras | Not feasible here | Pathology code is a single-image demo, not the published table pipeline. Radiology needs ChestX-Ray14 (about 42 GB) and TF 1.14. Ophthalmology uses Kaggle data that needs an account and terms acceptance. |
| 60 | TF-slim | Not feasible here | TF1. |
| 39 | PyTorch | Blocked on data | Evaluation lists refer to ImageNet validation images, which need an account and terms acceptance. |
| 58 | PyTorch | Blocked on data | The 5,000-instance selection lists are not released, so the evaluated sample cannot be reconstructed. |
| 34 | PyTorch, face recognition | Not attempted yet | LFW pairs must be recreated by the user; no per-comparison outcomes are released. |

Where a release fails only because of a runtime limit on this machine, that is not evidence against the release's sufficiency. Field 6 stays `unclear` for those papers.
