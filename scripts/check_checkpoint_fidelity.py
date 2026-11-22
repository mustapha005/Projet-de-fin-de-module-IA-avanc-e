"""Sanity-flag investigation: reload selected checkpoints and re-predict VALIDATION only.

For each named run, the selected checkpoint is loaded through the same function that
final evaluation uses (`load_selected_model`, hash-checked, eval mode) and the validation
split (development data, via `development_rows`, which refuses held-out rows) is predicted
with the same `predict_rows`. The result must equal the validation probabilities logged at
selection time. A match rules out a save/reload or train/eval-path fault for that run;
no test data is read and nothing in results/ is modified.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from sklearn.metrics import roc_auc_score
import torch

from src.datasets import development_rows
from src.evaluate import load_selected_model, predict_rows
from src.runtime import write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', nargs='+', help='result names, e.g. main_CNN_010_s2')
    parser.add_argument('--out', default='docs/reviews/checkpoint_fidelity.json')
    args = parser.parse_args()
    torch.set_num_threads(4)
    report = {}
    for name in args.runs:
        phase = 'main' if name.startswith('main_') else 'ablation'
        run = json.loads((ROOT / 'results' / phase / f'{name}.json').read_text())
        config, best = run['config'], run['fit']['best']
        _, val = development_rows(config['fraction'], config['seed'])
        if list(val.image_id) != best['validation_ids']:
            raise ValueError(f'{name}: validation identities differ from the logged order')
        model, linear = load_selected_model(config, best, ROOT / run['attempt_path'])
        predictions, _ = predict_rows(model, linear, val, config.get('image_size', 224))
        logged = np.asarray(best['validation_probabilities'])
        difference = float(np.max(np.abs(predictions.probability.to_numpy() - logged)))
        report[name] = {'max_abs_probability_difference': difference,
                        'logged_validation_auc': best['validation_auc'],
                        'recomputed_validation_auc': float(roc_auc_score(predictions.label, predictions.probability)),
                        'match': difference <= 1e-6}
        print(name, json.dumps(report[name]))
    status = 'PASS' if all(r['match'] for r in report.values()) else 'FAIL'
    write_json(ROOT / args.out, {'status': status, 'purpose': __doc__.splitlines()[0], 'runs': report})
    print(status)
    sys.exit(0 if status == 'PASS' else 1)


if __name__ == '__main__':
    main()
