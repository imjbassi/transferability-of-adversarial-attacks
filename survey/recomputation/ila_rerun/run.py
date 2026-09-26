"""Manifested rerun of the released ILA CIFAR-10 pipeline (rank 20, Huang et al., arXiv 1907.10823v3).

Runs the unchanged all_in_one_cifar10.py from a clean checkout at the pinned
commit, with two runtime-only adaptations recorded in the manifest:
  1. cifar10_config.model_configs checkpoint paths (hard-coded to the authors'
     cluster) are pointed at the downloaded checkpoints;
  2. pandas.DataFrame.append (removed in pandas 2) is restored as a concat shim;
  3. scipy.misc.imread/imresize/imsave (removed from SciPy) are stubs that raise;
     they are used only by the ImageNet DI_2_fgsm_tf path, never on CIFAR-10.
Checkpoints are torch state dicts; torch>=2.6 loads them with weights_only=True.

Example:
  python survey/recomputation/ila_rerun/run.py --ila-root D:/transfer_recompute/ila \
      --weights-dir D:/transfer_recompute/ila_weights --work-dir D:/transfer_recompute/ila_run_ifgsm \
      --attack ifgsm --num-batches 100 --batch-size 100
then: python survey/recomputation/ila_rerun/summarize.py ...
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
import runpy
import subprocess
import sys
from pathlib import Path

PINNED_COMMIT = "25271f84f74a9ee02b9ba0e707cc02680ab236dd"
CHECKPOINTS = {"ResNet18": "resnet18_epoch_347_acc_94.77.pth", "DenseNet121": "densenet121_epoch_315_acc_95.61.pth",
               "GoogLeNet": "googlenet_epoch_227_acc_94.86.pth", "SENet18": "senet18_epoch_279_acc_94.59.pth"}
CHECKPOINT_SOURCE = "https://drive.google.com/drive/folders/1RGtlPCc2vTqeQc5utOgLb1Y3_vIO5JVi (linked from the release README)"


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while block := handle.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ila-root", type=Path, required=True)
    parser.add_argument("--weights-dir", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--attack", required=True)
    parser.add_argument("--source", default="ResNet18")
    parser.add_argument("--num-batches", type=int, required=True)
    parser.add_argument("--batch-size", type=int, required=True)
    args = parser.parse_args()

    root = args.ila_root.resolve()
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True, check=True).stdout.strip()
    if head != PINNED_COMMIT or dirty:
        raise SystemExit(f"ILA checkout must be clean at {PINNED_COMMIT}")
    work = args.work_dir.resolve()
    out_csv = work / "release_output.csv"
    if out_csv.exists():
        raise SystemExit(f"{out_csv} exists; choose a new work dir")
    work.mkdir(parents=True, exist_ok=True)

    import os
    import pandas as pd
    import torch

    if not hasattr(pd.DataFrame, "append"):
        def _append(self, row, ignore_index=True):
            return pd.concat([self, pd.DataFrame([row])], ignore_index=ignore_index)
        pd.DataFrame.append = _append

    import scipy.misc
    for _name in ("imread", "imresize", "imsave"):
        if not hasattr(scipy.misc, _name):
            def _stub(*a, _n=_name, **k):
                raise RuntimeError(f"scipy.misc.{_n} stub called")
            setattr(scipy.misc, _name, _stub)

    sys.path.insert(0, str(root))
    os.chdir(work)  # release downloads CIFAR-10 to ./data and writes out_name relative to cwd
    import cifar10_config
    for name, filename in CHECKPOINTS.items():
        cls, _ = cifar10_config.model_configs[name]
        cifar10_config.model_configs[name] = (cls, str(args.weights_dir.resolve() / filename))

    started = dt.datetime.now(dt.timezone.utc).isoformat()
    sys.argv = ["all_in_one_cifar10.py", "--source_models", args.source, "--transfer_models", "ResNet18", "DenseNet121",
                "GoogLeNet", "SENet18", "--attacks", args.attack, "--num_batches", str(args.num_batches),
                "--batch_size", str(args.batch_size), "--out_name", str(out_csv)]
    runpy.run_path(str(root / "all_in_one_cifar10.py"), run_name="__main__")

    test_batch = work / "data" / "cifar-10-batches-py" / "test_batch"
    manifest = dict(
        paper="rank 20, arXiv 1907.10823v3", repository="https://github.com/CUVL/Intermediate-Level-Attack",
        commit=head, tracked_files_modified=False,
        runtime_adaptations=["model_configs checkpoint paths redirected", "pandas DataFrame.append concat shim", "scipy.misc imread/imresize/imsave raising stubs (ImageNet-only path)"],
        command=["python", "survey/recomputation/ila_rerun/run.py", "--attack", args.attack, "--source", args.source,
                 "--num-batches", str(args.num_batches), "--batch-size", str(args.batch_size)],
        release_argv=sys.argv[1:-1] + ["<work-dir>/release_output.csv"],
        started_utc=started, finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        images_evaluated=args.num_batches * args.batch_size,
        checkpoints={n: dict(file=f, source=CHECKPOINT_SOURCE, sha256=sha256(args.weights_dir / f)) for n, f in CHECKPOINTS.items()},
        cifar10_test_batch_sha256=sha256(test_batch) if test_batch.exists() else None,
        release_output_sha256=sha256(out_csv),
        determinism_note="No seed is set by the release; I-FGSM and ILA are deterministic given inputs, GPU kernels may not be",
        environment=dict(python=sys.version.split()[0], platform=platform.platform(), torch=torch.__version__,
                         cuda=torch.version.cuda, gpu=torch.cuda.get_device_name(0), pandas=pd.__version__),
    )
    (work / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
