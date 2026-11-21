"""Exercise all four fits, checkpoint replay, cache debit, deadline and statistics."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np

from src.datasets import development_rows
from src.evaluate import load_selected_model, predict_rows, final_evaluation
from src.runtime import setup_cpu, sha256, write_json
from src.stats import paired_auc_difference
from src.supervise import run_training


def main():
    started = time.perf_counter()
    limiter = setup_cpu(0, 4)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    write_json(ROOT / 'docs/benchmark/smoke_report.json', {'status': 'IN_PROGRESS', 'started_utc': stamp})
    root = ROOT / 'data/cache/smoke' / stamp
    root.mkdir(parents=True)
    before = {p.name: sha256(p) for p in (ROOT / 'data/manifests').glob('*.csv')}
    records = []
    for method in ['LP', 'PFT', 'LoRA', 'CNN']:
        config = {'method': method, 'purpose': 'smoke', 'seed': 0, 'fraction': .01,
                  'threads': 4, 'cap_seconds': 180., 'max_epochs': 2, 'patience': 8,
                  'lr': .0003, 'weight_decay': .01, 'C': 1., 'image_size': 224}
        folder = root / method
        print('Smoke fit:', method, flush=True)
        record = run_training(config, folder)
        if record['peak_rss_bytes'] < 128 * 1024 ** 2 or record['process_cpu_seconds'] <= 0:
            raise RuntimeError('Supervisor failed to monitor the actual training interpreter')
        _, val = development_rows(.01, 0)
        model, linear = load_selected_model(config, record['best'], folder)
        replay, seconds = predict_rows(model, linear, val)
        if replay.image_id.tolist() != record['best']['validation_ids']:
            raise RuntimeError('Checkpoint replay ordering mismatch')
        np.testing.assert_allclose(replay.probability, record['best']['validation_probabilities'], atol=1e-6, rtol=1e-6)
        records.append({'method': method, 'status': record['status'],
                        'checkpoint_replay': 'PASS', 'threshold': record['best']['threshold'],
                        'epochs_completed': record['fit'].get('epochs_completed'),
                        'fit_seconds': record['fit'].get('charged_wall_seconds'),
                        'peak_rss_bytes': record['peak_rss_bytes'], 'replay_seconds': seconds})
        del model
        # Real external/internal evaluation must be unavailable to smoke callers.
        try:
            final_evaluation(config, record['best'], folder, root / 'forbidden')
        except ValueError:
            pass
        else:
            raise AssertionError('Smoke gained access to real test evaluation')
    print('Checking LP cache debit', flush=True)
    lp_config = json.loads((root / 'LP/config.json').read_text())
    cached = run_training(lp_config, root / 'LP_cache_reuse')
    if not cached['fit']['cache_hit'] or cached['fit']['cache_credit_seconds'] <= 0:
        raise RuntimeError('Cache reuse was not charged')
    np.testing.assert_allclose(cached['best']['validation_probabilities'],
                               json.loads((root / 'LP/best.json').read_text())['validation_probabilities'], atol=1e-12)
    print('Checking an intentionally impossible deadline', flush=True)
    capped_config = {**lp_config, 'method': 'CNN', 'cap_seconds': .01}
    try:
        run_training(capped_config, root / 'deadline_failure')
    except RuntimeError:
        capped = json.loads((root / 'deadline_failure/supervised.json').read_text())
        if capped['status'] != 'FAIL' or capped['best'] is not None or not capped['supervisor_killed_at_cap']:
            raise
    else:
        raise AssertionError('Impossible deadline unexpectedly accepted a checkpoint')
    labels = np.array([0, 0, 0, 1, 1, 1])
    predictions = np.tile([.1, .2, .3, .7, .8, .9], (3, 1))
    contrast = paired_auc_difference(labels, predictions, predictions, 2000)
    assert contrast['ci95'] == [0., 0.]
    after = {p.name: sha256(p) for p in (ROOT / 'data/manifests').glob('*.csv')}
    assert before == after, 'Smoke changed a frozen data manifest'
    assert not (root / 'forbidden').exists(), 'Smoke created a real-test output directory'
    elapsed = time.perf_counter() - started
    report = {'status': 'PASS' if elapsed < 600 else 'FAIL_RUNTIME',
              'scope': 'Development-only integration plus synthetic paired-bootstrap fixture; no held-out performance',
              'elapsed_seconds': elapsed, 'max_seconds': 600,
              'smoke_nominal_fraction': .02, 'actual_unique_training_images': 8,
              'subset_note': '2% per-class floor yields the same eight IDs as nominal 1%.',
              'seed': 0, 'records': records, 'cache_debit_check': 'PASS',
              'deadline_failure_check': 'PASS', 'real_test_access_guard': 'PASS',
              'manifest_immutability': 'PASS', 'synthetic_bootstrap': 'PASS',
              'process_tree_resource_check': 'PASS',
              'attempt_path': root.relative_to(ROOT).as_posix()}
    write_json(ROOT / 'docs/benchmark/smoke_report.json', report)
    print(json.dumps(report, indent=2), flush=True)
    if report['status'] != 'PASS':
        raise RuntimeError('Smoke exceeded ten minutes')


if __name__ == '__main__':
    main()
