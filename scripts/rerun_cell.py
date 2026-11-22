"""Phase 7 gate: retrain one logged main cell from scratch and compare its test AUCs.

The configuration is read from the committed result and must hash identically. Training
goes to data/cache/reruns/ and evaluation uses the same `final_evaluation` entry point
with a scratch output folder, so results/ is never modified. This is a reproducibility
check of an already final run, not a selection step.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluate import final_evaluation
from src.protocol import validate_run_config
from src.runtime import config_hash, write_json
from src.supervise import run_training


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cell', default='main_LP_010_s1')
    parser.add_argument('--tolerance', type=float, default=.005)
    parser.add_argument('--cold', action='store_true',
                        help='LP only: move the cached features aside so they are re-extracted from the '
                             'images, compare them with the original arrays, then restore the original cache')
    args = parser.parse_args()
    logged = json.loads((ROOT / 'results/main' / f'{args.cell}.json').read_text())
    config = logged['config']
    validate_run_config(config)
    if config_hash(config) != logged['config_hash']:
        raise SystemExit('Logged configuration hash mismatch')
    base = ROOT / 'data/cache/reruns' / args.cell
    attempt = base / f'attempt_{len(list(base.glob("attempt_*"))) + 1:03d}' if base.exists() else base / 'attempt_001'
    cache = moved = None
    feature_check = None
    if args.cold:
        if config['method'] != 'LP':
            raise SystemExit('--cold applies to LP feature caches only')
        key = json.loads((ROOT / logged['attempt_path'] / 'run_metadata.json').read_text())['cache_key']
        cache = ROOT / 'data/cache/features' / key
        moved = cache.with_name(key + '.original')
        if moved.exists() or not cache.exists():
            raise SystemExit(f'Unexpected cache state; inspect {cache} and {moved} before retrying')
        os.replace(cache, moved)
    try:
        record = run_training(config, attempt)
        evaluation = final_evaluation(config, record['best'], attempt, attempt / 'evaluation')
        if args.cold:
            with np.load(moved / 'features.npz') as old, np.load(cache / 'features.npz') as new:
                feature_check = {name: {'identical': bool(np.array_equal(old[name], new[name])),
                                        'max_abs_difference': float(np.max(np.abs(old[name] - new[name])))}
                                 for name in ('x', 'y', 'xv', 'yv')}
            rerun_metadata = json.loads((attempt / 'run_metadata.json').read_text())
            feature_check['rerun_cache_hit'] = rerun_metadata['cache_hit']
    finally:
        if moved is not None:
            if cache.exists():
                shutil.rmtree(cache)
            os.replace(moved, cache)
    comparison = {}
    for cohort in ('internal', 'external'):
        old = logged['evaluation']['cohorts'][cohort]['metrics']['roc_auc']
        new = evaluation['cohorts'][cohort]['metrics']['roc_auc']
        comparison[cohort] = {'logged_auc': old, 'rerun_auc': new, 'abs_difference': abs(new - old),
                              'within_tolerance': abs(new - old) <= args.tolerance}
    report = {'cell': args.cell, 'tolerance': args.tolerance, 'rerun_attempt': attempt.relative_to(ROOT).as_posix(),
              'cold_feature_extraction': args.cold, 'feature_check': feature_check,
              'comparison': comparison, 'status': 'PASS' if all(c['within_tolerance'] for c in comparison.values()) else 'FAIL'}
    suffix = '_cold' if args.cold else ''
    write_json(ROOT / 'docs/reviews' / f'rerun_{args.cell}{suffix}.json', report)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
