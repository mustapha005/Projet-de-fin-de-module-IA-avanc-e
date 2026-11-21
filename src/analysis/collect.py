"""Load final run records and their saved predictions, verifying every hash."""
from pathlib import Path
import json

import numpy as np
import pandas as pd

from src.runtime import sha256

METHODS = ['LP', 'PFT', 'LoRA', 'CNN']
FM_METHODS = ['LP', 'PFT', 'LoRA']
FRACTIONS = [.01, .1, 1.]
SEEDS = [0, 1, 2]
COHORTS = ['internal', 'external']


def load_runs(root: Path, purpose: str = 'main') -> list[dict]:
    """Read every final record of one purpose; duplicates or failures are errors."""
    runs, seen = [], set()
    for path in sorted((root / 'results' / purpose).glob('*.json')):
        run = json.loads(path.read_text())
        if run.get('status') != 'PASS':
            raise ValueError(f'Non-PASS final record: {path.name}')
        config = run['config']
        key = (config.get('ablation_name', 'main'), config['method'], config['fraction'], config['seed'])
        if key in seen:
            raise ValueError(f'Duplicate final cell: {key}')
        seen.add(key)
        run['_path'] = path
        runs.append(run)
    return runs


def predictions(root: Path, run: dict, cohort: str) -> pd.DataFrame:
    """Saved per-image predictions, rejected if their recorded hash changed."""
    evidence = run['evaluation']['cohorts'][cohort]
    path = root / run['prediction_folder'] / evidence['predictions_file']
    if sha256(path) != evidence['predictions_sha256']:
        raise ValueError(f'Prediction hash mismatch: {path}')
    frame = pd.read_csv(path, float_precision='round_trip')
    if frame.image_id.duplicated().any():
        raise ValueError(f'Repeated image in {path}')
    return frame.sort_values('image_id').reset_index(drop=True)


def select(runs: list[dict], method: str, fraction: float, variant: str = 'main') -> list[dict]:
    """The three seed runs of one cell, ordered by seed; incomplete cells raise."""
    chosen = {r['config']['seed']: r for r in runs
              if r['config']['method'] == method and np.isclose(r['config']['fraction'], fraction)
              and r['config'].get('ablation_name', 'main') == variant}
    if sorted(chosen) != SEEDS:
        raise ValueError(f'Incomplete cell {variant}/{method}/{fraction}: seeds {sorted(chosen)}')
    return [chosen[s] for s in SEEDS]


def aligned(root: Path, cell_runs: list[dict], cohort: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Labels (images,), probabilities (seeds, images) and IDs, paired across seeds."""
    frames = [predictions(root, run, cohort) for run in cell_runs]
    ids = frames[0].image_id.tolist()
    labels = frames[0].label.to_numpy(int)
    for frame in frames[1:]:
        if frame.image_id.tolist() != ids or not np.array_equal(frame.label.to_numpy(int), labels):
            raise ValueError('Seeds do not share identical test images and labels')
    return labels, np.vstack([f.probability.to_numpy(float) for f in frames]), ids


def run_frame(runs: list[dict]) -> pd.DataFrame:
    """One row per final run with metrics, cost and stopping evidence."""
    rows = []
    for run in runs:
        config, supervised = run['config'], run['fit']
        inner, best = supervised['fit'], supervised['best']
        cohorts = run['evaluation']['cohorts']
        row = {'variant': config.get('ablation_name', 'main'), 'method': config['method'],
               'fraction': config['fraction'], 'seed': config['seed'],
               'n_train': inner.get('n_train'), 'trainable_parameters': inner['parameters']['trainable'],
               'total_parameters': inner['parameters']['total'],
               'stop_reason': inner.get('stop_reason'), 'epochs_completed': inner.get('epochs_completed'),
               'cap_hit': bool(supervised['supervisor_killed_at_cap'] or inner.get('stop_reason') == 'time_cap'),
               'charged_seconds': inner.get('charged_wall_seconds'),
               'time_to_best_seconds': best['charged_seconds_at_selection'],
               'best_epoch': best.get('epoch'), 'validation_auc': best['validation_auc'],
               'threshold': run['evaluation']['threshold'],
               'process_cpu_seconds': supervised['process_cpu_seconds'],
               'peak_rss_bytes': supervised['peak_rss_bytes'],
               'cache_hit': inner.get('cache_hit'), 'cache_credit_seconds': inner.get('cache_credit_seconds'),
               'auc_gap': run['auc_gap']}
        for cohort in COHORTS:
            evidence = cohorts[cohort]
            for metric, value in evidence['metrics'].items():
                row[f'{metric}_{cohort}'] = value
            row[f'inference_ms_per_image_{cohort}'] = 1000 * evidence['inference_seconds_per_image']
        rows.append(row)
    return pd.DataFrame(rows).sort_values(['variant', 'method', 'fraction', 'seed']).reset_index(drop=True)
