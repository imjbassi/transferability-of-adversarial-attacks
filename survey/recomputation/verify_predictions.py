"""Independently verify all archived counts/rates, including SSA label spaces.

Run from any directory with Python's standard library; no models or GPU needed.
This verifies arithmetic, not equivalence to published attack implementations.
"""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def summarize(rows, model, target_offset=0):
    eligible = [r for r in rows if r['source_clean'] == r['label']
                and r[model + '_clean'] == r['label'] + target_offset]
    success = [r for r in eligible if r['source_adv'] != r['label']]
    failures = [r for r in eligible if r['source_adv'] == r['label']]
    wrong = lambda r: r[model + '_adv'] != r['label'] + target_offset
    e, f = len(eligible), len(success)
    g, h, j = sum(map(wrong, eligible)), sum(map(wrong, success)), sum(map(wrong, failures))
    rate = lambda numerator, denominator: 100 * numerator / denominator if denominator else None
    assert g == h + j
    return dict(n=len(rows), eligible_count=e, source_success_count=f,
                target_error_count=g, joint_success_count=h,
                failed_source_target_error_count=j,
                unconditional_attacked_error_percent=rate(sum(map(wrong, rows)), len(rows)),
                ptr_percent=rate(g, e), ctr_percent=rate(h, f),
                a_st_percent=rate(f, e), b_st_percent=rate(j, e - f))


def verify():
    report = []
    for prefix, offset in [('si_ni', 0), ('vmi', 0), ('ssa', 1)]:
        with (ROOT / f'{prefix}_per_example_predictions.csv').open(newline='', encoding='utf-8') as handle:
            raw = list(csv.DictReader(handle))
        if len(raw) != 1000 or len({r['image_id'] for r in raw}) != 1000:
            raise ValueError(f'{prefix}: expected 1000 unique images')
        rows = [{k: int(v) for k, v in r.items() if k != 'image_id'} for r in raw]
        metrics = json.loads((ROOT / f'{prefix}_conditioned_metrics.json').read_text())
        for item in metrics:
            actual = summarize(rows, item['model'], offset)
            for key, value in actual.items():
                expected = item[key]
                if value is None or expected is None:
                    valid = value is expected
                else:
                    valid = math.isclose(value, expected, abs_tol=1e-9)
                if not valid:
                    raise ValueError(f'{prefix}/{item["model"]}/{key}: {value} != {expected}')
        report.append(dict(run=prefix, images=len(rows), verified_summaries=len(metrics),
                           target_label_offset=offset))
    return report


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
