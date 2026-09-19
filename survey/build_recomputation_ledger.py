"""Regenerate the recomputation ledger from archived metric JSON files."""

from __future__ import annotations

import csv
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
FIELDS = [
    "paper_id", "title", "repository", "commit", "target", "status",
    "published_unconditional_percent", "recomputed_unconditional_percent",
    "delta_points", "ptr_percent", "ctr_percent", "a_st_percent",
    "b_st_percent", "evidence", "notes",
]
RUNS = [
    {
        "paper_id": "fb0568dcb546bbb4d7d1ed71ce395f4b66691003",
        "title": "Nesterov Accelerated Gradient and Scale Invariance for Adversarial Attacks",
        "repository": "https://github.com/JHL-HUST/SI-NI-FGSM",
        "commit": "4464fcd55b5f0a109f7c0190819856d449cc01b5",
        "metrics": "si_ni_conditioned_metrics.json",
        "evidence": "Table 4 and survey/recomputation/si_ni_conditioned_metrics.json",
        "notes": "Fresh SI-NI-FGSM run through an equation-preserving PyTorch adapter; authors' linked converted checkpoints; per-example predictions archived.",
    },
    {
        "paper_id": "7301d58eb8a750e44b7da5ab0266b134d1651237",
        "title": "Enhancing the Transferability of Adversarial Attacks through Variance Tuning",
        "repository": "https://github.com/JHL-HUST/VT",
        "commit": "9c87680732108fefa0d3cb5f22d76715c3010a6c",
        "metrics": "vmi_conditioned_metrics.json",
        "evidence": "Table 1 and survey/recomputation/vmi_conditioned_metrics.json",
        "notes": "Fresh VMI-FGSM run through an equation-preserving PyTorch adapter; authors' linked converted checkpoints; per-example predictions archived.",
    },
    {
        "paper_id": "8680c075abfb7832ff1321b5f409f2a5e57570f2",
        "title": "Frequency Domain Model Augmentation for Adversarial Attack",
        "repository": "https://github.com/yuyang-long/SSA",
        "commit": "c955cf07c8372bfc4e9f17e647042e027f9f3b1d",
        "metrics": "ssa_conditioned_metrics.json",
        "evidence": "Table 1 and survey/recomputation/ssa_conditioned_metrics.json",
        "notes": "Fresh 1,000-image S2I-FGSM run; per-example predictions archived.",
    },
]


def cell(value):
    return "" if value is None else value


rows = []
for run in RUNS:
    metrics = json.loads((HERE / "recomputation" / run["metrics"]).read_text())
    for item in metrics:
        rows.append({
            "paper_id": run["paper_id"],
            "title": run["title"],
            "repository": run["repository"],
            "commit": run["commit"],
            "target": item["model"],
            "status": "completed",
            "published_unconditional_percent": cell(item["published_unconditional_percent"]),
            "recomputed_unconditional_percent": item["unconditional_attacked_error_percent"],
            "delta_points": cell(item["delta_vs_published_points"]),
            "ptr_percent": item["ptr_percent"],
            "ctr_percent": item["ctr_percent"],
            "a_st_percent": item["a_st_percent"],
            "b_st_percent": cell(item["b_st_percent"]),
            "evidence": run["evidence"],
            "notes": run["notes"],
        })

with (HERE / "recomputation_ledger.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
