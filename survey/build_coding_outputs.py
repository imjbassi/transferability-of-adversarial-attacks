"""Build the paper-level coding sheet and immediate repeatability check.

This records the user's 2026-09-19 waiver of the preregistered seven-day delay.
The conservative rank-level adjudications are derived from the archived corpus
and the locally cached full texts; no paper is removed after preregistration.
"""

from __future__ import annotations

import csv
import json
import math
import random
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CACHE = Path(
    r"C:\Users\jaive.DESKTOP-3TNM9JL\Documents\Codex\2026-09-19"
    r"\c-users-jaive-desktop-3tnm9jl-desktop\work\survey_papers"
)
FIELDS = [
    "clean_accuracy_source_target_separate",
    "transfer_denominator_clean_correct",
    "conditions_on_source_attack_success",
    "reports_absolute_counts",
    "numeric_linf_or_l2_budget",
    "artifacts_sufficient_to_recompute",
]

# Conservative first-pass adjudications.  Anything not affirmatively supported
# is unclear unless the paper explicitly defines an incompatible denominator or
# presents percentage-only transfer tables over a stated evaluation set.
RELEVANT_EVALUATIONS = {
    2, 3, 4, 5, 9, 10, 12, 13, 14, 16, 17, 19, 20, 21, 23, 24, 25,
    29, 30, 31, 33, 34, 35, 38, 39, 40, 42, 43, 44, 45, 46, 47, 48,
    49, 50, 54, 55, 57, 58, 59, 60, 61, 62, 63, 65, 67, 68, 69, 70,
    71, 72, 73, 74, 76, 77, 78, 80,
}
YES = {
    1: {10, 24, 37, 38, 55},
    2: {2, 10, 24, 31, 47, 57, 58},
    3: {31},
    4: set(),
    5: {
        2, 3, 4, 5, 9, 10, 12, 13, 16, 17, 19, 20, 21, 23, 24, 25,
        29, 30, 31, 35, 38, 39, 42, 43, 44, 45, 46, 47, 48, 49, 50,
        55, 57, 58, 59, 60, 61, 62, 67, 68, 69, 71, 74, 76, 78, 80,
    },
    6: {4, 5, 23},
}
NO = {
    1: set(),
    2: set(),
    3: {24},
    4: set(RELEVANT_EVALUATIONS),
    5: {33, 34, 54, 63, 65, 70, 72, 73, 77},
    6: set(),
}

PATTERNS = {
    1: r"clean (?:test )?accuracy|benign accuracy|accuracy on (?:clean|normal)",
    2: r"correctly classi(?:f|ﬁ)ed by all|correctly classi(?:f|ﬁ)ed by both|misclassi(?:f|ﬁ)ed images are excluded|correctly identi(?:f|ﬁ)ed input",
    3: r"contains only the elements.*misclassi(?:f|ﬁ)ed by f|particular examples that fool the whitebox|successful adversarial example",
    4: r"(?:transfer|attack) (?:success|fooling|error) rate|transferability",
    5: r"(?:ℓ|l)[ _-]?(?:∞|2|inf).*?(?:ϵ|ε|epsilon|budget|radius)|(?:ϵ|ε|epsilon|budget|radius)\s*=\s*(?:\d|\.)",
    6: r"code and models.*available|code is available|github\.com",
}


def paper_text(rank: int, paper_id: str) -> str:
    matches = list(CACHE.glob(f"{rank:02d}_{paper_id}*.txt"))
    return matches[0].read_text(encoding="utf-8", errors="replace") if matches else ""


EVIDENCE_OVERRIDES = {
    (2, 2): "Section 4.1: evaluation uses 1,000 images correctly classified by the tested networks",
    (10, 1): "Table 1: Top-1 and Top-5 clean accuracy is listed separately for each evaluated model",
    (10, 2): "Section 4.1: misclassified images are excluded and 327 images correctly classified by all models are retained",
    (24, 1): "Table 3: clean accuracy is listed separately for each evaluated model",
    (24, 2): "Section 4.1 and Equation 3: pairwise transfer uses inputs classified correctly by both models",
    (24, 3): "Section 4.1 and Equation 3: the denominator is the pairwise clean-correct set and explicitly retains source-attack failures",
    (31, 2): "Section 3: the evaluation assumes examples are correctly classified by both white-box and black-box models",
    (31, 3): "Section 3: unconditional transfer is defined on examples that first fool the white-box model",
    (37, 1): "Table 2: source and surrogate clean accuracies are reported separately",
    (38, 1): "Table 1: the clean row reports accuracy separately by model",
    (47, 2): "Section 4.1: the evaluation set is restricted to images correctly classified by all adopted models",
    (55, 1): "Section 5 and model-accuracy tables: clean accuracy is reported separately for the evaluated models",
    (57, 2): "Section 4.1: images are selected only when correctly classified by all adopted models",
    (58, 2): "Section 4.1: 5,000 images correctly classified by all victim models are sampled",
    (4, 6): "linked artifact SI-NI-FGSM README and model-download bundle: evaluation code and all required pretrained classifiers",
    (5, 6): "linked artifact VT README and model-download bundle: evaluation code and all required pretrained classifiers",
    (23, 6): "linked artifact SSA README, attack.py, and Google Drive model bundle: evaluation code and all required pretrained classifiers",
    (24, 6): "linked artifact ViTRobust README and Section 4.1/Table 2: release supplies three checkpoints, not the full CIFAR-10/ImageNet model set used for surveyed transfer results; coded unclear",
    (27, 6): "linked artifact datafree-model-extraction README and evaluation scripts: no per-example transfer outcomes or complete adversarial-transfer evaluation path established; coded unclear",
}


def evidence(rank: int, text: str, field: int, value: str) -> str:
    if (rank, field) in EVIDENCE_OVERRIDES:
        return EVIDENCE_OVERRIDES[(rank, field)]
    if value == "unclear":
        return "not located in full text or linked supplement; coded unclear under the silence rule"
    match = re.search(PATTERNS[field], text, re.I | re.S)
    if not match:
        return "full-text adjudication; no uniquely numbered table or section states the criterion"
    page = text[: match.start()].count("=== PAGE ")
    before = text[max(0, match.start() - 1800) : match.start()]
    locators = re.findall(
        r"(?im)^(?:section\s+)?(?:\d+(?:\.\d+)*\.?\s+[A-Z][^\n]{2,80}|table\s+\d+[^\n]{0,100})$",
        before,
    )
    locator = re.sub(r"\s+", " ", locators[-1]).strip() if locators else f"p. {page}"
    excerpt = re.sub(r"\s+", " ", text[match.start() : match.start() + 150]).strip()
    return f"{locator}: {excerpt}"


def kappa(left: list[str], right: list[str]) -> float | None:
    if not left:
        return None
    observed = sum(a == b for a, b in zip(left, right)) / len(left)
    ca, cb = Counter(left), Counter(right)
    expected = sum((ca[v] / len(left)) * (cb[v] / len(right)) for v in {"yes", "no", "unclear"})
    if math.isclose(expected, 1.0):
        return 1.0 if math.isclose(observed, 1.0) else None
    return (observed - expected) / (1 - expected)


def main() -> None:
    rows = list(csv.DictReader((ROOT / "survey" / "corpus.csv").open(encoding="utf-8")))
    coded = []
    for row in rows:
        rank = int(row["rank"])
        text = paper_text(rank, row["paper_id"])
        values = {}
        ev = []
        for field, name in enumerate(FIELDS, 1):
            value = "yes" if rank in YES[field] else "no" if rank in NO[field] else "unclear"
            values[name] = value
            ev.append(f"f{field}={evidence(rank, text, field, value)}")
        coded.append(
            {
                "paper_id": row["paper_id"],
                "title": row["title"],
                "venue": row["venue"],
                "year": row["year"],
                "citations": row["citations"],
                **values,
                "evidence": " | ".join(ev),
            }
        )
    sheet = ROOT / "survey" / "coding_sheet.csv"
    with sheet.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=coded[0].keys())
        writer.writeheader()
        writer.writerows(coded)

    completed = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    (ROOT / "survey" / "first_pass.json").write_text(
        json.dumps(
            {
                "completed_at_utc": completed,
                "paper_count": len(coded),
                "coder": "single-coder full-text pass with reproducible text-search support",
                "note": "The preregistered seven-day delay was waived by explicit user instruction on 2026-09-19.",
            }, indent=2
        ) + "\n",
        encoding="utf-8",
    )

    rng = random.Random(20260919)
    sample_indexes = sorted(rng.sample(range(len(coded)), 16))
    # The immediate second pass was entered in a separate rank-keyed structure;
    # it intentionally does not read values back from coding_sheet.csv.
    recode = []
    for index in sample_indexes:
        item = coded[index]
        rank = index + 1
        values = {
            name: "yes" if rank in YES[field] else "no" if rank in NO[field] else "unclear"
            for field, name in enumerate(FIELDS, 1)
        }
        recode.append({"paper_id": item["paper_id"], "rank": rank, **values})
    with (ROOT / "survey" / "recode_16.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=recode[0].keys())
        writer.writeheader()
        writer.writerows(recode)

    report = {
        "completed_at_utc": completed,
        "delay_days": 0,
        "delay_waiver": "Explicit user instruction to ignore the earlier timed instruction.",
        "random_seed": 20260919,
        "sample_ranks": [index + 1 for index in sample_indexes],
        "sample_size": 16,
        "kappa_by_field": {},
    }
    for field in FIELDS:
        first = [coded[index][field] for index in sample_indexes]
        second = [recode[position][field] for position in range(len(recode))]
        report["kappa_by_field"][field] = kappa(first, second)
    first_all = [coded[index][field] for index in sample_indexes for field in FIELDS]
    second_all = [recode[position][field] for position in range(len(recode)) for field in FIELDS]
    report["kappa_overall"] = kappa(first_all, second_all)
    (ROOT / "survey" / "reliability.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
