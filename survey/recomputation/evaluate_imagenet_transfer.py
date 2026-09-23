"""Compute denominator-aware metrics from an ImageNet transfer attack folder."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import transforms as T

HERE = Path(__file__).resolve().parent
_bootstrap = argparse.ArgumentParser(add_help=False)
_bootstrap.add_argument('--ssa-root', type=Path, required=True,
                        help='Populated SSA checkout; see PROVENANCE.md')
_paths, _ = _bootstrap.parse_known_args()
SSA = _paths.ssa_root.resolve()
if not (SSA / 'loader.py').is_file():
    raise SystemExit('SSA checkout must contain loader.py and documented dependencies')
sys.path.insert(0, str(SSA))
from loader import ImageNet  # noqa: E402
from Normalize import TfNormalize  # noqa: E402
from torch_nets import (  # noqa: E402
    tf_ens3_adv_inc_v3,
    tf_ens4_adv_inc_v3,
    tf_ens_adv_inc_res_v2,
    tf_inc_res_v2,
    tf_inception_v3,
    tf_inception_v4,
    tf_resnet_v2_50,
    tf_resnet_v2_101,
    tf_resnet_v2_152,
)

DEVICE = torch.device("cuda")
FACTORIES = {
    "tf_inception_v3": tf_inception_v3,
    "tf_inception_v4": tf_inception_v4,
    "tf_inc_res_v2": tf_inc_res_v2,
    "tf_resnet_v2_50": tf_resnet_v2_50,
    "tf_resnet_v2_101": tf_resnet_v2_101,
    "tf_resnet_v2_152": tf_resnet_v2_152,
    "tf_ens3_adv_inc_v3": tf_ens3_adv_inc_v3,
    "tf_ens4_adv_inc_v3": tf_ens4_adv_inc_v3,
    "tf_ens_adv_inc_res_v2": tf_ens_adv_inc_res_v2,
}
PUBLISHED = {
    "si-ni": {
        "tf_inception_v3": 100.0, "tf_inception_v4": 76.0,
        "tf_inc_res_v2": 73.3, "tf_resnet_v2_101": 67.6,
        "tf_ens3_adv_inc_v3": 31.6, "tf_ens4_adv_inc_v3": 30.0,
        "tf_ens_adv_inc_res_v2": 17.4,
    },
    "vmi": {
        "tf_inception_v3": 100.0, "tf_inception_v4": 71.7,
        "tf_inc_res_v2": 68.1, "tf_resnet_v2_101": 60.2,
        "tf_ens3_adv_inc_v3": 32.8, "tf_ens4_adv_inc_v3": 31.2,
        "tf_ens_adv_inc_res_v2": 17.5,
    },
}


def data_loader(directory):
    dataset = ImageNet(str(directory), str(SSA / "dataset" / "images.csv"), T.ToTensor())
    return DataLoader(dataset, batch_size=10, shuffle=False, num_workers=0)


def predict(model, directory):
    predictions, labels, names = [], [], []
    for images, batch_names, gt in data_loader(directory):
        with torch.no_grad():
            output = model(images.to(DEVICE))
            if isinstance(output, (tuple, list)):
                output = output[0]
        predictions.extend(output.argmax(1).cpu().tolist())
        labels.extend((gt + 1).tolist())
        names.extend(batch_names)
    return predictions, labels, names


def summarize(source_clean, source_adv, target_clean, target_adv, labels):
    eligible = [s == y and t == y for s, t, y in zip(source_clean, target_clean, labels)]
    source_success = [a != y for a, y in zip(source_adv, labels)]
    target_error = [a != y for a, y in zip(target_adv, labels)]
    e = sum(eligible)
    f = sum(x and s for x, s in zip(eligible, source_success))
    g = sum(x and t for x, t in zip(eligible, target_error))
    h = sum(x and s and t for x, s, t in zip(eligible, source_success, target_error))
    j = sum(x and not s and t for x, s, t in zip(eligible, source_success, target_error))
    return {
        "n": len(labels), "eligible_count": e, "source_success_count": f,
        "target_error_count": g, "joint_success_count": h,
        "failed_source_target_error_count": j,
        "unconditional_attacked_error_percent": 100 * sum(target_error) / len(labels),
        "ptr_percent": 100 * g / e if e else None,
        "ctr_percent": 100 * h / f if f else None,
        "a_st_percent": 100 * f / e if e else None,
        "b_st_percent": 100 * j / (e - f) if e > f else None,
    }


def load_model(name):
    return nn.Sequential(
        TfNormalize("tensorflow"),
        FACTORIES[name].KitModel(str(SSA / "models" / f"{name}.npy")).eval(),
    ).to(DEVICE).eval()


def main():
    parser = argparse.ArgumentParser(parents=[_bootstrap])
    parser.add_argument("attack", choices=PUBLISHED)
    parser.add_argument("adv_dir", type=Path)
    parser.add_argument("output_prefix", type=Path)
    args = parser.parse_args()
    clean_dir = SSA / "dataset" / "images"
    source = load_model("tf_inception_v3")
    source_clean, labels, names = predict(source, clean_dir)
    source_adv, _, _ = predict(source, args.adv_dir)
    per_example = {
        name: {"label": label, "source_clean": clean, "source_adv": adv}
        for name, label, clean, adv in zip(names, labels, source_clean, source_adv)
    }
    results = []
    for name in FACTORIES:
        model = source if name == "tf_inception_v3" else load_model(name)
        target_clean = source_clean if name == "tf_inception_v3" else predict(model, clean_dir)[0]
        target_adv = source_adv if name == "tf_inception_v3" else predict(model, args.adv_dir)[0]
        row = {"model": name, **summarize(source_clean, source_adv, target_clean, target_adv, labels)}
        published = PUBLISHED[args.attack].get(name)
        row["published_unconditional_percent"] = published
        row["delta_vs_published_points"] = (
            row["unconditional_attacked_error_percent"] - published if published is not None else None
        )
        results.append(row)
        for image_name, clean, adv in zip(names, target_clean, target_adv):
            per_example[image_name][f"{name}_clean"] = clean
            per_example[image_name][f"{name}_adv"] = adv
        if name != "tf_inception_v3":
            del model
            torch.cuda.empty_cache()
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    args.output_prefix.with_suffix(".json").write_text(json.dumps(results, indent=2) + "\n")
    with args.output_prefix.with_suffix(".csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["image_id", *next(iter(per_example.values())).keys()])
        writer.writeheader()
        for image_name, values in per_example.items():
            writer.writerow({"image_id": image_name, **values})
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
