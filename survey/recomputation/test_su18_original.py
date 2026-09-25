"""Check archived selected-run integrity and metrics without legacy TensorFlow."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from transferlab.metrics import summarize, binomial


class OriginalRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = Path(__file__).with_name('su18_original')
        cls.manifest = json.loads((cls.folder / 'manifest.json').read_text())
        cls.rows = [json.loads(line) for line in (cls.folder / 'predictions.jsonl').read_text().splitlines()]

    def test_integrity_and_cohort(self):
        m = self.manifest
        self.assertEqual(hashlib.sha256((self.folder / 'predictions.jsonl').read_bytes()).hexdigest(), m['predictions_sha256'])
        self.assertEqual(hashlib.sha256(Path(__file__).with_name('su18_original_probe.py').read_bytes()).hexdigest(), m['harness_sha256'])
        selected = m['selected_image_ids']
        processed = [r['image_id'] for r in self.rows]
        skipped = [r['image_id'] for r in m['skipped']]
        self.assertEqual(len(selected), 1000)
        self.assertEqual(len(set(selected)), 1000)
        self.assertEqual(len(processed), 692)
        self.assertEqual(len(set(processed + skipped)), 1000)
        self.assertCountEqual(selected, processed + skipped)
        self.assertTrue(all(r['source_clean'] == r['label'] for r in self.rows))
        self.assertTrue(all(0 <= r['linf'] <= m['epsilon'] + 1e-6 for r in self.rows))

    def test_metrics_and_identity(self):
        actual = summarize(self.rows)
        eligible = [r for r in self.rows if r['target_clean'] == r['label']]
        successes = [r for r in eligible if r['source_adv'] != r['label']]
        failures = [r for r in eligible if r['source_adv'] == r['label']]
        actual['a_st'] = binomial(len(successes), len(eligible))
        actual['b_st'] = binomial(sum(r['target_adv'] != r['label'] for r in failures), len(failures))
        self.assertEqual(actual, self.manifest['metrics'])
        for name, counts in [('pair_transfer', (345, 645)), ('conditional_transfer', (334, 539)), ('a_st', (539, 645)), ('b_st', (11, 106))]:
            self.assertEqual((actual[name]['successes'], actual[name]['total']), counts)
        a, b = actual['a_st']['rate'], actual['b_st']['rate']
        self.assertAlmostEqual(actual['pair_transfer']['rate'], a * actual['conditional_transfer']['rate'] + (1-a) * b)


if __name__ == '__main__':
    unittest.main()
