"""Compute Equation 1 bounds for the qualifying unconditional rate table."""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER_ID = "a9682a89b2fef793507c365a577f1521745db96c"
TARGETS = ["ResNet V2", "Inception V3", "Inception V4", "Inception-ResNet V2", "Ensemble"]
CLEAN = [89.6, 96.4, 97.6, 100.0, 99.8]
ATTACKS = ["FGSM", "BIM", "C&W", "JSMA", "TAP", "ATA"]
VALUES = {
    "ResNet V2": [
        [14.6, 56.3, 64.8, 66.8, 63.1], [4.4, 53.2, 62.0, 63.8, 54.3],
        [37.7, 94.5, 96.4, 98.5, 98.5], [27.2, 59.3, 65.2, 62.1, 64.4],
        [9.5, 51.2, 60.1, 55.5, 50.3], [8.7, 52.9, 58.3, 55.1, 49.4],
    ],
    "Inception V3": [
        [65.7, 27.2, 70.2, 72.9, 76.2], [76.8, 0.01, 67.7, 70.2, 73.6],
        [86.9, 24.5, 93.5, 96.2, 96.0], [66.4, 22.4, 57.2, 60.3, 68.9],
        [48.2, 0.1, 24.5, 26.3, 34.2], [47.2, 0.1, 22.1, 25.7, 31.9],
    ],
    "Inception V4": [
        [68.3, 67.1, 50.3, 72.8, 76.4], [62.1, 40.9, 0.9, 69.1, 55.5],
        [86.7, 91.7, 49.5, 93.2, 92.9], [70.7, 68.9, 30.0, 65.2, 68.9],
        [58.4, 27.3, 1.8, 24.2, 51.7], [59.9, 24.8, 0.9, 22.1, 50.3],
    ],
    "Inception-ResNet V2": [
        [71.7, 69.0, 76.5, 57.2, 78.7], [60.4, 41.5, 51.5, 1.2, 54.5],
        [85.6, 91.7, 92.4, 49.0, 93.5], [55.4, 62.7, 66.8, 50.3, 64.9],
        [53.3, 25.9, 33.2, 4.8, 48.2], [49.8, 22.1, 30.1, 1.2, 45.3],
    ],
}


def main() -> None:
    rows = []
    for source, matrix in VALUES.items():
        for attack, accuracies in zip(ATTACKS, matrix):
            for target, clean, attacked in zip(TARGETS, CLEAN, accuracies):
                if source == target:
                    continue
                error = 100.0 - attacked
                clean_error = 100.0 - clean
                rows.append(
                    {
                        "paper_id": PAPER_ID,
                        "source": source,
                        "target": target,
                        "attack": attack,
                        "clean_accuracy_percent": clean,
                        "clean_error_percent": round(clean_error, 2),
                        "reported_unconditional_attacked_error_percent": round(error, 2),
                        "newly_induced_error_lower_bound_percent": round(max(0.0, error - clean_error), 2),
                        "evidence": "Table 1, accuracy of undefended models under attacks",
                    }
                )
    with (ROOT / "survey" / "analytic_bounds.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    values = [row["newly_induced_error_lower_bound_percent"] for row in rows]
    summary = {
        "papers_qualifying": 1,
        "rates_bounded": len(values),
        "minimum_percent": min(values),
        "median_percent": statistics.median(values),
        "mean_percent": statistics.mean(values),
        "maximum_percent": max(values),
        "q1_percent": statistics.quantiles(values, n=4, method="inclusive")[0],
        "q3_percent": statistics.quantiles(values, n=4, method="inclusive")[2],
        "interpretation": "Each value is max(0, reported attacked error minus target clean error).",
    }
    (ROOT / "survey" / "analytic_bounds_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
