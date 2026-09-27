"""Manifested rerun of the released RAP attack (rank 67, Qin et al. NeurIPS 2022).

Runs the unchanged rap_attack.py (via shimmed_rap.py, which only restores numpy.int) for
Table 1's untargeted CE setting from ResNet-50: the I-FGSM baseline (--transpoint 400),
+RAP (--transpoint 0 --adv_perturbation) and +RAP-LS (--transpoint 100 --adv_perturbation).

Release facts recorded in the manifest:
- RAP is only active with --adv_perturbation; the README's RAP/RAP-LS example commands omit it.
- --source_model accepts 'resnet50' (the README writes resnet_50).
- logging() writes to arg.file_path, which exists only with --save, so --save is required;
  it also saves the 400-iteration adversarial tensor (~1 GB), hashed and kept outside Git.
- Data paths are hard-coded to /targeted_attack/dataset/; on Windows this resolves on the
  current drive, so D:/targeted_attack/dataset is a junction to the Targeted-Transfer
  release's dataset (the same 1,000 NIPS 2017 images and official labels).

Example:
  python survey/recomputation/rap_rerun/run.py --rap-root D:/transfer_recompute/rap \
      --dataset D:/transfer_recompute/tt/dataset --record-dir survey/recomputation/rap_rerun/run1
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PINNED_COMMIT = "2112d8892136f8009392076e2193bb4031cc9b97"
BASE = ["--source_model", "resnet50", "--loss_function", "CE", "--max_iterations", "400", "--seed", "9018", "--save"]
# Section 4.1: "we set KLS as 100 and alpha_n as 2/255. We set eps_n as 12/255 for I and TI in untargeted
# attack and 16/255 for other attacks". The release defaults are eps_n 16/255 and 8 steps (alpha_n 2/255),
# i.e. the setting for the other attacks. The paper's I-row setting is eps_n 12/255 with 6 steps.
PAPER_I = ["--adv_epsilon", "12/255", "--adv_steps", "6"]
CONFIGS = {
    "I": ["--transpoint", "400"],
    "I+RAP": ["--transpoint", "0", "--adv_perturbation", *PAPER_I],
    "I+RAP-LS": ["--transpoint", "100", "--adv_perturbation", *PAPER_I],
    "I+RAP_eps16_release_default": ["--transpoint", "0", "--adv_perturbation"],
    "I+RAP-LS_eps16_release_default": ["--transpoint", "100", "--adv_perturbation"],
}
PAPER_CONFIG = {"I": "I", "I+RAP": "I+RAP", "I+RAP-LS": "I+RAP-LS",
                "I+RAP_eps16_release_default": "I+RAP", "I+RAP-LS_eps16_release_default": "I+RAP-LS"}
# pos rows in the script: model_1 Inception-v3, model_2 ResNet-50 (source), model_3 DenseNet-121, model_4 VGG16-BN
ROWS = ["inception_v3", "resnet50", "densenet121", "vgg16_bn"]
# Table 1 (PDF p. 7), untargeted CE, ResNet-50 => Dense-121 / VGG-16 / Inc-v3, row "I / +RAP / +RAP-LS".
PUBLISHED = {"densenet121": {"I": 79.2, "I+RAP": 91.5, "I+RAP-LS": 91.9},
             "vgg16_bn": {"I": 78.0, "I+RAP": 91.1, "I+RAP-LS": 92.9},
             "inception_v3": {"I": 34.6, "I+RAP": 57.0, "I+RAP-LS": 57.2}}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while block := handle.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def exp_name(cfg):
    """Directory the release writes to (its name ignores eps_n, so runs are moved to <label> afterwards)."""
    return "resnet50_CE_" + CONFIGS[cfg][1]


def summarize(counts, n=1000):
    rows = []
    for target, pub in PUBLISHED.items():
        for cfg in CONFIGS:
            if cfg not in counts:
                continue
            c = counts[cfg][target][39]
            rows.append(dict(target=target, config=cfg, paper_setting=cfg in ("I", "I+RAP", "I+RAP-LS"),
                             iterations=400, successes=c, images=n, rerun_percent=round(100 * c / n, 4),
                             published_percent=pub[PAPER_CONFIG[cfg]], delta=round(100 * c / n - pub[PAPER_CONFIG[cfg]], 4)))
    return dict(source="resnet50", outcome="untargeted: target top-1 != true label over all 1,000 images", comparison=rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rap-root", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--record-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.rap_root.resolve()
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True, check=True).stdout.strip()
    if head != PINNED_COMMIT or dirty:
        raise SystemExit(f"RAP checkout must be clean at {PINNED_COMMIT}")
    drive_root = Path(os.path.splitdrive(str(Path.cwd()))[0] + "/targeted_attack")
    if not (drive_root / "dataset" / "images.csv").exists():
        raise SystemExit(f"{drive_root}/dataset must point at the Targeted-Transfer dataset (junction)")
    import numpy as np
    record = args.record_dir
    record.mkdir(parents=True, exist_ok=True)
    manifest_path = record / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest.update(paper="rank 67, NeurIPS 2022", repository="https://github.com/SCLBD/Transfer_attack_RAP", commit=head,
                    tracked_files_modified=False,
                    release_notes=["RAP requires --adv_perturbation; README RAP/RAP-LS examples omit it",
                                   "--source_model choice is 'resnet50' (README: resnet_50)",
                                   "--save required because logging writes to arg.file_path",
                                   "numpy.int restored (shimmed_rap.py)",
                                   "hard-coded /targeted_attack/dataset resolved via a junction to the Targeted-Transfer dataset"],
                    dataset=dict(images_csv_sha256=sha256(args.dataset / "images.csv")))
    counts = {}
    for cfg, extra in CONFIGS.items():
        out_dir = drive_root / "adv_example" / cfg
        result = out_dir / "results.npy"
        if not result.exists():
            release_dir = drive_root / "adv_example" / exp_name(cfg)
            if release_dir.exists():
                raise SystemExit(f"{release_dir} exists; move it to its configuration label first")
            started = dt.datetime.now(dt.timezone.utc).isoformat()
            cmd = [sys.executable, str(HERE / "shimmed_rap.py"), str(root / "rap_attack.py"), *BASE, *extra]
            with open(record / f"stdout_{cfg}.log", "w", encoding="utf-8") as log:
                subprocess.run(cmd, cwd=str(drive_root), check=True, stdout=log, stderr=subprocess.STDOUT)
            release_dir.rename(out_dir)
            manifest[f"run_{cfg}"] = dict(started_utc=started, finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                                          argv=[*BASE, *extra])
        pos = np.load(result)
        counts[cfg] = {ROWS[r]: [int(x) for x in pos[r]] for r in range(4)}
        adv = out_dir / "iter_400.npy"
        manifest.setdefault(f"run_{cfg}", {}).update(results_npy_sha256=sha256(result),
                                                     iter_400_npy_sha256=sha256(adv) if adv.exists() else None)
        (record / f"log_{cfg}.txt").write_text((out_dir / "log.txt").read_text(encoding="utf-8"), encoding="utf-8")
        (record / "counts.json").write_text(json.dumps(counts, indent=1) + "\n", encoding="utf-8")
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    summary = summarize(counts)
    (record / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    import torch
    import torchvision
    hub = Path(torch.hub.get_dir()) / "checkpoints"
    used = ["resnet50-0676ba61.pth", "densenet121-a639ec97.pth", "vgg16_bn-6c64b313.pth", "inception_v3_google-0cc3c7bd.pth"]
    manifest["torchvision_weights"] = {f: sha256(hub / f) for f in used if (hub / f).exists()}
    manifest["environment"] = dict(python=sys.version.split()[0], platform=platform.platform(), torch=torch.__version__,
                                   torchvision=torchvision.__version__, numpy=np.__version__, gpu=torch.cuda.get_device_name(0))
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for r in summary["comparison"]:
        print(r["target"], r["config"], r["rerun_percent"], r["published_percent"], r["delta"])


if __name__ == "__main__":
    main()
