"""Conditioned transfer quantities for every rerun that archived per-example predictions.

For each source -> target pair (target != source) this computes, over the rerun's image set:
  unconditional   P(target adversarial prediction != label)        (the metric the releases report)
  PTR             P(target wrong | source and target clean-correct)
  a_st            P(source wrong after attack | both clean-correct)
  CTR             P(target wrong | both clean-correct, source fooled)
  b_st            P(target wrong | both clean-correct, source not fooled)
using the same eligible-set definition as verify_predictions.summarize. Counts are kept so
every rate can be re-derived. These are descriptive quantities for selected configurations
of four papers' releases, not corpus estimates.

Run: python survey/recomputation/conditioning_across_reruns.py [--output PATH]
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def quantities(rows):
    """rows: dicts with ints y, sc, sa, tc, ta (all in the same label space)."""
    eligible = [r for r in rows if r["sc"] == r["y"] and r["tc"] == r["y"]]
    fooled = [r for r in eligible if r["sa"] != r["y"]]
    unfooled = [r for r in eligible if r["sa"] == r["y"]]
    wrong = lambda r: r["ta"] != r["y"]
    n, e, f = len(rows), len(eligible), len(fooled)
    g, h, j = sum(map(wrong, eligible)), sum(map(wrong, fooled)), sum(map(wrong, unfooled))
    pct = lambda a, b: round(100 * a / b, 4) if b else None
    return dict(n=n, unconditional_wrong=sum(map(wrong, rows)), eligible=e, source_fooled=f,
                eligible_target_wrong=g, fooled_target_wrong=h, unfooled_target_wrong=j,
                unconditional_percent=pct(sum(map(wrong, rows)), n), ptr_percent=pct(g, e),
                a_st_percent=pct(f, e), ctr_percent=pct(h, f), b_st_percent=pct(j, e - f),
                ctr_minus_unconditional_points=None if not f else round(100 * h / f - 100 * sum(map(wrong, rows)) / n, 4))


def read(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def ssa(seed):
    rows = read(HERE / "ssa_rerun" / seed / "per_example_predictions.csv")
    targets = [c[:-6] for c in rows[0] if c.endswith("_clean") and c != "source_clean"]
    out = []
    for t in targets:
        # source is 0-based pretrainedmodels Inception-v3; converted targets are 1-based
        data = [dict(y=int(r["label"]), sc=int(r["source_clean"]), sa=int(r["source_adv"]),
                     tc=int(r[f"{t}_clean"]) - 1, ta=int(r[f"{t}_adv"]) - 1) for r in rows]
        out.append(dict(rerun=f"ssa_rerun/{seed}", paper_rank=23, config="S2I-FGSM", source="pretrainedmodels inceptionv3",
                        target=t, **quantities(data)))
    return out


def paired(rerun, rank, path, sources):
    """Tables with '<model>__<column>' columns; sources maps config column -> source model column."""
    rows = read(path)
    models = sorted({c.split("__")[0] for c in rows[0] if "__" in c})
    out = []
    for cfg, src in sources.items():
        for t in models:
            if t == src:
                continue
            data = [dict(y=int(r["label"]), sc=int(r[f"{src}__clean"]), sa=int(r[f"{src}__{cfg}"]),
                         tc=int(r[f"{t}__clean"]), ta=int(r[f"{t}__{cfg}"])) for r in rows]
            out.append(dict(rerun=rerun, paper_rank=rank, config=cfg, source=src, target=t, **quantities(data)))
    return out


def build():
    cells = ssa("seed0") + ssa("seed1")
    cells += paired("sgm_rerun/run1", 13, HERE / "sgm_rerun/run1/per_example_predictions.csv",
                    {"rn152_pgd": "resnet152", "rn152_sgm": "resnet152", "dn201_pgd": "densenet201", "dn201_sgm": "densenet201"})
    cells += paired("pna_rerun/run1", 47, HERE / "pna_rerun/run1/per_example_predictions.csv",
                    {s: s for s in ["vit_base_patch16_224", "pit_b_224", "cait_s24_224", "visformer_small"]})
    cells += paired("sia_rerun/run1", 57, HERE / "sia_rerun/run1/per_example_predictions.csv",
                    {"mu1": "resnet18", "mu0_release_default": "resnet18"})
    diffs = [c["ctr_minus_unconditional_points"] for c in cells if c["ctr_minus_unconditional_points"] is not None]
    gaps = [c["unconditional_percent"] - c["ptr_percent"] for c in cells if c["ptr_percent"] is not None]
    return dict(
        scope="Selected configurations from four released pipelines (ranks 13, 23, 47, 57) rerun in this repository; descriptive, not corpus estimates",
        definitions="eligible = source and target both correct on the clean image; CTR conditions additionally on the source being fooled",
        pairs=len(cells),
        ctr_minus_unconditional_points=dict(minimum=min(diffs), maximum=max(diffs), median=sorted(diffs)[len(diffs) // 2]),
        unconditional_minus_ptr_points=dict(minimum=round(min(gaps), 4), maximum=round(max(gaps), 4)),
        cells=cells)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "conditioning_across_reruns.json")
    args = parser.parse_args()
    result = build()
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "cells"}, indent=1))
