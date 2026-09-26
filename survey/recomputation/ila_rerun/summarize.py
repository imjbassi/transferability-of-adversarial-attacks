"""Aggregate a release_output.csv from run.py and compare with the published CIFAR-10 table cells.

Per-batch accuracies are weighted by batch size (all batches full when
num_batches * batch_size <= 10,000 and batch_size divides 10,000).
Layer indices follow the release's enumerate(model._modules), which the
paper's Appendix A list matches (ResNet18: conv, bn, layer1..layer4, linear).

Run: python survey/recomputation/ila_rerun/summarize.py WORK_DIR --attack ifgsm --output OUT.json
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

CLEAN_PUBLISHED = {"ResNet18": 94.8, "SENet18": 94.6, "DenseNet121": 95.6, "GoogLeNet": 94.9}  # Section 4, PDF p. 4
# (attack, source): (fixed l, baseline column, ILAP column); accuracy after attack %, PDF p. 12 (Table 4) / p. 6 (Table 2)
PUBLISHED = {
    ("ifgsm", "ResNet18"): (4, {"ResNet18": 3.3, "SENet18": 44.4, "DenseNet121": 45.8, "GoogLeNet": 58.6},
                            {"ResNet18": 7.6, "SENet18": 27.5, "DenseNet121": 27.7, "GoogLeNet": 35.8}, "Table 4 I-FGSM"),
    ("momentum_ifgsm", "ResNet18"): (4, {"ResNet18": 5.7, "SENet18": 33.8, "DenseNet121": 35.1, "GoogLeNet": 45.1},
                                     {"ResNet18": 11.3, "SENet18": 30.6, "DenseNet121": 30.4, "GoogLeNet": 37.7}, "Table 2 MI-FGSM"),
}


def summarize(work_dir, attack, source="ResNet18"):
    rows = list(csv.DictReader(open(Path(work_dir) / "release_output.csv", newline="", encoding="utf-8")))
    manifest = json.loads((Path(work_dir) / "manifest.json").read_text(encoding="utf-8"))
    batch = int(manifest["command"][manifest["command"].index("--batch-size") + 1])
    acc, clean, batches = defaultdict(float), defaultdict(float), defaultdict(set)
    for r in rows:
        ila = r["with_ILA"] == "True"
        layer = int(float(r["layer_index"])) if ila else None
        key = (r["target_model"], ila, layer)
        acc[key] += float(r["acc_after_attack"]) * batch
        clean[key] += float(r["original_acc"]) * batch
        batches[key].add(r["batch_index"])
    n = {k: len(v) * batch for k, v in batches.items()}
    cells = [dict(target=t, with_ila=ila, layer_index=l, images=n[(t, ila, l)],
                  acc_after_attack_percent=round(acc[(t, ila, l)] / n[(t, ila, l)], 4),
                  clean_accuracy_percent=round(clean[(t, ila, l)] / n[(t, ila, l)], 4))
             for (t, ila, l) in sorted(acc, key=lambda k: (k[0], k[1], -1 if k[2] is None else k[2]))]
    comparison = []
    layer, base, ilap, table = PUBLISHED[(attack, source)]
    for target in base:
        b = next(c for c in cells if c["target"] == target and not c["with_ila"])
        i = next(c for c in cells if c["target"] == target and c["with_ila"] and c["layer_index"] == layer)
        comparison.append(dict(
            target=target, white_box=target == source,
            clean_recomputed=b["clean_accuracy_percent"], clean_published=CLEAN_PUBLISHED[target],
            baseline_recomputed=b["acc_after_attack_percent"], baseline_published=base[target],
            baseline_delta=round(b["acc_after_attack_percent"] - base[target], 4),
            ilap_recomputed=i["acc_after_attack_percent"], ilap_published=ilap[target],
            ilap_delta=round(i["acc_after_attack_percent"] - ilap[target], 4)))
    return dict(attack=attack, source=source, published_table=table, fixed_layer_index=layer,
                images=max(n.values()), manifest_sha256_of_release_output=manifest["release_output_sha256"],
                comparison=comparison, cells=cells)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("work_dir", type=Path)
    parser.add_argument("--attack", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.dumps(summarize(args.work_dir, args.attack), indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload)
