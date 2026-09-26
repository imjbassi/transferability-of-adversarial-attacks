"""Rounding-aware bounds for rank 20 (ILA, Huang et al., arXiv 1907.10823v3) CIFAR-10 tables.

Appendix A states that adversarial examples are generated "for all images in the
test set", and Section 4 reports each author-trained model's final test accuracy,
so clean and attacked accuracies share the full CIFAR-10 test population with no
source-success or clean-correct filtering (reviews/20.json, group
cifar10_full_test_transfer). This file is separate from the frozen first pass.

Included: fixed-configuration columns only (baseline attack and ILAP at the
source-chosen layer l), off-diagonal source/target pairs.
Excluded:
- "Opt ILAP" columns: the layer is chosen by evaluating on the transfer models.
- Table 2 C&W columns: all 48 printed cells lie on the 1/96 lattice. A value
  printed to 0.1 points lands on that lattice by chance with probability about
  0.1, so the C&W evaluation population is probably smaller than the stated
  test set and is not established.
- Tables 6-7: stated 50 x 32 = 1,600-image subset with no matched clean accuracy.
- Table 3 (best-over-hyperparameter values), Table 1/17 and figures (ImageNet or
  graphical).

Run: python survey/rank20_bounds.py --output survey/analytic_bounds_rank20.json
"""
import argparse
import json
import statistics
from pathlib import Path

from rounding_bounds import bounds

MODELS = ["ResNet18", "SENet18", "DenseNet121", "GoogLeNet"]
CLEAN = {"ResNet18": "94.8", "SENet18": "94.6", "DenseNet121": "95.6", "GoogLeNet": "94.9"}  # Section 4, PDF p. 4
# column -> (table, PDF page, 4x4 matrix rows=source, cols=target in MODELS order), accuracy after attack %.
COLUMNS = {
    "MI-FGSM 20 itr": ("Table 2", 6, [["5.7", "33.8", "35.1", "45.1"], ["31.0", "3.3", "31.6", "41.1"],
                                       ["34.4", "33.5", "6.4", "36.3"], ["44.6", "43.0", "38.9", "1.5"]]),
    "MI-FGSM 10 itr + ILAP (fixed l)": ("Table 2", 6, [["11.3", "30.6", "30.4", "37.7"], ["27.5", "10.0", "27.3", "34.8"],
                                                       ["28.1", "27.7", "4.0", "30.3"], ["34.5", "33.5", "29.2", "1.4"]]),
    "I-FGSM 20 itr": ("Table 4", 12, [["3.3", "44.4", "45.8", "58.6"], ["36.8", "2.4", "38.0", "48.4"],
                                      ["45.1", "43.4", "2.6", "47.3"], ["55.9", "55.6", "48.9", "0.9"]]),
    "I-FGSM 10 itr + ILAP (fixed l)": ("Table 4", 12, [["7.6", "27.5", "27.7", "35.8"], ["25.8", "7.9", "25.9", "33.7"],
                                                       ["26.7", "26.1", "1.7", "28.6"], ["34.0", "33.1", "28.7", "0.8"]]),
    "DeepFool 50 itr": ("Table 4", 12, [["48.7", "87.4", "89.1", "89.3"], ["91.9", "56.8", "92.9", "92.3"],
                                        ["81.6", "81.5", "34.9", "82.3"], ["92.3", "92.1", "93.1", "51.5"]]),
    "DeepFool 25 itr + ILAP (fixed l)": ("Table 4", 12, [["12.9", "43.7", "43.8", "50.7"], ["40.3", "11.4", "41.3", "48.7"],
                                                         ["30.1", "29.0", "4.1", "32.4"], ["44.0", "42.9", "38.1", "4.2"]]),
    "FGSM baseline": ("Table 5", 13, [["47.7", "63.6", "64.9", "66.5"], ["60.7", "40.7", "61.8", "63.8"],
                                      ["65.0", "65.0", "47.3", "64.6"], ["64.9", "65.1", "63.7", "36.6"]]),
    "FGSM + ILAP (fixed l)": ("Table 5", 13, [["2.0", "42.6", "44.6", "55.5"], ["37.4", "3.0", "37.0", "46.3"],
                                              ["36.4", "35.5", "5.8", "37.6"], ["43.5", "43.8", "39.7", "5.9"]]),
    "TAP 20 itr": ("Table 8", 17, [["6.2", "31.6", "32.7", "41.6"], ["31.4", "2.0", "31.3", "41.5"],
                                   ["35.2", "34.2", "4.8", "37.8"], ["37.1", "36.5", "32.6", "1.3"]]),
}
C_AND_W = ["7.3", "5.2", "2.1", "85.4", "41.7", "41.7", "84.4", "41.7", "41.7", "90.6", "57.3", "57.3",
           "87.5", "42.7", "42.7", "6.2", "7.3", "3.1", "88.5", "38.5", "38.5", "91.7", "52.1", "52.1",
           "87.5", "37.5", "37.5", "86.5", "34.4", "34.4", "2.1", "0.0", "0.0", "90.6", "45.8", "45.8",
           "89.6", "63.5", "60.4", "90.6", "53.1", "53.1", "89.6", "58.3", "51.0", "4.2", "0.0", "0.0"]


def on_lattice(display, n):
    return any(f"{100 * k / n:.1f}" == display for k in range(n + 1))


def paper_id():
    review = Path(__file__).parent / "evidence_audit" / "reviews" / "20.json"
    return json.loads(review.read_text(encoding="utf-8"))["paper_id"]


def build():
    pid = paper_id()
    rows = []
    for column, (table, page, matrix) in COLUMNS.items():
        for s, source in enumerate(MODELS):
            for t, target in enumerate(MODELS):
                if s == t:
                    continue
                rows.append(dict(paper_id=pid, source=source, target=target, attack=column, table=table,
                                 pdf_page=page, clean_display_percent=CLEAN[target],
                                 attacked_display_percent=matrix[s][t], **bounds(CLEAN[target], matrix[s][t])))
    lower = [r["induced_mass_lower_percent"] for r in rows]
    by_attack = {}
    for column in COLUMNS:
        vals = [r["induced_mass_lower_percent"] for r in rows if r["attack"] == column]
        by_attack[column] = dict(rates=len(vals), minimum_percent=min(vals),
                                 median_percent=round(statistics.median(vals), 6), maximum_percent=max(vals))
    return dict(
        scope="Single-paper extraction for rank 20; four CIFAR-10 models, 12 ordered pairs per column; correlated observations",
        evidence="Huang et al., arXiv 1907.10823v3: Section 4 clean test accuracies (PDF p. 4); Appendix A population statement; Tables 2, 4, 5, 8",
        rounding_assumption="Nearest displayed unit (0.1 points); closed intervals include ties. Not sampling uncertainty.",
        extraction_status="Same-auditor text-layer extraction with a rendered-page recheck; no independent second person",
        caveats=[
            "The population match rests on the Appendix A statement; the released script's --num_batches/--batch_size can evaluate a prefix subset, and Tables 6-7 do so explicitly (1,600 images). Which setting produced Tables 2, 4, 5 and 8 is not independently verified.",
            "Clean accuracies are the Section 4 'final test accuracies'; that they were measured with the same checkpoints and preprocessing as the attack evaluation is assumed, not verified.",
            "Table 8 is described as 'same as experiment in Table 2'; it inherits that population statement.",
            "DeepFool is not L-infinity-budgeted in the same way; the identity does not depend on the budget.",
        ],
        c_and_w_lattice_check=dict(cells=len(C_AND_W), on_1_96_lattice=sum(on_lattice(v, 96) for v in C_AND_W),
                                   on_10000_lattice=sum(on_lattice(v, 10000) for v in C_AND_W)),
        papers_extracted=1, rates_bounded=len(rows),
        summary=dict(minimum_percent=min(lower), median_percent=round(statistics.median(lower), 6),
                     maximum_percent=max(lower), mean_percent=round(statistics.mean(lower), 6)),
        by_attack=by_attack,
        rows=rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.dumps(build(), indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
