"""Manifested rerun of the released PNA+PatchOut attack (rank 47, Wei et al. AAAI 2022, arXiv 2109.04176).

Runs the unchanged our_attacks.py (OurAlgorithm = PNA + PatchOut + L2 term, release
defaults) from each of the four Table 1 surrogates and the unchanged evaluate.py for all
eight ViT victims, in-process via runpy, with runtime-only adaptations recorded in the manifest:
  1. utils.ROOT_PATH / BASE_ADV_PATH (documented as user-edited) point at --root;
  2. glob.glob results and AdvDataset.paths use '/' separators, because dataset.py splits paths on '/'
     (the release assumes POSIX);
  3. an empty `cnns_method` module is importable (the release ships only compiled .pyc
     for it; the attack path never uses it). It lives in shim/ and is put on the venv path
     with a .pth so that Windows-spawned DataLoader workers also see it.
timm 0.4.12 is used: the release pins the unpublished 0.4.13, and the eight models'
weight URLs are identical in 0.4.12 and 0.5.4 (see README).

Example:
  D:/transfer_recompute/venv_pna/Scripts/python.exe survey/recomputation/pna_rerun/run.py \
      --pna-root D:/transfer_recompute/pna --root D:/transfer_recompute/pna_root --record-dir survey/recomputation/pna_rerun/run1
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob as _glob
import hashlib
import json
import os
import platform
import runpy
import subprocess
import sys
from pathlib import Path

PINNED_COMMIT = "85f23c78284556057422abe395d0e1229a13156a"
SURROGATES = ["vit_base_patch16_224", "pit_b_224", "cait_s24_224", "visformer_small"]
VICTIMS = ["vit_base_patch16_224", "deit_base_distilled_patch16_224", "levit_256", "pit_b_224",
           "cait_s24_224", "convit_base", "tnt_s_patch16_224", "visformer_small"]
# Table 1 (PDF p. 5), row "Ours": MASR % per victim, averaged over the surrogates other than the victim.
PUBLISHED_MASR = {"vit_base_patch16_224": 46.10, "pit_b_224": 52.40, "cait_s24_224": 59.87,
                  "visformer_small": 58.60, "deit_base_distilled_patch16_224": 63.85,
                  "tnt_s_patch16_224": 67.25, "levit_256": 57.62, "convit_base": 63.70}
PREFIX = "rerun"


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while block := handle.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def folder_digest(folder):
    names = sorted(p.name for p in Path(folder).glob("*.png"))
    return len(names), hashlib.sha256("".join(f"{n} {sha256(Path(folder) / n)}\n" for n in names).encode()).hexdigest()


def run_script(pna_root, script, argv):
    old_argv, old_cwd = sys.argv, os.getcwd()
    sys.argv = [script, *argv]
    os.chdir(pna_root)
    try:
        runpy.run_path(str(Path(pna_root) / script), run_name="__main__")
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pna-root", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True, help="holds clean_resized_images/ and transformer/<json>")
    parser.add_argument("--record-dir", type=Path, required=True)
    parser.add_argument("--stage", choices=["attack", "evaluate", "all"], default="all")
    args = parser.parse_args()
    pna = args.pna_root.resolve()
    head = subprocess.run(["git", "-C", str(pna), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(pna), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True, check=True).stdout.strip()
    if head != PINNED_COMMIT or dirty:
        raise SystemExit(f"PNA checkout must be clean at {PINNED_COMMIT}")
    import cnns_method  # noqa: F401  (must resolve to the empty shim)
    if "pna_shim" not in cnns_method.__file__:
        raise SystemExit("cnns_method must come from the placeholder shim")

    original_glob = _glob.glob
    _glob.glob = lambda pattern, *a, **k: [p.replace("\\", "/") for p in original_glob(pattern, *a, **k)]
    sys.path.insert(0, str(pna))
    import utils
    root = str(args.root.resolve()).replace("\\", "/")
    utils.ROOT_PATH = root
    utils.BASE_ADV_PATH = root + "/paper_results"
    import dataset  # after ROOT_PATH is set: dataset computes its label-file path at import
    _init = dataset.AdvDataset.__init__

    def _posix_init(self, *a, **k):
        _init(self, *a, **k)
        self.paths = [p.replace("\\", "/") for p in self.paths]  # os.path.join inserts '\\'; __getitem__ splits on '/'
    dataset.AdvDataset.__init__ = _posix_init
    import torch
    import timm

    record = args.record_dir
    record.mkdir(parents=True, exist_ok=True)
    manifest_path = record / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest.update(
        repository="https://github.com/zhipeng-wei/PNA-PatchOut", commit=head, tracked_files_modified=False,
        runtime_adaptations=["utils.ROOT_PATH/BASE_ADV_PATH set to the run root",
                             "glob.glob results and AdvDataset.paths normalised to '/' separators (POSIX path splitting in dataset.py)",
                             "empty cnns_method placeholder module (release ships only .pyc; unused by OurAlgorithm)"],
        clean_zip_sha256=sha256(pna / "clean_resized_images.zip"),
        clean_images=dict(zip(("count", "digest"), folder_digest(args.root / "clean_resized_images"))),
        label_json_sha256=sha256(pna / "image_name_to_class_id_and_name.json"),
        environment=dict(python=sys.version.split()[0], platform=platform.platform(), torch=torch.__version__,
                         timm=timm.__version__, gpu=torch.cuda.get_device_name(0)))

    adv_dirs = {s: Path(utils.BASE_ADV_PATH) / f"model_{s}-method_OurAlgorithm-{PREFIX}" for s in SURROGATES}
    if args.stage in ("attack", "all"):
        for s in SURROGATES:
            if adv_dirs[s].exists() and len(list(adv_dirs[s].glob("*.png"))) == 1000:
                print("skip", s)
                continue
            started = dt.datetime.now(dt.timezone.utc).isoformat()
            run_script(pna, "our_attacks.py", ["--attack", "OurAlgorithm", "--gpu", "0", "--batch_size", "1",
                                               "--model_name", s, "--filename_prefix", PREFIX])
            count, digest = folder_digest(adv_dirs[s])
            manifest[f"attack_{s}"] = dict(started_utc=started, finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                                           release_argv=["--attack", "OurAlgorithm", "--batch_size", "1", "--model_name", s],
                                           defaults="epsilon 16/255, steps 10, step epsilon/steps, lamb 0.1, 130 of 196 patches, attention-gradient skip on",
                                           images=count, adversarial_digest=digest)
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    if args.stage in ("evaluate", "all"):
        folders = {"clean": args.root.resolve() / "clean_resized_images", **{s: adv_dirs[s] for s in SURROGATES}}
        for victim in VICTIMS:
            for key, folder in folders.items():
                existing = list(Path(folder).glob(f"prediction-model_{victim}-top1_*.csv"))
                if not existing:
                    run_script(pna, "evaluate.py", ["--adv_path", str(folder).replace("\\", "/"), "--gpu", "0",
                                                    "--batch_size", "10", "--model_name", victim])
        hub = Path(torch.hub.get_dir()) / "checkpoints"
        manifest["victim_checkpoints"] = {p.name: sha256(p) for p in sorted(hub.iterdir())
                                          if p.suffix in (".pth", ".npz", ".tar")}
        rows = {}
        for key, folder in folders.items():
            for victim in VICTIMS:
                path = next(Path(folder).glob(f"prediction-model_{victim}-top1_*.csv"))
                with open(path, newline="", encoding="utf-8") as handle:
                    for r in csv.DictReader(handle):
                        name = r["path"].replace("\\", "/").split("/")[-1]
                        rows.setdefault(name, {"image": name, "label": int(r["gt"])})[f"{victim}__{key}"] = int(r["pre"])
        columns = ["image", "label"] + [f"{v}__{k}" for v in VICTIMS for k in folders]
        with open(record / "per_example_predictions.csv", "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            writer.writerows(sorted(rows.values(), key=lambda r: r["image"]))
        summary = summarize(record / "per_example_predictions.csv")
        (record / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary["masr"], indent=1))


def summarize(path):
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    n = len(rows)
    asr, clean_acc, cond = {}, {}, {}
    for v in VICTIMS:
        clean_ok = [int(r[f"{v}__clean"]) == int(r["label"]) for r in rows]
        clean_acc[v] = round(100 * sum(clean_ok) / n, 4)
        for s in SURROGATES:
            wrong = [int(r[f"{v}__{s}"]) != int(r["label"]) for r in rows]
            asr[f"{s}->{v}"] = round(100 * sum(wrong) / n, 4)
            e = sum(clean_ok)
            cond[f"{s}->{v}"] = round(100 * sum(w for w, c in zip(wrong, clean_ok) if c) / e, 4) if e else None
    masr = {}
    for v in VICTIMS:
        vals = [asr[f"{s}->{v}"] for s in SURROGATES if s != v]
        mean = sum(vals) / len(vals)
        masr[v] = dict(surrogates=len(vals), rerun=round(mean, 4), published=PUBLISHED_MASR[v],
                       delta=round(mean - PUBLISHED_MASR[v], 4))
    return dict(images=n, note="ASR = victim top-1 != label over all 1,000 released images (release evaluate.py convention); "
                               "MASR averages over surrogates other than the victim",
                victim_clean_accuracy_percent=clean_acc, asr_percent=asr,
                victim_clean_correct_asr_percent=cond, masr=masr)


if __name__ == "__main__":
    main()
