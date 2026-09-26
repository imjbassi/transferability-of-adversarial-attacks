# Recomputation feasibility for field-6 candidates

Assessed 25–26 September 2026 on the available machine: Windows 11, an RTX 4070 (Ada, 12 GB), Python 3.14 and torch 2.14. Local storage for weights and data is under `D:\transfer_recompute` and is not in Git.

"Feasible" means the released code can be run here without accounts, terms acceptance or undisclosed data. It says nothing about whether the paper's results are correct. "Blocked" is about practical access, not a judgment on the release.

| Rank | Release | Status | Reason |
| --- | --- | --- | --- |
| 23 SSA | PyTorch | **Run**: `ssa_rerun/` | One configuration, two seeds. |
| 20 ILA | PyTorch, CIFAR-10 | **Run**: `ila_rerun/` | I-FGSM done; MI-FGSM in progress. |
| 13 SGM | PyTorch + advertorch | **Running**: `sgm_rerun/` | Four configurations; Inception targets proxied by converted TF-slim weights. |
| 57 SIA | PyTorch, torchvision | Feasible | Images from the Admix Drive folder; `weights='DEFAULT'` may differ from 2023 weights. |
| 47 | PyTorch, timm | Feasible | Clean images released; correspondence of timm weights to 2021 unverified. |
| 44 | PyTorch, torchvision | Feasible for model-to-model scopes | Table 4 commercial-API outcomes cannot be regenerated. |
| 10 | TF 1.8 | Run earlier (`su18_original/`) | CPU-only legacy runtime. |
| 16 FIA | TF 1.12 + Keras | Not feasible here | TF1 GPU builds need CUDA 9/10 and cannot drive an Ada GPU. The CPU estimate is about 17 h for one 1,000-image configuration (ens = 30). |
| 46 Ghost | TF1 | Not feasible here | Same TF1/GPU limit; SharePoint-hosted data and checkpoints also unverified. |
| 48 | TF 1.4/1.14 + Keras | Not feasible here | Pathology code is a single-image demo, not the published table pipeline. Radiology needs ChestX-Ray14 (about 42 GB) and TF 1.14. Ophthalmology uses Kaggle data that needs an account and terms acceptance. |
| 60 | TF-slim | Not feasible here | TF1. |
| 39 | PyTorch | Blocked on data | Evaluation lists refer to ImageNet validation images, which need an account and terms acceptance. |
| 58 | PyTorch | Blocked on data | The 5,000-instance selection lists are not released, so the evaluated sample cannot be reconstructed. |
| 34 | PyTorch, face recognition | Not attempted yet | LFW pairs must be recreated by the user; no per-comparison outcomes are released. |

Where a release fails only because of a runtime limit on this machine, that is not evidence against the release's sufficiency. Field 6 stays `unclear` for those papers.
