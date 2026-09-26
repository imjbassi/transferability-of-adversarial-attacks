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

class Rank68BoundsTests(unittest.TestCase):
    def test_scope_and_rounding(self):
        from rank68_bounds import build
        result = build()
        self.assertEqual(result["rates_bounded"], 18)
        self.assertNotIn("VGG19", {r["target"] for r in result["rows"]})
        denoise = next(r for r in result["rows"] if r["target"] == "RNXt101den")
        self.assertAlmostEqual(denoise["nominal_induced_mass_percent"], 3.2)
        self.assertAlmostEqual(denoise["induced_mass_lower_percent"], 3.19)

class Rank38StrataTests(unittest.TestCase):
    def test_strata_and_table3(self):
        from rank38_bounds_strata import build
        s = build()["summaries"]
        self.assertEqual(s["single_target_table1"]["rates"], 72)
        self.assertEqual(s["ensemble_contains_source_table1"]["rates"], 24)
        self.assertEqual(s["single_target_all"]["rates"], 81)
        self.assertEqual(s["ensemble_contains_source_all"]["rates"], 27)
        rows = build()["rows"]
        cell = next(r for r in rows if r["attack"] == "TAP+ATA" and r["target"] == "Inception-ResNet V2")
        self.assertAlmostEqual(cell["induced_mass_lower_percent"], 79.65)

class Rank20BoundsTests(unittest.TestCase):
    def test_scope_and_exclusions(self):
        from rank20_bounds import build
        result = build()
        self.assertEqual(result["rates_bounded"], 108)
        self.assertTrue(all(r["source"] != r["target"] for r in result["rows"]))
        self.assertFalse(any("Opt" in r["attack"] or "C&W" in r["attack"] for r in result["rows"]))
        self.assertEqual(result["c_and_w_lattice_check"]["on_1_96_lattice"], 48)
        cell = next(r for r in result["rows"] if r["attack"] == "DeepFool 50 itr"
                    and r["source"] == "GoogLeNet" and r["target"] == "DenseNet121")
        self.assertAlmostEqual(cell["induced_mass_lower_percent"], 2.4)

class BoundsDistributionTests(unittest.TestCase):
    def test_pools_single_target_only(self):
        from bounds_distribution import build
        result = build()
        self.assertEqual(result["pooled_single_target"]["rates"], 108 + 81 + 18)
        self.assertEqual(result["rank38_ensemble_contains_source_not_pooled"]["rates"], 27)

class SsaRerunTests(unittest.TestCase):
    def test_metrics_recompute_from_predictions(self):
        import csv
        import math
        folder = Path(__file__).parent / "recomputation/ssa_rerun"
        seeds = sorted(p for p in folder.glob("seed*") if (p / "conditioned_metrics.json").exists())
        self.assertTrue(seeds)
        for seed in seeds:
            with (seed / "per_example_predictions.csv").open(newline="", encoding="utf-8") as handle:
                rows = [{k: int(v) for k, v in r.items() if k != "image_id"} for r in csv.DictReader(handle)]
            self.assertEqual(len(rows), 1000)
            manifest = json.loads((seed / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["attack"]["checkout"]["commit"], "c955cf07c8372bfc4e9f17e647042e027f9f3b1d")
            self.assertEqual(len(manifest["evaluate"]["target_weights"]), 9)
            for item in json.loads((seed / "conditioned_metrics.json").read_text(encoding="utf-8")):
                with self.subTest(seed=seed.name, model=item["model"]):
                    for key, value in summarize(rows, item["model"], 1).items():
                        expected = item[key]
                        self.assertTrue(value is expected if value is None or expected is None
                                        else math.isclose(value, expected, abs_tol=1e-9))

class IlaRerunTests(unittest.TestCase):
    def test_summaries_reproduce_from_release_output(self):
        import hashlib
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "recomputation" / "ila_rerun"))
        from summarize import summarize
        folder = Path(__file__).parent / "recomputation/ila_rerun"
        runs = sorted(p for p in folder.iterdir() if (p / "summary.json").exists())
        self.assertTrue(runs)
        for run in runs:
            with self.subTest(run=run.name):
                stored = json.loads((run / "summary.json").read_text(encoding="utf-8"))
                manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
                data = (run / "release_output.csv").read_bytes()  # -text in .gitattributes: bytes as produced
                self.assertEqual(hashlib.sha256(data).hexdigest(), manifest["release_output_sha256"])
                self.assertEqual(summarize(run, stored["attack"]), stored)
                self.assertEqual(stored["images"], 10000)

class SgmRerunTests(unittest.TestCase):
    def test_summary_reproduces_from_predictions(self):
        import importlib.util
        folder = Path(__file__).parent / "recomputation/sgm_rerun"
        spec = importlib.util.spec_from_file_location("sgm_run", folder / "run.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        run = folder / "run1"
        stored = json.loads((run / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(module.summarize_rows(run / "per_example_predictions.csv"), stored)
        self.assertEqual({c["images"] for c in stored["comparison"]}, {5000})
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["checkout"]["commit"], "9b2e5cca9b673efcac253e16b2f55f6cda1a8692")
        self.assertEqual({k for k in manifest if k.startswith("attack_")},
                         {"attack_rn152_pgd", "attack_rn152_sgm", "attack_dn201_pgd", "attack_dn201_sgm"})

class PnaRerunTests(unittest.TestCase):
    def test_summary_reproduces_from_predictions(self):
        import importlib.util
        folder = Path(__file__).parent / "recomputation/pna_rerun"
        spec = importlib.util.spec_from_file_location("pna_run", folder / "run.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        run = folder / "run1"
        stored = json.loads((run / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(module.summarize(run / "per_example_predictions.csv"), stored)
        self.assertEqual(stored["images"], 1000)
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["commit"], "85f23c78284556057422abe395d0e1229a13156a")
        self.assertEqual({k for k in manifest if k.startswith("attack_")},
                         {f"attack_{s}" for s in module.SURROGATES})

class TargetedTransferRerunTests(unittest.TestCase):
    def test_summary_reproduces_from_counts(self):
        import csv
        import importlib.util
        folder = Path(__file__).parent / "recomputation/tt_rerun"
        spec = importlib.util.spec_from_file_location("tt_run", folder / "run.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        run = folder / "seed0"
        counts = {}
        with (run / "success_counts.csv").open(newline="", encoding="utf-8") as handle:
            for r in csv.DictReader(handle):
                counts.setdefault(r["attack"], {})[r["target"]] = [int(r[f"iter_{20 * (i + 1)}"]) for i in range(15)]
        stored = json.loads((run / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(module.summarize(counts), stored)
        self.assertEqual(len(stored["comparison"]), 27)
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["commit"], "2e0b6d0b581a14bc43836f69b04dc431cabcd05f")

class SiaRerunTests(unittest.TestCase):
    def test_summary_and_release_eval_agree(self):
        import importlib.util
        folder = Path(__file__).parent / "recomputation/sia_rerun"
        spec = importlib.util.spec_from_file_location("sia_run", folder / "run.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        run = folder / "run1"
        stored = json.loads((run / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(module.summarize(run / "per_example_predictions.csv"), stored)
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["commit"], "6d5432d4165a85753c8ae8fdee5cfd3362509a97")
        for cfg in module.CONFIGS:
            # release --eval prints accuracies in model_list order, which equals MODELS
            release_acc = [float(v) for v in manifest[f"release_eval_{cfg}"].strip("| ").split("|")]
            ours = [c["success_percent"] for c in stored["configs"][cfg]]
            for acc, succ in zip(release_acc, ours):
                self.assertAlmostEqual(100 - acc, succ, places=6)

class ConditioningAcrossRerunsTests(unittest.TestCase):
    def test_reproducible_and_consistent(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "recomputation"))
        from conditioning_across_reruns import build
        result = build()
        stored = json.loads((Path(__file__).parent / "recomputation/conditioning_across_reruns.json").read_text(encoding="utf-8"))
        self.assertEqual(result, stored)
        for c in result["cells"]:
            self.assertEqual(c["eligible_target_wrong"], c["fooled_target_wrong"] + c["unfooled_target_wrong"])
            self.assertNotEqual(c["source"], c["target"])

class RepairedExportTests(unittest.TestCase):
    def test_export_matches_reviews_and_reliability_format(self):
        import build_repaired_coding_sheet as export
        from compute_reliability import read_rows
        reviews = export.load_reviews()
        self.assertEqual(len(reviews), 80)
        rows = read_rows(export.AUDIT / "repaired_first_pass.csv")
        by_id = {r["paper_id"]: r for r in rows}
        for entry, review, _digest, _path in reviews:
            for key, name in export.FIELDS.items():
                self.assertEqual(by_id[review["paper_id"]][name], review["judgments"][key]["value"])

if __name__ == "__main__":
    unittest.main()
