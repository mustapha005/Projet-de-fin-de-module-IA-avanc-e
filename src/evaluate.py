"""Checkpoint inference; real held-out cohorts are accessed only by final_evaluation."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np
import pandas as pd
from scipy.special import expit
import torch

from src.datasets import Images, loader
from src.models import build_model
from src.runtime import ROOT, sha256, write_json
from src.stats import metrics


def load_selected_model(config, best, folder):
    path = folder / best['checkpoint']
    if path.parent.resolve() != folder.resolve() or sha256(path) != best['checkpoint_sha256']:
        raise ValueError('Selected checkpoint hash/path mismatch')
    options = {k: config[k] for k in ('depth', 'rank', 'lora_depth') if k in config}
    model = build_model(config['method'], **options)
    linear = None
    if config['method'] == 'LP':
        linear = json.loads(path.read_text())
        if linear['classes'] != [0, 1]:
            raise ValueError('Unexpected logistic class ordering')
    else:
        model.load_state_dict(torch.load(path, map_location='cpu', weights_only=True), strict=True)
    return model.eval(), linear


def predict_rows(model, linear, rows, size=224):
    """No selection or threshold changes; caller supplies the already eligible rows."""
    result = []
    started = time.perf_counter()
    with torch.no_grad():
        for pixels, labels, ids in loader(Images(rows, size=size)):
            output = model(pixels)
            probabilities = (expit(output.numpy() @ np.asarray(linear['coef']).T +
                                   np.asarray(linear['intercept'])).ravel()
                             if linear is not None else output.softmax(dim=1)[:, 1].numpy())
            result.extend({'image_id': image_id, 'label': int(label), 'probability': float(probability)}
                          for image_id, label, probability in zip(ids, labels, probabilities))
    return pd.DataFrame(result), time.perf_counter() - started


def final_evaluation(config, best, folder: Path, output: Path):
    """One selected-run transaction. Interrupted uncommitted inference fails closed."""
    if config.get('purpose') not in {'main', 'ablation'}:
        raise ValueError('Only selected final main/ablation runs may access real tests')
    from src.protocol import validate_run_config
    validate_run_config(config)
    tag = subprocess.run(['git', 'rev-parse', '--verify', 'refs/tags/protocol-frozen'],
                         cwd=ROOT, capture_output=True, text=True)
    if tag.returncode:
        raise RuntimeError('Final evaluation requires protocol-frozen')
    output.mkdir(parents=True, exist_ok=True)
    receipt = output / 'evaluation.json'
    if receipt.exists():
        result = json.loads(receipt.read_text())
        if result['checkpoint_sha256'] != best['checkpoint_sha256']:
            raise RuntimeError('Attempt to replace an already evaluated checkpoint')
        for name, record in result['cohorts'].items():
            if sha256(output / record['predictions_file']) != record['predictions_sha256']:
                raise RuntimeError('Saved test predictions changed')
        return result
    lock = output / 'evaluation_started.json'
    with lock.open('x', encoding='utf-8') as stream:
        json.dump({'started_utc': datetime.now(timezone.utc).isoformat(),
                   'checkpoint_sha256': best['checkpoint_sha256'],
                   'frozen_commit': tag.stdout.strip()}, stream)
    # This is deliberately the only model-evaluation entry point loading holdouts.
    internal = pd.read_csv(ROOT / 'data/manifests/busi_splits.csv', dtype={'phash': str})
    internal = internal[internal.split == 'test'].sort_values('image_id')
    external = pd.read_csv(ROOT / 'data/manifests/breast_external.csv', dtype={'phash': str}).sort_values('image_id')
    model, linear = load_selected_model(config, best, folder)
    result = {'checkpoint_sha256': best['checkpoint_sha256'], 'threshold': best['threshold'],
              'frozen_commit': tag.stdout.strip(), 'cohorts': {}}
    for name, rows in [('internal', internal), ('external', external)]:
        for row in rows.to_dict('records'):
            if sha256(ROOT / row['path']) != row['sha256']:
                raise RuntimeError('Held-out image checksum mismatch: ' + row['image_id'])
        predictions, seconds = predict_rows(model, linear, rows, config.get('image_size', 224))
        path = output / f'{name}_predictions.csv'
        temporary = path.with_suffix('.csv.tmp')
        temporary.write_text(predictions.to_csv(index=False, lineterminator='\n', float_format='%.17g'),
                             encoding='utf-8', newline='\n')
        os.replace(temporary, path)
        result['cohorts'][name] = {'predictions_file': path.name, 'predictions_sha256': sha256(path),
                                   'n_images': len(predictions), 'inference_seconds': seconds,
                                   'inference_seconds_per_image': seconds / len(predictions),
                                   'metrics': metrics(predictions.label, predictions.probability, best['threshold'])}
    write_json(receipt, result)
    return result
