"""Dependency-free boundary tests; no model execution."""
import unittest
from compute_reliability import kappa
from count_reconstruction import count_candidates
from rounding_bounds import bounds, build, interval
from recomputation.verify_predictions import summarize, verify

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

if __name__ == "__main__":
    unittest.main()
