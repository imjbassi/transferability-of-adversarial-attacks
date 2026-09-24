"""Structural validation only; completion records do not prove evidence correctness."""
import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def aggregate_conditioning(values):
    """Dated repair rule for fields 2/3; preserve explicit mixed reporting."""
    if any(value not in {"yes", "no", "unclear"} for value in values):
        raise ValueError("Invalid conditioning value")
    kinds = set(values)
    reason = "unresolved_scope"
    result = "unclear"
    if not values:
        reason = "not_applicable_to_located_results"
    elif kinds == {"yes"}:
        result, reason = "yes", "all_scopes_explicit_yes"
    elif kinds == {"no"}:
        result, reason = "no", "all_scopes_explicit_no"
    elif {"yes", "no"} <= kinds:
        reason = "mixed_explicit"
    return {"value": result, "reason": reason, "any_explicit_yes": "yes" in kinds}

def require_text(item, keys):
    for key in keys:
        if not isinstance(item.get(key), str) or not item[key].strip():
            raise ValueError(f"Missing nonempty text: {key}")

def validate_review(review, paper):
    if (review.get("rank"), review.get("paper_id")) != (paper["rank"], paper["paper_id"]):
        raise ValueError("Review identity differs from ledger")
    date.fromisoformat(review["review_date"])
    if review.get("amendment") != "coding_amendment_2026-09-23.md":
        raise ValueError("Unknown repair amendment")
    if review.get("review_mode") != "non_blind_evidence_audit":
        raise ValueError("These reviews must not be labeled blind")
    coverage = review["coverage"]
    require_text(coverage, ["main", "supplement", "applicability", "excluded_results"])
    if coverage.get("inventory_complete") is not True:
        raise ValueError("Complete review requires completed result inventory")
    sources = review["sources"]
    if not sources or len({s["id"] for s in sources}) != len(sources):
        raise ValueError("Sources must have unique identifiers")
    for source in sources:
        require_text(source, ["id", "url", "sha256"])
        if not re.fullmatch(r"[0-9a-f]{64}", source["sha256"]):
            raise ValueError("Source requires SHA-256")
    groups = review["result_groups"]
    group_ids = {g["id"] for g in groups}
    if len(group_ids) != len(groups):
        raise ValueError("Duplicate result group")
    for group in groups:
        require_text(group, ["id", "locator", "population", "outcome", "evidence"])
    judgments = review["judgments"]
    if set(judgments) != {f"f{i}" for i in range(1, 7)}:
        raise ValueError("Exactly six field judgments required")
    for judgment in judgments.values():
        require_text(judgment, ["value", "reason", "locator", "evidence"])
        if judgment["value"] not in {"yes", "no", "unclear"}:
            raise ValueError("Invalid judgment category")
    if not groups:
        # Enforce the existing amendment's non-applicability rule for all fields,
        # not just the two conditioning fields aggregated below.
        for judgment in judgments.values():
            if (judgment["value"], judgment["reason"]) != (
                "unclear", "not_applicable_to_located_results"
            ):
                raise ValueError("Empty result inventory requires non-applicable judgments")
        exclusion = review.get("bounds_exclusion", {})
        require_text(exclusion, ["status", "locator", "reason"])
        if exclusion["status"] != "not_applicable_to_located_results":
            raise ValueError("Empty result inventory requires an explicit bounds exclusion")
    elif "bounds_exclusion" in review:
        raise ValueError("Use group-specific bounds checks for nonempty inventories")
    for field in ["f2", "f3"]:
        derived = aggregate_conditioning([group[field] for group in groups])
        if any(judgments[field][key] != derived[key] for key in ["value", "reason"]):
            raise ValueError("Conditioning aggregation differs from amendment")
    if not review["artifact_checks"]:
        raise ValueError("Artifact search log required, including unsuccessful checks")
    for check in review["artifact_checks"]:
        require_text(check, ["date", "url", "result"])
        date.fromisoformat(check["date"])
    covered = set()
    for check in review["bounds_checks"]:
        require_text(check, ["status", "locator", "reason"])
        if not check["groups"] or not set(check["groups"]) <= group_ids:
            raise ValueError("Bounds check has unknown or empty scope")
        covered.update(check["groups"])
    if covered != group_ids:
        raise ValueError("Bounds eligibility must cover all result groups")
    return {f: aggregate_conditioning([g[f] for g in groups]) for f in ["f2", "f3"]}

def validate():
    data = json.loads((ROOT / "evidence_audit/ledger.json").read_text(encoding="utf-8"))
    with (ROOT / "corpus.csv").open(encoding="utf-8-sig", newline="") as handle:
        corpus = list(csv.DictReader(handle))
    papers = data["papers"]
    if len(papers) != 80 or len({p["paper_id"] for p in papers}) != 80:
        raise ValueError("Audit must retain all 80 distinct frozen papers")
    for expected, actual in zip(corpus, papers):
        if (expected["paper_id"], int(expected["rank"]), expected["title"]) != (
            actual["paper_id"], actual["rank"], actual["title"]
        ):
            raise ValueError("Audit order or identity differs from frozen corpus")
        if actual["evidence_audit"] not in {"pending", "partial", "complete"}:
            raise ValueError("Invalid audit workflow state")
        if actual["evidence_audit"] == "partial" and not actual["notes"]:
            raise ValueError("Partial review requires an evidence locator")
        if actual["evidence_audit"] == "complete":
            review_path = ROOT / "evidence_audit/reviews" / f"{actual['rank']:02d}.json"
            validate_review(json.loads(review_path.read_text(encoding="utf-8")), actual)
    counts = Counter(p["evidence_audit"] for p in papers)
    return {
        "papers": len(papers),
        "partial": counts["partial"],
        "pending": counts["pending"],
        "complete": counts["complete"],
        "warning": "Validates identity, evidence-record structure and conditioning aggregation, not evidence correctness. Complete means documented review, not recomputation or independent validation. No survey prevalence is calculated."
    }

if __name__ == "__main__":
    print(json.dumps(validate(), indent=2))
