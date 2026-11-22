"""Gallery diagnostic: how similar are LP/PFT/LoRA attention rollouts? Validation images only.

The failure gallery (D013) shows CLS attention rollout for the three DINOv2 variants. This
check quantifies, on the first N validation images, the similarity of their rollout maps
and of their last-layer CLS attention, using the same seed-0, nominal-100% checkpoints as
the gallery. It is descriptive evidence for the figure caption; it reads no test data.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from src.analysis.error_analysis import rollout
from src.datasets import Images, development_rows
from src.evaluate import load_selected_model
from src.runtime import write_json

PAIRS = [('LP', 'PFT'), ('LP', 'LoRA'), ('PFT', 'LoRA')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images', type=int, default=10)
    args = parser.parse_args()
    torch.set_num_threads(4)
    _, val = development_rows(1.0, 0)
    images = Images(val.iloc[:args.images].reset_index(drop=True))
    models = {}
    for method in ['LP', 'PFT', 'LoRA']:
        run = json.loads((ROOT / f'results/main/main_{method}_100_s0.json').read_text())
        models[method] = load_selected_model(run['config'], run['fit']['best'], ROOT / run['attempt_path'])[0]
    rows = {f'{a}_vs_{b}': {'rollout_corr': [], 'last_layer_corr': []} for a, b in PAIRS}
    for i in range(len(images)):
        pixels = images[i][0][None]
        maps, last = {}, {}
        for method, model in models.items():
            maps[method] = rollout(model, pixels).ravel()
            with torch.no_grad():
                attention = model.backbone(pixel_values=pixels, output_attentions=True).attentions
            last[method] = attention[-1][0].mean(0)[0, 1:].numpy()
        for a, b in PAIRS:
            rows[f'{a}_vs_{b}']['rollout_corr'].append(float(np.corrcoef(maps[a], maps[b])[0, 1]))
            rows[f'{a}_vs_{b}']['last_layer_corr'].append(float(np.corrcoef(last[a], last[b])[0, 1]))
    summary = {pair: {key: {'min': min(v), 'median': float(np.median(v)), 'max': max(v)} for key, v in values.items()}
               for pair, values in rows.items()}
    report = {'images': f'first {len(images)} validation images (sorted image_id)',
              'checkpoints': 'seed 0, nominal 100%, as in the gallery', 'per_pair': summary, 'raw': rows}
    write_json(ROOT / 'docs/reviews/rollout_similarity.json', report)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
