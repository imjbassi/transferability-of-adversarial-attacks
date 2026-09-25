"""Instrument the pinned Su et al. release in TensorFlow 1.8, without porting FGSM.

This is a selected-configuration rerun, not proof of published-table equivalence.
Run with a separate legacy Python environment; never import this as a modern port.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import time


PIN = "353ef696f594631f3577e94c01882c67e19aa3df"
SOURCE_HASHES = {
    "setup_imagenet.py": "6d78e1d697a208c8d50c0f80a1e798ed73a75efcae2d54db989d18623e8e5e63",
    "FGSM_attack.py": "3a4328db49d74198fccbfeeac44bf40d38df7501f20c1b2f9f9cb9c0aa250b92",
    "test_transferability.py": "353e8ff29c2f8aa748d27d1f7ecd893e7e89ada1e9f4005775ee7163c0f1c5d5",
}


def sha(path):
    digest = hashlib.sha256()
    with open(str(path), "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--epsilon", required=True, type=float)
    parser.add_argument("--images", default=1000, type=int)
    parser.add_argument("--source", default="inception_v1")
    parser.add_argument("--target", default="inception_v2")
    args = parser.parse_args()
    release, output = args.release.resolve(), args.output.resolve()
    if args.images < 1 or not 0 < args.epsilon <= 1:
        raise ValueError("Invalid cohort size or unit-pixel budget")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output must be new or empty; preserve prior runs")
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(release)).decode().strip() != PIN:
        raise ValueError("Wrong release commit")
    for name, expected in SOURCE_HASHES.items():
        if sha(release / name) != expected:
            raise ValueError("Modified upstream source: " + name)
    output.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(release))
    import numpy as np
    import tensorflow as tf
    import setup_imagenet as original
    from FGSM_attack import FGSM
    if tf.__version__ != "1.8.0":
        raise ValueError("This probe requires original TensorFlow 1.8.0")
    source_param, target_param = [original.model_params[name] for name in (args.source, args.target)]
    if source_param["size"] != target_param["size"]:
        raise ValueError("Probe deliberately requires equal-size models; no padding-policy assumptions")
    if any(token in name for name in (args.source, args.target) for token in ("vgg", "densenet", "alexnet")):
        raise ValueError("Probe currently restricted to unchanged 1001-output label space")
    os.chdir(str(release))
    random.seed(args.seed)
    np.random.seed(args.seed)
    names = sorted(os.listdir("imagenetdata/imgs"))
    random.shuffle(names)
    selected = names[:args.images]
    checkpoint_hashes = {p["model_filename"]: sha(release / "tmp/imagenet" / p["model_filename"])
                         for p in (source_param, target_param)}
    config = tf.ConfigProto(intra_op_parallelism_threads=4, inter_op_parallelism_threads=1)
    start = time.time()
    with open(str(output / "upstream_log.txt"), "w") as log, contextlib.redirect_stdout(log):
        sg, tg = tf.Graph(), tf.Graph()
        ss, ts = tf.Session(graph=sg, config=config), tf.Session(graph=tg, config=config)
        with sg.as_default():
            tf.set_random_seed(args.seed)
            original.CREATED_GRAPH = False
            source = original.ImageNetModel(ss, False, args.source)
            attack = FGSM(ss, source, args.epsilon, use_log=False, targeted=False,
                          batch_size=1, ord=np.inf, clip_min=-0.5, clip_max=0.5)
        with tg.as_default():
            tf.set_random_seed(args.seed)
            original.CREATED_GRAPH = False
            target = original.ImageNetModel(ts, False, args.target)
        records, skipped = [], []
        with open(str(output / "predictions.jsonl"), "w") as stream:
            for index, filename in enumerate(selected):
                loaded = original.readimg(filename, source.image_size)
                if loaded is None:
                    skipped.append({"image_id": filename, "reason": "non_rgb_original_loader"})
                    continue
                clean, label = loaded
                sc = int(np.argmax(source.model.predict(clean)))
                if sc != label:
                    skipped.append({"image_id": filename, "reason": "source_clean_incorrect", "label": label, "source_clean": sc})
                    continue
                onehot = np.eye(1001, dtype=np.float32)[label:label+1]
                adv = attack.attack_batch(clean[None], onehot)[0]
                sa = int(np.argmax(source.model.predict(adv)))
                tc = int(np.argmax(target.model.predict(clean)))
                ta = int(np.argmax(target.model.predict(adv)))
                linf = float(np.max(np.abs(adv-clean)))
                if linf > args.epsilon + 1e-6 or np.max(adv) > .500001 or np.min(adv) < -.500001:
                    raise ValueError("Attack budget/domain check failed")
                row = dict(image_id=filename, image_sha256=sha(release / "imagenetdata/imgs" / filename),
                           label=label, source_clean=sc, source_adv=sa, target_clean=tc, target_adv=ta,
                           l2=float(np.linalg.norm(adv-clean)), linf=linf,
                           adversarial_float32_sha256=hashlib.sha256(adv.astype(np.float32).tobytes()).hexdigest())
                records.append(row)
                stream.write(json.dumps(row, sort_keys=True) + "\n")
                stream.flush()
                if (index+1) % 50 == 0:
                    print("processed", index+1, "of", len(selected), "attackable", len(records), file=sys.__stdout__, flush=True)
        ss.close()
        ts.close()
    repo = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("existing_metrics", str(repo / "transferlab/metrics.py"))
    metrics_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metrics_module)
    summary = metrics_module.summarize(records)
    eligible = [r for r in records if r["target_clean"] == r["label"]]
    succeeded = [r for r in eligible if r["source_adv"] != r["label"]]
    failed = [r for r in eligible if r["source_adv"] == r["label"]]
    a_st = metrics_module.binomial(len(succeeded), len(eligible))
    b_st = metrics_module.binomial(sum(r["target_adv"] != r["label"] for r in failed), len(failed))
    summary.update(a_st=a_st, b_st=b_st)
    manifest = dict(status="selected_configuration_rerun_not_published_table_replication",
                    release_commit=PIN, upstream_hashes=SOURCE_HASHES, checkpoint_hashes=checkpoint_hashes,
                    harness_sha256=sha(Path(__file__)), python=platform.python_version(), tensorflow=tf.__version__,
                    numpy=np.__version__, source=args.source, target=args.target, epsilon=args.epsilon,
                    seed=args.seed, requested_images=args.images, selected_image_ids=selected,
                    skipped=skipped, source_clean_correct_count=len(records), elapsed_seconds=time.time()-start,
                    objective="original FGSM use_zvalue branch: ascend negative true-class logit",
                    execution="CPU; original attack and prediction classes; serial original image loader",
                    published_comparator_status="not_assigned_pending_seed_and_population_reconciliation",
                    adaptations=["serial loading replaces multiprocessing only", "record clean/source/target predictions before target-clean filtering", "same-size 1001-output models only"],
                    predictions_sha256=sha(output / "predictions.jsonl"), metrics=summary)
    with open(str(output / "manifest.json"), "w") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
