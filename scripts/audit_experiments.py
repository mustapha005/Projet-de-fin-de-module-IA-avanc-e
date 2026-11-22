"""Audit completed main or ablation predictions and report an incomplete grid honestly.

`--phase main` (default) writes docs/reviews/main_grid_audit.json; `--phase ablation`
applies the same per-run checks to the 21 pre-registered ablation cells and also requires
their test identities to match the main grid, writing docs/reviews/ablation_audit.json.
"""
import argparse
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

# Mirrors the variant list in scripts/run_experiments.py (pre-registered in docs/PROTOCOL.md).
ABLATIONS = [('lora_last2', 'LoRA', 'all'), ('lora_rank4', 'LoRA', 'ten'), ('lora_rank16', 'LoRA', 'ten'),
             ('pft_depth4', 'PFT', 'ten'), ('lora_no_augmentation', 'LoRA', 'ten')]


def expected_cells(phase, contract):
    if phase == 'main':
        return {('main', m, f, s) for m in ['LP', 'PFT', 'LoRA', 'CNN']
                for f in contract['fractions'] for s in contract['seeds']}
    return {(variant, method, f, s) for variant, method, scope in ABLATIONS
            for f in (contract['fractions'] if scope == 'all' else [.1]) for s in contract['seeds']}


def check_run(path, run, contract, tag_time, pairings, flags, seed_metrics):
    config = run['config']
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
        key = (config.get('ablation_name', 'main'), config['method'], config['fraction'], cohort)
        seed_metrics.setdefault(key, []).append(actual['roc_auc'])
        auc = actual['roc_auc']
        if auc >= .98 or abs(auc - .5) <= .02:
            flags.append({'run': path.stem, 'cohort': cohort, 'auc': auc,
                          'reason': 'Near-perfect or near-chance AUC; investigate implementation before interpretation, not retuning.'})
    if run['auc_gap'] < 0:
        flags.append({'run': path.stem, 'reason': 'External AUC exceeds internal AUC; review case mix, uncertainty and code.'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['main', 'ablation'], default='main')
    args = parser.parse_args()
    contract = verify_frozen()
    tag_time = datetime.fromisoformat(subprocess.check_output(
        ['git', 'show', '-s', '--format=%cI', 'protocol-frozen'], cwd=ROOT, text=True).strip())
    expected = expected_cells(args.phase, contract)
    found, pairings, flags, seed_metrics = set(), {}, [], {}
    if args.phase == 'ablation':
        # Ablation test identities must equal the main grid's (one main file fixes the reference).
        reference = json.loads(next(iter(sorted((ROOT / 'results/main').glob('*.json')))).read_text())
        for cohort, evidence in reference['evaluation']['cohorts'].items():
            frame = pd.read_csv(ROOT / reference['prediction_folder'] / evidence['predictions_file'])
            pairings[cohort] = list(zip(frame.image_id, frame.label.astype(int)))
    for path in sorted((ROOT / 'results' / args.phase).glob('*.json')):
        run = json.loads(path.read_text())
        config = run['config']
        assert config['purpose'] == args.phase
        cell = (config.get('ablation_name', 'main'), config['method'], config['fraction'], config['seed'])
        if cell not in expected or cell in found:
            raise ValueError(f'Unknown or duplicate {args.phase} cell: {cell}')
        found.add(cell)
        check_run(path, run, contract, tag_time, pairings, flags, seed_metrics)
    for key, values in seed_metrics.items():
        if len(values) == 3 and len(set(values)) == 1:
            flags.append({'variant_method_fraction_cohort': list(key),
                          'reason': 'Identical AUC across seeds; inspect predictions and run seeds before interpretation.'})
    report = {'status': 'PASS' if found == expected else 'INCOMPLETE', 'phase': args.phase,
              f'expected_{args.phase}_cells': len(expected), f'completed_{args.phase}_cells': len(found),
              'missing': [list(x) for x in sorted(expected - found)],
              'checks_applied_to_completed_cells': len(found),
              'recomputed_saved_metrics': bool(found), 'paired_test_identities': bool(found),
              'selection_threshold_and_deadline_checks': bool(found), 'sanity_flags': flags,
              'flags_policy': 'Flags require investigation, not deletion or performance-driven protocol changes.'}
    name = 'main_grid_audit.json' if args.phase == 'main' else 'ablation_audit.json'
    write_json(ROOT / 'docs/reviews' / name, report)
    print(json.dumps({k: v for k, v in report.items() if k not in {'missing', 'sanity_flags'}}, indent=2))
    print('sanity_flags:', len(flags))


if __name__ == '__main__':
    main()
