"""Manifested rerun of the released single-model targeted-transfer script (rank 44, Zhao et al. NeurIPS 2021, arXiv 2012.11207).

Executes the unchanged eval_single.py (a notebook export: ResNet50 source; CE, Po+Trip and
Logit losses with MI/TI/DI; 300 iterations; targeted success counted every 20 iterations on
Inception-v3, DenseNet121 and VGG16-BN) in-process with runpy and reads its result arrays.
Runtime-only adaptations, recorded in the manifest:
  1. numpy.int (removed in NumPy 1.24) is restored as the builtin int;
  2. tqdm.tqdm_notebook is aliased to tqdm.tqdm (the script is a notebook export);
  3. numpy's global RNG is seeded, because the release seeds torch but its DI transform
     draws from numpy's unseeded RNG.

Example:
  python survey/recomputation/tt_rerun/run.py --tt-root D:/transfer_recompute/tt --record-dir survey/recomputation/tt_rerun/seed0 --seed 0
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import platform
import runpy
import subprocess
import sys
from pathlib import Path

PINNED_COMMIT = "2e0b6d0b581a14bc43836f69b04dc431cabcd05f"
ROWS = ["tf_order_inception_v3", "densenet121", "vgg16_bn"]  # rows of the script's pos arrays: model_1, model_3, model_4
TARGET_NAMES = ["inception_v3", "densenet121", "vgg16_bn"]
ATTACKS = {"CE": "pos_res50_ce", "Po+Trip": "pos_res50_trip_po", "Logit": "pos_res50_logit"}
# Table 1 (PDF p. 6), source Res50, targeted success % at 20/100/300 iterations.
PUBLISHED = {
    "CE": {"densenet121": (26.9, 39.4, 42.6), "vgg16_bn": (17.3, 27.3, 30.4), "inception_v3": (2.4, 3.8, 4.1)},
    "Po+Trip": {"densenet121": (26.7, 53.0, 54.7), "vgg16_bn": (18.8, 34.2, 34.4), "inception_v3": (2.9, 6.0, 5.9)},
    "Logit": {"densenet121": (29.3, 63.3, 72.5), "vgg16_bn": (24.0, 55.7, 62.7), "inception_v3": (3.0, 7.2, 9.4)},
}
CHECKPOINTS = {20: 0, 100: 4, 300: 14}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while block := handle.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def summarize(counts, n=1000):
    comparison = []
    for attack, per_target in PUBLISHED.items():
        for target, published in per_target.items():
            row = counts[attack][target]
            for (iters, idx), pub in zip(CHECKPOINTS.items(), published):
                rate = 100 * row[idx] / n
                comparison.append(dict(attack=attack, target=target, iterations=iters, successes=row[idx], images=n,
                                       rerun_percent=round(rate, 4), published_percent=pub, delta=round(rate - pub, 4)))
    return dict(source="resnet50", outcome="targeted success: target-model top-1 == official target label, over all images",
                comparison=comparison)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tt-root", type=Path, required=True)
    parser.add_argument("--record-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    root = args.tt_root.resolve()
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True, check=True).stdout.strip()
    if head != PINNED_COMMIT or dirty:
        raise SystemExit(f"checkout must be clean at {PINNED_COMMIT}")

    import numpy as np
    import torch
    import torchvision
    import tqdm
    if not hasattr(np, "int"):
        np.int = int
    tqdm.tqdm_notebook = tqdm.tqdm
    np.random.seed(args.seed)

    started = dt.datetime.now(dt.timezone.utc).isoformat()
    old_cwd = os.getcwd()
    os.chdir(root)
    try:
        g = runpy.run_path(str(root / "eval_single.py"), run_name="__main__")
    finally:
        os.chdir(old_cwd)
    finished = dt.datetime.now(dt.timezone.utc).isoformat()

    counts = {a: {TARGET_NAMES[r]: [int(x) for x in g[var][r]] for r in range(3)} for a, var in ATTACKS.items()}
    record = args.record_dir
    record.mkdir(parents=True, exist_ok=True)
    with open(record / "success_counts.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["attack", "target"] + [f"iter_{20 * (i + 1)}" for i in range(15)])
        for a in ATTACKS:
            for t in TARGET_NAMES:
                writer.writerow([a, t] + counts[a][t])
    summary = summarize(counts)
    (record / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    images = root / "dataset" / "images"
    names = sorted(p.name for p in images.glob("*.png"))
    hub = Path(torch.hub.get_dir()) / "checkpoints"
    used = ["resnet50-0676ba61.pth", "densenet121-a639ec97.pth", "vgg16_bn-6c64b313.pth", "inception_v3_google-0cc3c7bd.pth"]
    manifest = dict(
        paper="rank 44, arXiv 2012.11207v4", repository="https://github.com/ZhengyuZhao/Targeted-Transfer", commit=head,
        tracked_files_modified=False, script="eval_single.py",
        runtime_adaptations=["numpy.int restored as int", "tqdm.tqdm_notebook aliased to tqdm.tqdm",
                             f"numpy global RNG seeded with {args.seed} (release seeds torch only; DI uses numpy)"],
        release_settings="batch 20, 300 iterations, step 2/255, epsilon 16/255, MI + TI (5x5) + DI (p = 0.7); torch.manual_seed(42) in the script",
        started_utc=started, finished_utc=finished, seed=args.seed,
        images=dict(count=len(names), images_csv_sha256=sha256(root / "dataset" / "images.csv"),
                    digest=hashlib.sha256("".join(f"{n} {sha256(images / n)}\n" for n in names).encode()).hexdigest()),
        torchvision_weights={f: sha256(hub / f) for f in used if (hub / f).exists()},
        environment=dict(python=sys.version.split()[0], platform=platform.platform(), torch=torch.__version__,
                         torchvision=torchvision.__version__, numpy=np.__version__, gpu=torch.cuda.get_device_name(0)))
    (record / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for c in summary["comparison"]:
        print(c["attack"], c["target"], c["iterations"], c["rerun_percent"], c["published_percent"], c["delta"])


if __name__ == "__main__":
    main()
