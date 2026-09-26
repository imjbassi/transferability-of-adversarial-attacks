"""Manifested rerun of the released SSA S2I-FGSM attack (rank 23, Long et al. ECCV 2022).

Stages:
  attack    run the unchanged released attack.py (seeded through seeded_attack.py)
  evaluate  per-example predictions of the release's source and nine converted targets
Both stages append to manifest.json in --record-dir. Adversarial PNGs stay in
--work-dir (not committed); their aggregate hash is recorded.

Converted target weights are .npy object arrays. They are read with a restricted
unpickler that admits only numpy array reconstruction and _codecs.encode, so no
arbitrary code runs; the release's own np.load(allow_pickle=True) is not used.

Example:
  python survey/recomputation/ssa_rerun/run.py --ssa-root D:/transfer_recompute/ssa \
      --weights-dir D:/transfer_recompute/ssa_models --work-dir D:/transfer_recompute/ssa_run_seed0 \
      --record-dir survey/recomputation/ssa_rerun --seed 0 all
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import pickle
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
from numpy.lib import format as npf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from verify_predictions import summarize  # noqa: E402

PINNED_COMMIT = "c955cf07c8372bfc4e9f17e647042e027f9f3b1d"
TARGETS = ["tf_inception_v3", "tf_inception_v4", "tf_inc_res_v2", "tf_resnet_v2_50", "tf_resnet_v2_101",
           "tf_resnet_v2_152", "tf_ens3_adv_inc_v3", "tf_ens4_adv_inc_v3", "tf_ens_adv_inc_res_v2"]
WEIGHT_FILE = {name: f"tf2torch_{name[3:]}.npy" for name in TARGETS}
WEIGHT_URL = "https://github.com/ylhz/tf_to_pytorch_model/releases/download/v1.0/"
# Table 1 (PDF p. 10), S2I-FGSM, Inc-v3 source, attack success rate (%); '*' marks white-box in the paper.
PUBLISHED = {"tf_inception_v3": 99.7, "tf_inception_v4": 65.0, "tf_inc_res_v2": 58.9,
             "tf_resnet_v2_152": 50.3, "tf_resnet_v2_50": 56.2, "tf_resnet_v2_101": 53.3}
SAFE_CLASSES = {("numpy", "dtype"), ("numpy", "ndarray"), ("numpy.core.multiarray", "_reconstruct"),
                ("numpy._core.multiarray", "_reconstruct"), ("_codecs", "encode")}


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) in SAFE_CLASSES:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"blocked {module}.{name}")


def safe_load_weights(path):
    with open(path, "rb") as handle:
        version = npf.read_magic(handle)
        reader = npf.read_array_header_1_0 if version == (1, 0) else npf.read_array_header_2_0
        shape, _, dtype = reader(handle)
        if shape != () or not dtype.hasobject:
            raise ValueError(f"{path}: expected a 0-d object array")
        obj = RestrictedUnpickler(handle, encoding="latin1").load()
    weights = obj.item()
    if not isinstance(weights, dict):
        raise ValueError(f"{path}: payload is not a dict")
    return weights


def sha256(path, chunk=1 << 20):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def folder_digest(folder, names):
    """Hash of 'name sha256' lines in the given order."""
    lines = "".join(f"{n} {sha256(Path(folder) / n)}\n" for n in names)
    return hashlib.sha256(lines.encode()).hexdigest()


def image_names(ssa_root):
    with open(Path(ssa_root) / "dataset" / "images.csv", newline="", encoding="utf-8") as handle:
        return [row["ImageId"] + ".png" for row in csv.DictReader(handle)]


def update_manifest(record_dir, key, value):
    path = Path(record_dir) / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    manifest[key] = value
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def environment():
    import torch
    return dict(python=sys.version.split()[0], platform=platform.platform(), torch=torch.__version__,
                cuda=torch.version.cuda, cudnn=torch.backends.cudnn.version(),
                gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                numpy=np.__version__)


def checkout_state(ssa_root):
    head = subprocess.run(["git", "-C", str(ssa_root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(ssa_root), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True, check=True).stdout.strip()
    if head != PINNED_COMMIT or dirty:
        raise SystemExit(f"SSA checkout must be clean at {PINNED_COMMIT}; got {head} dirty={bool(dirty)}")
    return dict(repository="https://github.com/yuyang-long/SSA", commit=head, tracked_files_modified=False,
                attack_py_sha256=sha256(Path(ssa_root) / "attack.py"),
                images_csv_sha256=sha256(Path(ssa_root) / "dataset" / "images.csv"),
                clean_images_digest=folder_digest(Path(ssa_root) / "dataset" / "images", image_names(ssa_root)))


def run_attack(args):
    out = Path(args.work_dir) / "adv"
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} is not empty; choose a new work dir")
    out.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(HERE / "seeded_attack.py"), str(args.seed), "--output_dir", str(out) + "/"]
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    subprocess.run(command, cwd=args.ssa_root, check=True)
    names = image_names(args.ssa_root)
    missing = [n for n in names if not (out / n).exists()]
    if missing:
        raise SystemExit(f"{len(missing)} adversarial images missing")
    import torch
    source_ckpt = Path(torch.hub.get_dir()) / "checkpoints" / "inception_v3_google-1a9a5a14.pth"
    update_manifest(args.record_dir, "attack", dict(
        started_utc=started, finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        command=["python", "survey/recomputation/ssa_rerun/seeded_attack.py", str(args.seed), "--output_dir", "<work-dir>/adv/"],
        seed=args.seed, released_defaults="max_epsilon=16, num_iter=10 (hard-coded), N=20, rho=0.5, sigma=16, batch_size=10; momentum/DI/TI lines commented out in release (S2I-FGSM)",
        source_model="pretrainedmodels.inceptionv3(pretrained='imagenet') as in released attack.py",
        source_checkpoint=dict(file=source_ckpt.name, url="https://download.pytorch.org/models/inception_v3_google-1a9a5a14.pth",
                               sha256=sha256(source_ckpt)),
        adversarial_images_digest=folder_digest(out, names), adversarial_image_count=len(names),
        determinism_note="torch/numpy/random seeded and cudnn.deterministic set; GPU kernels may still be nondeterministic",
        environment=environment(), checkout=checkout_state(args.ssa_root)))


def run_evaluate(args):
    import torch
    from torch import nn
    from torch.utils.data import DataLoader
    from torchvision import transforms as T
    sys.path.insert(0, str(Path(args.ssa_root).resolve()))
    import importlib
    import pretrainedmodels
    from loader import ImageNet
    from Normalize import Normalize, TfNormalize

    device = torch.device("cuda")
    names = image_names(args.ssa_root)
    clean_dir, adv_dir = Path(args.ssa_root) / "dataset" / "images", Path(args.work_dir) / "adv"
    csv_path = str(Path(args.ssa_root) / "dataset" / "images.csv")

    def predict(model, folder):
        loader = DataLoader(ImageNet(str(folder), csv_path, T.ToTensor()), batch_size=10, shuffle=False, num_workers=0)
        preds, labels, ids = [], [], []
        with torch.no_grad():
            for images, batch_ids, gt in loader:
                out = model(images.to(device))
                out = out[0] if isinstance(out, (tuple, list)) else out
                preds += out.argmax(1).cpu().tolist(); labels += gt.tolist(); ids += list(batch_ids)
        return preds, labels, ids

    source = nn.Sequential(Normalize(np.array([0.5] * 3), np.array([0.5] * 3)),
                           pretrainedmodels.inceptionv3(num_classes=1000, pretrained="imagenet").eval()).to(device).eval()
    source_clean, labels, ids = predict(source, clean_dir)
    source_adv, _, ids_adv = predict(source, adv_dir)
    assert ids == ids_adv == names
    rows = [dict(image_id=i, label=y, source_clean=c, source_adv=a) for i, y, c, a in zip(ids, labels, source_clean, source_adv)]
    del source
    weight_hashes = {}
    for name in TARGETS:
        path = Path(args.weights_dir) / WEIGHT_FILE[name]
        weight_hashes[name] = dict(file=path.name, url=WEIGHT_URL + path.name, bytes=path.stat().st_size, sha256=sha256(path))
        module = importlib.import_module(f"torch_nets.{name}")
        module.load_weights = safe_load_weights
        model = nn.Sequential(TfNormalize("tensorflow"), module.KitModel(str(path)).eval()).to(device).eval()
        for suffix, folder in (("clean", clean_dir), ("adv", adv_dir)):
            preds, _, _ = predict(model, folder)
            for row, p in zip(rows, preds):
                row[f"{name}_{suffix}"] = p
        del model
        torch.cuda.empty_cache()
        print(name, "done", flush=True)
    record = Path(args.record_dir)
    with (record / "per_example_predictions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    int_rows = [{k: v for k, v in r.items() if k != "image_id"} for r in rows]
    metrics = []
    for name in TARGETS:
        m = dict(model=name, **summarize(int_rows, name, 1))
        pub = PUBLISHED.get(name)
        m["target_clean_error_percent"] = 100 * sum(r[f"{name}_clean"] != r["label"] + 1 for r in int_rows) / len(int_rows)
        m["published_unconditional_percent"] = pub
        m["delta_vs_published_points"] = None if pub is None else round(m["unconditional_attacked_error_percent"] - pub, 6)
        metrics.append(m)
    source_error = 100 * sum(r["source_adv"] != r["label"] for r in int_rows) / len(int_rows)
    (record / "conditioned_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    update_manifest(args.record_dir, "evaluate", dict(
        finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(), target_weights=weight_hashes,
        weight_loading="restricted unpickler (numpy dtype/ndarray/_reconstruct, _codecs.encode only)",
        evaluator="this script; verify.py equivalent: target argmax != label+1 over 1,000 images",
        source_white_box_error_percent=source_error, label_convention="label and source 0-based; converted targets 1-based (compare to label+1)",
        adversarial_images_digest=folder_digest(adv_dir, names), environment=environment()))
    print(json.dumps(metrics, indent=1))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ssa-root", type=Path, required=True)
    parser.add_argument("--weights-dir", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--record-dir", type=Path, default=HERE)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("stage", choices=["attack", "evaluate", "all"])
    args = parser.parse_args()
    checkout_state(args.ssa_root)
    if args.stage in ("attack", "all"):
        run_attack(args)
    if args.stage in ("evaluate", "all"):
        run_evaluate(args)


if __name__ == "__main__":
    main()
