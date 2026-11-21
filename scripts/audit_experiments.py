"""Audit completed main predictions and report an incomplete grid honestly."""
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from src.protocol import verify_frozen
from src.runtime import sha256, write_json
from src.stats import choose_threshold, metrics


def main():
    contract = verify_frozen()
    tag_time = datetime.fromisoformat(subprocess.check_output(
        ['git', 'show', '-s', '--format=%cI', 'protocol-frozen'], cwd=ROOT, text=True).strip())
    expected = {(m, f, s) for m in ['LP', 'PFT', 'LoRA', 'CNN']
                for f in contract['fractions'] for s in contract['seeds']}
    found, pairings, flags, seed_metrics = set(), {}, [], {}
    for path in sorted((ROOT / 'results/main').glob('*.json')):
        run = json.loads(path.read_text())
        config = run['config']
        cell = (config['method'], config['fraction'], config['seed'])
        if cell not in expected or cell in found:
            raise ValueError('Unknown or duplicate main-grid cell')
        found.add(cell)
        assert datetime.fromisoformat(run['completed_utc']) > tag_time
        fit = run['fit']
        assert fit['status'] == 'PASS'
        assert fit['fit']['parameters']['trainable'] > 0
        assert fit['peak_rss_bytes'] > 128 * 1024 ** 2
        assert fit['best']['charged_seconds_at_selection'] < contract['cap_seconds']
        threshold = choose_threshold(fit['best']['validation_labels'], fit['best']['validation_probabilities'])
        assert threshold == fit['best']['threshold'] == run['evaluation']['threshold']
        for cohort, evidence in run['evaluation']['cohorts'].items():
            predictions_path = ROOT / run['prediction_folder'] / evidence['predictions_file']
            assert sha256(predictions_path) == evidence['predictions_sha256']
            predictions = pd.read_csv(predictions_path, float_precision='round_trip')
            assert not predictions.image_id.duplicated().any()
            identity = list(zip(predictions.image_id, predictions.label.astype(int)))
            if cohort in pairings:
                assert identity == pairings[cohort], 'Unpaired test identities/labels'
            pairings[cohort] = identity
            actual = metrics(predictions.label, predictions.probability, threshold)
            for metric, value in actual.items():
                assert np.isclose(value, evidence['metrics'][metric], atol=1e-12, rtol=0), metric
            seed_metrics.setdefault((config['method'], config['fraction'], cohort), []).append(actual['roc_auc'])
            auc = actual['roc_auc']
            if auc >= .98 or abs(auc - .5) <= .02:
                flags.append({'run': path.stem, 'cohort': cohort, 'auc': auc,
                              'reason': 'Near-perfect or near-chance AUC; investigate implementation before interpretation, not retuning.'})
        if run['auc_gap'] < 0:
            flags.append({'run': path.stem, 'reason': 'External AUC exceeds internal AUC; review case mix, uncertainty and code.'})
    for key, values in seed_metrics.items():
        if len(values) == 3 and len(set(values)) == 1:
            flags.append({'method_fraction_cohort': list(key),
                          'reason': 'Identical AUC across seeds; inspect predictions and run seeds before interpretation.'})
    report = {'status': 'PASS' if found == expected else 'INCOMPLETE',
              'expected_main_cells': 36, 'completed_main_cells': len(found),
              'missing': [list(x) for x in sorted(expected - found)],
              'checks_applied_to_completed_cells': len(found),
              'recomputed_saved_metrics': bool(found), 'paired_test_identities': bool(found),
              'selection_threshold_and_deadline_checks': bool(found), 'sanity_flags': flags,
              'flags_policy': 'Flags require investigation, not deletion or performance-driven protocol changes.'}
    write_json(ROOT / 'docs/reviews/main_grid_audit.json', report)
    print(json.dumps({k: v for k, v in report.items() if k not in {'missing', 'sanity_flags'}}, indent=2))


if __name__ == '__main__':
    main()
