"""Manifested rerun of the released SIA attack (rank 57, Wang et al. ICCV 2023, "Structure Invariant Transformation").

Stages, each calling the unchanged main.py of the pinned SIT checkout through seeded_main.py:
  attack    main.py --model resnet18 --momentum M   (the release's post-attack loop, which
            re-evaluates the source model for every entry, runs unchanged; its output is ignored)
  evaluate  main.py --eval on the adversarial folder (release numbers, trans.txt), plus
            per-example predictions of the eight torchvision models (weights='DEFAULT') on the
            adversarial and clean images, using the release's own load_images/wrap_model.
The paper states decay mu = 1 (Section 4.1); main.py defaults to --momentum 0. Both are run.
Dependency: torch-dct (imported by attack.py, not listed in the README requirements).

Example:
  D:/transfer_recompute/venv_sia/Scripts/python.exe survey/recomputation/sia_rerun/run.py \
      --sit-root D:/transfer_recompute/sit --input-dir D:/transfer_recompute/sia_input \
      --work-dir D:/transfer_recompute/sia_run --record-dir survey/recomputation/sia_rerun/run1 --seed 0
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PINNED_COMMIT = "6d5432d4165a85753c8ae8fdee5cfd3362509a97"
MODELS = ["resnet18", "resnet101", "resnext50", "densenet121", "mobilenet", "vit", "swin", "inceptionv3"]
# Figure 3(a) (PDF p. 5), SIA bars for the ResNet-18 source, read from the PDF's vector bar
# geometry: value = (y_zero - y_top) / (y_zero - y_hundred) * 100 with y_zero = 149.962,
# y_hundred = 96.330 (axis tick lines). Order on the axis: ResNet-18, ResNet-101, Inception-v3,
# ResNeXt-50, DenseNet-121, MobileNet, ViT, Swin.
FIGURE3A_SIA = {"resnet18": 100.0, "resnet101": 89.40, "inceptionv3": 92.10, "resnext50": 92.30,
                "densenet121": 99.30, "mobilenet": 98.40, "vit": 65.90, "swin": 84.20}
CONFIGS = {"mu1": "1.0", "mu0_release_default": "0.0"}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while block := handle.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def folder_digest(folder):
    names = sorted(os.listdir(folder))
    return len(names), hashlib.sha256("".join(f"{n} {sha256(Path(folder) / n)}\n" for n in names).encode()).hexdigest()


def call_release(args, argv, log):
    cmd = [sys.executable, str(HERE / "seeded_main.py"), str(args.seed), *argv]
    with open(log, "w", encoding="utf-8") as handle:
        subprocess.run(cmd, cwd=args.sit_root, check=True, stdout=handle, stderr=subprocess.STDOUT)


def per_example(args, folders):
    sys.path.insert(0, str(Path(args.sit_root).resolve()))
    import torch
    from utils import load_images, load_labels, model_list, wrap_model  # release helpers
    f2l = load_labels(str(Path(args.input_dir) / "val_rs.csv"))
    preds = {}
    for name in MODELS:
        model = wrap_model(model_list[name](weights="DEFAULT").eval().cuda())
        for key, folder in folders.items():
            with torch.no_grad():
                for filenames, images in load_images(str(folder), 64):
                    out = model(images.cuda()).argmax(dim=1).cpu().tolist()
                    for f, p in zip(filenames, out):
                        preds.setdefault(f, {"image": f, "label": f2l[f] - 1})[f"{name}__{key}"] = p
        del model
        torch.cuda.empty_cache()
    return list(preds.values())


def summarize(path):
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    n = len(rows)
    out = {"images": n, "clean_accuracy_percent": {}, "configs": {}}
    for m in MODELS:
        out["clean_accuracy_percent"][m] = round(100 * sum(int(r[f"{m}__clean"]) == int(r["label"]) for r in rows) / n, 4)
    for cfg in CONFIGS:
        cells = []
        for m in MODELS:
            clean_ok = [int(r[f"{m}__clean"]) == int(r["label"]) for r in rows]
            wrong = [int(r[f"{m}__{cfg}"]) != int(r["label"]) for r in rows]
            e = sum(clean_ok)
            rate = 100 * sum(wrong) / n
            cells.append(dict(target=m, white_box=m == "resnet18", success_percent=round(rate, 4),
                              clean_correct_success_percent=round(100 * sum(w for w, c in zip(wrong, clean_ok) if c) / e, 4) if e else None,
                              figure3a_sia_percent=FIGURE3A_SIA[m], delta=round(rate - FIGURE3A_SIA[m], 4)))
        out["configs"][cfg] = cells
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sit-root", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path, required=True, help="contains data/ (Admix images) and val_rs.csv")
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--record-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--attack-batchsize", type=int, default=8, help="release default 64 x 20 copies does not fit 12 GB")
    args = parser.parse_args()
    root = args.sit_root.resolve()
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True, check=True).stdout.strip()
    if head != PINNED_COMMIT or dirty:
        raise SystemExit(f"SIT checkout must be clean at {PINNED_COMMIT}")
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    record = args.record_dir
    record.mkdir(parents=True, exist_ok=True)
    manifest = dict(paper="rank 57, ICCV 2023 (arXiv 2309.14700)", repository="https://github.com/xiaosen-wang/SIT", commit=head,
                    tracked_files_modified=False, seed=args.seed,
                    runtime_notes=["python/numpy/torch RNGs seeded by seeded_main.py (release seeds nothing)",
                                   "torch-dct installed (imported by attack.py; not in README requirements)",
                                   "release save_images keeps the .JPEG file names, so PIL writes adversarial images as JPEG; kept unchanged",
                                   "attack --batchsize reduced from the release default 64 to fit a 12 GB GPU (20 transformed copies per image); blocks/operations are drawn per batch, so this changes which images share random draws, not the algorithm"],
                    input_images=dict(zip(("count", "digest"), folder_digest(args.input_dir / "data"))),
                    labels_sha256=sha256(args.input_dir / "val_rs.csv"))
    folders = {"clean": (args.input_dir / "data").resolve()}
    for cfg, mu in CONFIGS.items():
        out = work / f"adv_{cfg}"
        if not (out.exists() and len(os.listdir(out)) == 1000):
            started = dt.datetime.now(dt.timezone.utc).isoformat()
            call_release(args, ["--model", "resnet18", "--momentum", mu, "--batchsize", str(args.attack_batchsize), "--input_dir", str(args.input_dir.resolve()) + os.sep,
                                "--output_dir", str(out), "--output_txt", str(work / f"attack_{cfg}.txt")],
                         work / f"attack_{cfg}.log")
            manifest[f"attack_{cfg}"] = dict(started_utc=started, finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                                             release_argv=["--model", "resnet18", "--momentum", mu, "--batchsize", str(args.attack_batchsize)])
        count, digest = folder_digest(out)
        manifest.setdefault(f"attack_{cfg}", {}).update(images=count, adversarial_digest=digest)
        eval_txt = work / f"eval_{cfg}.txt"
        if not eval_txt.exists():
            call_release(args, ["--eval", "--input_dir", str(args.input_dir.resolve()) + os.sep, "--output_dir", str(out),
                                "--output_txt", str(eval_txt)], work / f"eval_{cfg}.log")
        manifest[f"release_eval_{cfg}"] = eval_txt.read_text(encoding="utf-8").strip()
        folders[cfg] = out
    rows = per_example(args, folders)
    columns = ["image", "label"] + [f"{m}__{k}" for m in MODELS for k in folders]
    with open(record / "per_example_predictions.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["image"]))
    summary = summarize(record / "per_example_predictions.csv")
    (record / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    import torch
    import torchvision
    hub = Path(torch.hub.get_dir()) / "checkpoints"
    manifest["torchvision_checkpoints"] = {p.name: sha256(p) for p in sorted(hub.glob("*.pth"))}
    manifest["environment"] = dict(python=sys.version.split()[0], platform=platform.platform(), torch=torch.__version__,
                                   torchvision=torchvision.__version__, gpu=torch.cuda.get_device_name(0))
    (record / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for cfg in CONFIGS:
        print(cfg, [(c["target"], c["success_percent"], c["figure3a_sia_percent"]) for c in summary["configs"][cfg]])


if __name__ == "__main__":
    main()
