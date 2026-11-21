"""Phase 4 gate: recompute random main-table cells from raw prediction CSVs.

Deliberately independent of src/analysis: it parses results JSON and prediction
files directly and uses scikit-learn's AUC, then compares with tables/main_results.csv.
"""
import argparse
import json
from pathlib import Path
import random

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
FRACTION_LABEL = {0.01: '1%', 0.1: '10%', 1.0: '100%'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--seed', type=int, required=True, help='Recorded so the check can be repeated')
    parser.add_argument('--cells', type=int, default=3)
    args = parser.parse_args()
    table = pd.read_csv(args.root / 'tables/main_results.csv')
    runs = [json.loads(p.read_text()) for p in sorted((args.root / 'results/main').glob('*.json'))]
    rng = random.Random(args.seed)
    picks = rng.sample([(m, f, c) for m in ['LP', 'PFT', 'LoRA', 'CNN'] for f in FRACTION_LABEL
                        for c in ('internal', 'external')], args.cells)
    report = []
    for method, fraction, cohort in picks:
        aucs = []
        for run in sorted((r for r in runs if r['config']['method'] == method
                           and abs(r['config']['fraction'] - fraction) < 1e-9), key=lambda r: r['config']['seed']):
            frame = pd.read_csv(args.root / run['prediction_folder'] / f'{cohort}_predictions.csv')
            aucs.append(roc_auc_score(frame.label, frame.probability))
        recomputed = f'{np.mean(aucs):.3f} ± {np.std(aucs, ddof=1):.3f}'
        row = table[(table.Method == method) & table.Labels.str.startswith(FRACTION_LABEL[fraction] + ' ')]
        column = 'AUC_in' if cohort == 'internal' else 'AUC_out'
        tabled = row[column].iloc[0]
        report.append({'method': method, 'fraction': fraction, 'cohort': cohort, 'per_seed_auc': aucs,
                       'recomputed': recomputed, 'table': tabled, 'match': recomputed == tabled})
    print(json.dumps({'seed': args.seed, 'all_match': all(r['match'] for r in report), 'cells': report}, indent=2))
    if not all(r['match'] for r in report):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
