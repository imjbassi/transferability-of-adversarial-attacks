"""Manifested rerun of the released SGM code (rank 13, Wu et al. ICLR 2020, arXiv 2002.05990).

attack    runs the unchanged attack_sgm.py (cwd = pinned checkout) for each configuration.
          advertorch 0.2.x imports torch.autograd.gradcheck.zero_gradients, which modern
          torch removed; shim/zero_gradients_shim.py (installed in the isolated venv with a
          one-line .pth) restores the original helper in every process (PGD/MI never call it).
evaluate  per-example top-1 predictions on clean and adversarial images for each target.
          pretrainedmodels targets use the release evaluate.py preprocessing
          (pretrainedmodels.utils.TransformImage, scale 1.0, preserve aspect ratio).
          The paper's Inception targets are TF-slim checkpoints; here they are proxied by
          the ylhz PyTorch conversions of those slim checkpoints (1,001 outputs, label + 1),
          resized 224 -> 299 bilinearly. This proxy is recorded as such.

Example:
  D:/transfer_recompute/venv_sgm/Scripts/python.exe survey/recomputation/sgm_rerun/run.py \
      --sgm-root D:/transfer_recompute/sgm --data D:/transfer_recompute/sgm_data/extract/SubImageNet224 \
      --work-dir D:/transfer_recompute/sgm_run --tf-weights D:/transfer_recompute/ssa_models \
      --ssa-root D:/transfer_recompute/ssa all
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PINNED_COMMIT = "9b2e5cca9b673efcac253e16b2f55f6cda1a8692"
# name: (arch, gamma); gamma 1.0 disables SGM hooks -> plain 10-step PGD (Section 4.1: alpha=2, eps=16, 10 steps;
# SGM gamma 0.2 on ResNet and 0.5 on DenseNet sources).
CONFIGS = {"rn152_pgd": ("resnet152", 1.0), "rn152_sgm": ("resnet152", 0.2),
           "dn201_pgd": ("densenet201", 1.0), "dn201_sgm": ("densenet201", 0.5)}
PM_TARGETS = ["vgg19", "vgg19_bn", "resnet152", "densenet201", "senet154"]
TF_TARGETS = {"tf_inception_v3": "tf2torch_inception_v3.npy", "tf_inception_v4": "tf2torch_inception_v4.npy",
              "tf_inc_res_v2": "tf2torch_inc_res_v2.npy"}
# Table 3 (PDF p. 6), success rate %, mean over 5 runs. Keys: config -> target.
PUBLISHED = {
    "rn152_pgd": {"vgg19": 45.03, "resnet152": 99.91, "densenet201": 51.49, "senet154": 29.35,
                  "tf_inception_v3": 26.56, "tf_inception_v4": 21.03, "tf_inc_res_v2": 19.10},
    "rn152_sgm": {"vgg19": 79.90, "resnet152": 99.87, "densenet201": 81.56, "senet154": 61.83,
                  "tf_inception_v3": 57.22, "tf_inception_v4": 48.57, "tf_inc_res_v2": 45.44},
    "dn201_pgd": {"vgg19": 57.61, "resnet152": 59.84, "densenet201": 99.89, "senet154": 39.78,
                  "tf_inception_v3": 36.01, "tf_inception_v4": 31.76, "tf_inc_res_v2": 25.92},
    "dn201_sgm": {"vgg19": 82.66, "resnet152": 86.65, "densenet201": 99.67, "senet154": 72.03,
                  "tf_inception_v3": 65.48, "tf_inception_v4": 58.77, "tf_inc_res_v2": 54.97},
}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while block := handle.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def folder_digest(folder):
    names = sorted(p.name for p in Path(folder).iterdir() if p.suffix == ".png")
    lines = "".join(f"{n} {sha256(Path(folder) / n)}\n" for n in names)
    return len(names), hashlib.sha256(lines.encode()).hexdigest()


def update_manifest(work, key, value):
    path = Path(work) / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    manifest[key] = value
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def checkout(root):
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True, check=True).stdout.strip()
    if head != PINNED_COMMIT or dirty:
        raise SystemExit(f"SGM checkout must be clean at {PINNED_COMMIT}")
    return dict(repository="https://github.com/csdongxian/skip-connections-matter", commit=head,
                attack_sgm_py_sha256=sha256(Path(root) / "attack_sgm.py"),
                class_to_idx_sha256=sha256(Path(root) / "imagenet_class_to_idx.npy"))


def run_attack(args):
    for name, (arch, gamma) in CONFIGS.items():
        out = Path(args.work_dir) / f"adv_{name}"
        if out.exists() and any(out.iterdir()):
            print("skip existing", name)
            continue
        out.mkdir(parents=True, exist_ok=True)
        argv = ["--gamma", str(gamma), "--output_dir", str(out), "--arch", arch, "--batch-size", "40",
                "--input_dir", str(args.data)]
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        subprocess.run([sys.executable, str(HERE / "shimmed_attack.py"), *argv], cwd=args.sgm_root, check=True)
        count, digest = folder_digest(out)
        update_manifest(args.work_dir, f"attack_{name}", dict(
            release_argv=argv[:3] + ["<work-dir>/adv_" + name] + argv[4:7] + ["<data>"], started_utc=started,
            finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(), images=count, adversarial_digest=digest,
            defaults_used="epsilon 16, num-steps 10, step-size 2 (/255), momentum 0, rand_init False (deterministic)"))


def run_evaluate(args):
    import numpy as np
    import torch
    import torch.nn.functional as F
    import pretrainedmodels
    import pretrainedmodels.utils
    from PIL import Image
    sys.path.insert(0, str(HERE.parent))
    sys.path.insert(0, str(Path(args.ssa_root).resolve()))
    from ssa_rerun.run import safe_load_weights
    import importlib

    device = torch.device("cuda")
    sys.path.insert(0, str(HERE))
    from safe_npy import load_class_to_idx
    class_to_idx = load_class_to_idx(Path(args.sgm_root) / "imagenet_class_to_idx.npy")
    names = sorted(p.name for p in Path(args.data).iterdir() if p.suffix == ".png")
    labels = [class_to_idx[n.split("_")[0]] for n in names]
    folders = {"clean": (Path(args.data), names)}
    for cfg in CONFIGS:
        folders[cfg] = (Path(args.work_dir) / f"adv_{cfg}", [n + ".png" for n in names])

    def batches(folder, files, transform, size=50):
        for i in range(0, len(files), size):
            yield torch.stack([transform(Image.open(folder / f).convert("RGB")) for f in files[i:i + size]])

    preds = {}
    for target in PM_TARGETS + list(TF_TARGETS):
        if target in PM_TARGETS:
            model = pretrainedmodels.__dict__[target](num_classes=1000, pretrained="imagenet").eval().to(device)
            transform = pretrainedmodels.utils.TransformImage(model, scale=1.0, preserve_aspect_ratio=True)
            offset = 0
        else:
            module = importlib.import_module(f"torch_nets.{target}")
            module.load_weights = safe_load_weights
            net = module.KitModel(str(Path(args.tf_weights) / TF_TARGETS[target])).eval().to(device)
            from torchvision import transforms as T
            base = T.Compose([T.Resize(299), T.ToTensor()])
            transform = base
            model = torch.nn.Sequential(_TfNorm(), net).eval()
            offset = 1
        for key, (folder, files) in folders.items():
            out = []
            with torch.no_grad():
                for x in batches(folder, files, transform):
                    y = model(x.to(device))
                    y = y[0] if isinstance(y, (tuple, list)) else y
                    out += (y.argmax(1) - offset).cpu().tolist()
            preds[(target, key)] = out
        del model
        torch.cuda.empty_cache()
        print(target, "done", flush=True)

    record = Path(args.record_dir)
    record.mkdir(parents=True, exist_ok=True)
    columns = ["image", "label"] + [f"{t}__{k}" for t in PM_TARGETS + list(TF_TARGETS) for k in folders]
    with (record / "per_example_predictions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        for i, (n, y) in enumerate(zip(names, labels)):
            writer.writerow([n, y] + [preds[(t, k)][i] for t in PM_TARGETS + list(TF_TARGETS) for k in folders])
    summary = summarize_rows(record / "per_example_predictions.csv")
    (record / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    manifest = json.loads((Path(args.work_dir) / "manifest.json").read_text(encoding="utf-8"))
    hub = Path(torch.hub.get_dir()) / "checkpoints"
    manifest["evaluate"] = dict(
        finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(), images=len(names),
        data_zip_sha256=args.data_zip_sha256, clean_digest=folder_digest(args.data)[1],
        pretrainedmodels_checkpoints={p.name: sha256(p) for p in sorted(hub.glob("*.pth"))},
        tf_proxy_weights={t: dict(file=f, sha256=sha256(Path(args.tf_weights) / f)) for t, f in TF_TARGETS.items()},
        environment=dict(python=sys.version.split()[0], platform=platform.platform(), torch=torch.__version__,
                         gpu=torch.cuda.get_device_name(0), numpy=np.__version__, advertorch=_advertorch_version()),
        checkout=checkout(args.sgm_root))
    (record / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["comparison"], indent=1))


class _TfNorm:
    """[0,1] -> [-1,1], as TfNormalize('tensorflow') in the SSA release."""
    def __new__(cls):
        import torch

        class M(torch.nn.Module):
            def forward(self, x):
                return x * 2.0 - 1.0
        return M()


def _advertorch_version():
    try:
        import importlib.metadata as md
        return md.version("advertorch")
    except Exception:
        return None


def summarize_rows(path):
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    targets = sorted({c.split("__")[0] for c in rows[0] if "__" in c})
    comparison = []
    for cfg, (arch, _) in CONFIGS.items():
        for t in targets:
            y = [int(r["label"]) for r in rows]
            clean = [int(r[f"{t}__clean"]) for r in rows]
            adv = [int(r[f"{t}__{cfg}"]) for r in rows]
            n = len(rows)
            clean_ok = [c == l for c, l in zip(clean, y)]
            wrong = [a != l for a, l in zip(adv, y)]
            e = sum(clean_ok)
            pub = PUBLISHED[cfg].get(t)
            rate = 100 * sum(wrong) / n
            comparison.append(dict(
                config=cfg, source=arch, target=t, white_box=(t == arch), images=n,
                target_clean_accuracy_percent=round(100 * e / n, 4),
                unconditional_success_percent=round(rate, 4),
                target_clean_correct_success_percent=round(100 * sum(w for w, c in zip(wrong, clean_ok) if c) / e, 4) if e else None,
                wrong_count=sum(wrong), target_clean_correct_count=e,
                published_percent=pub, delta_points=None if pub is None else round(rate - pub, 4)))
    return dict(note="success = top-1 != label over all 5,000 released images (release evaluate.py convention: 1 - accuracy); "
                     "tf_* targets are PyTorch conversions of the TF-slim checkpoints, a proxy for the paper's TF targets",
                comparison=comparison)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sgm-root", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--tf-weights", type=Path, required=True)
    parser.add_argument("--ssa-root", type=Path, required=True)
    parser.add_argument("--record-dir", type=Path, default=HERE)
    parser.add_argument("--data-zip-sha256", default="d3352e6b038b118ed4dd9bbd36d68b0d2fcdb20055cf973a85aa6b2cd8446e4a")
    parser.add_argument("stage", choices=["attack", "evaluate", "all"])
    args = parser.parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    update_manifest(args.work_dir, "checkout", checkout(args.sgm_root))
    if args.stage in ("attack", "all"):
        run_attack(args)
    if args.stage in ("evaluate", "all"):
        run_evaluate(args)


if __name__ == "__main__":
    main()
