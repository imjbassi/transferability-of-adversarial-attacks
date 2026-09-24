"""Dependency-free boundary tests; no model execution."""
import unittest
import json
from pathlib import Path
from compute_reliability import kappa
from count_reconstruction import count_candidates
from rounding_bounds import bounds, build, interval
from recomputation.verify_predictions import summarize, verify
from validate_evidence_audit import aggregate_conditioning, validate_review

class AuditTests(unittest.TestCase):
    def test_count_recovery_known_thousand(self):
        self.assertEqual(count_candidates('23.5', 1000)['unique_numerator'], 235)
    def test_count_recovery_five_thousand_ambiguous(self):
        result = count_candidates('23.5', 5000)
        self.assertEqual((result['minimum_numerator'], result['maximum_numerator']), (1173, 1177))
        self.assertIsNone(result['unique_numerator'])
    def test_count_recovery_impossible(self):
        self.assertEqual(count_candidates('0.01', 1000)['candidate_count'], 0)
    def test_count_recovery_bad_denominator(self):
        for denominator in [0, -1, 1.5, True]:
            with self.assertRaises(ValueError):
                count_candidates('50.0', denominator)
    def test_rounding_bound(self):
        self.assertAlmostEqual(bounds('89.6', '65.7')['induced_mass_lower_percent'], 23.8)
    def test_rounded_hundred_is_not_exact(self):
        self.assertEqual([float(x) for x in interval('100')], [99.5, 100])
    def test_zero_clean_conditional_undefined(self):
        self.assertIsNone(bounds('0', '40.0')['target_clean_conditional_lower_percent'])
    def test_invalid_percentage(self):
        for value in ['-1', '101', 'NaN']:
            with self.assertRaises(ValueError):
                interval(value)
    def test_case_scope(self):
        result = build()
        self.assertEqual(result['rates_bounded'], 96)
        self.assertEqual(result['papers_extracted'], 1)
        self.assertTrue(all(0 <= r['induced_mass_lower_percent'] <= r['induced_mass_upper_percent'] <= 100 for r in result['rows']))
    def test_degenerate_kappa(self):
        self.assertIsNone(kappa(["yes"] * 16, ["yes"] * 16)["kappa"])
    def test_perfect_nondegenerate(self):
        self.assertEqual(kappa(["yes", "no"], ["yes", "no"])["kappa"], 1)
    def test_opposite(self):
        self.assertEqual(kappa(["yes", "no"], ["no", "yes"])["kappa"], -1)
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            kappa([], [])
    def test_empty_eligibility(self):
        r = summarize([], "m")
        self.assertIsNone(r["ptr_percent"])
        self.assertIsNone(r["ctr_percent"])
        self.assertIsNone(r["b_st_percent"])
    def test_offset_and_empty_failure(self):
        row = dict(label=0, source_clean=0, source_adv=1, m_clean=1, m_adv=2)
        r = summarize([row], "m", 1)
        self.assertEqual(r["ctr_percent"], 100)
        self.assertIsNone(r["b_st_percent"])
    def test_zero_source_success(self):
        row = dict(label=0, source_clean=0, source_adv=0, m_clean=0, m_adv=1)
        r = summarize([row], "m")
        self.assertIsNone(r["ctr_percent"])
        self.assertEqual(r["b_st_percent"], 100)
    def test_archived_predictions(self):
        self.assertEqual(sum(r["verified_summaries"] for r in verify()), 27)

class EvidenceRecordTests(unittest.TestCase):
    def setUp(self):
        self.review = json.loads((Path(__file__).parent / "evidence_audit/reviews/31.json").read_text(encoding="utf-8"))
        self.paper = {"rank": 31, "paper_id": self.review["paper_id"]}

    def test_mixed_not_missing(self):
        result = aggregate_conditioning(["yes", "no", "unclear"])
        self.assertEqual(result, {"value": "unclear", "reason": "mixed_explicit", "any_explicit_yes": True})

    def test_no_vacuous_yes(self):
        self.assertEqual(aggregate_conditioning([])["reason"], "not_applicable_to_located_results")
        self.assertEqual(aggregate_conditioning(["yes", "unclear"])["value"], "unclear")

    def test_unanimous(self):
        for value in ["yes", "no"]:
            self.assertEqual(aggregate_conditioning([value, value])["value"], value)

    def test_complete_documented_review(self):
        self.assertEqual(validate_review(self.review, self.paper)["f3"]["reason"], "mixed_explicit")

    def test_all_committed_review_records(self):
        folder = Path(__file__).parent / "evidence_audit/reviews"
        for path in folder.glob("*.json"):
            with self.subTest(path=path.name):
                review = json.loads(path.read_text(encoding="utf-8"))
                validate_review(review, {"rank": int(path.stem), "paper_id": review["paper_id"]})

    def test_positive_scope_survives_unresolved_aggregation(self):
        review = json.loads((Path(__file__).parent / "evidence_audit/reviews/02.json").read_text(encoding="utf-8"))
        result = validate_review(review, {"rank": 2, "paper_id": review["paper_id"]})
        self.assertEqual(result["f2"]["value"], "unclear")
        self.assertTrue(result["f2"]["any_explicit_yes"])

    def test_missing_field_rejected(self):
        del self.review["judgments"]["f6"]
        with self.assertRaises(ValueError):
            validate_review(self.review, self.paper)

    def empty_scope_review(self):
        self.review["result_groups"] = []
        self.review["bounds_checks"] = []
        self.review["bounds_exclusion"] = {
            "status": "not_applicable_to_located_results",
            "locator": "Test fixture",
            "reason": "No original cross-model attack result in this fixture."
        }
        for judgment in self.review["judgments"].values():
            judgment.update(value="unclear", reason="not_applicable_to_located_results")

    def test_empty_scope_documented(self):
        self.empty_scope_review()
        result = validate_review(self.review, self.paper)
        self.assertEqual(result["f2"]["reason"], "not_applicable_to_located_results")

    def test_empty_scope_no_positive_or_negative_judgments(self):
        for field in [f"f{i}" for i in range(1, 7)]:
            for value in ["yes", "no"]:
                with self.subTest(field=field, value=value):
                    self.empty_scope_review()
                    self.review["judgments"][field]["value"] = value
                    with self.assertRaises(ValueError):
                        validate_review(self.review, self.paper)

    def test_empty_scope_not_missing_reporting(self):
        self.empty_scope_review()
        self.review["judgments"]["f6"]["reason"] = "release_not_found"
        with self.assertRaises(ValueError):
            validate_review(self.review, self.paper)

    def test_empty_scope_requires_bounds_exclusion(self):
        self.empty_scope_review()
        del self.review["bounds_exclusion"]
        with self.assertRaises(ValueError):
            validate_review(self.review, self.paper)

    def test_nonempty_scope_cannot_use_blanket_exclusion(self):
        self.review["bounds_exclusion"] = {"status": "not_applicable_to_located_results"}
        with self.assertRaises(ValueError):
            validate_review(self.review, self.paper)

    def test_uncovered_metric_rejected(self):
        self.review["bounds_checks"].pop()
        with self.assertRaises(ValueError):
            validate_review(self.review, self.paper)

    def test_wrong_aggregation_rejected(self):
        self.review["judgments"]["f3"]["value"] = "no"
        with self.assertRaises(ValueError):
            validate_review(self.review, self.paper)

    def test_bad_source_hash_rejected(self):
        self.review["sources"][0]["sha256"] = "not-a-hash"
        with self.assertRaises(ValueError):
            validate_review(self.review, self.paper)

    def test_empty_evidence_rejected(self):
        self.review["judgments"]["f6"]["evidence"] = " "
        with self.assertRaises(ValueError):
            validate_review(self.review, self.paper)

    def test_identity_mismatch_rejected(self):
        self.paper["rank"] = 30
        with self.assertRaises(ValueError):
            validate_review(self.review, self.paper)

if __name__ == "__main__":
    unittest.main()
