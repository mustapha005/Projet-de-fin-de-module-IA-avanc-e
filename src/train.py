"""Train on development data with charged cache costs and atomic selection evidence."""
import argparse
import json
import math
import os
from pathlib import Path
import time
import warnings

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import torch

from src.datasets import Images, development_rows, loader
from src.models import build_model, parameter_counts
from src.runtime import ROOT, config_hash, sha256, setup_cpu, write_json
from src.stats import choose_threshold


class BudgetExpired(RuntimeError):
    pass


class Budget:
    def __init__(self, folder: Path, seconds: float):
        self.folder, self.limit, self.credit = folder, seconds, 0.
        self.started = time.perf_counter()
        write_json(folder / 'budget.json', {'started_monotonic': self.started,
                                           'seconds': seconds, 'credit_seconds': 0.})

    def elapsed(self):
        return time.perf_counter() - self.started + self.credit

    def check(self):
        if self.elapsed() >= self.limit:
            raise BudgetExpired('Common charged wall-clock cap reached')

    def debit_cache(self, seconds):
        self.credit += seconds
        write_json(self.folder / 'budget.json', {'started_monotonic': self.started,
                                                'seconds': self.limit, 'credit_seconds': self.credit})
        self.check()


def lr_multiplier(step: int, steps_per_epoch: int, epochs: int) -> float:
    """Linear one-epoch warmup; the last optimizer step receives zero cosine LR."""
    if step < steps_per_epoch:
        return (step + 1) / steps_per_epoch
    remaining = max(1, (epochs - 1) * steps_per_epoch)
    progress = min(1., (step - steps_per_epoch + 1) / remaining)
    return .5 * (1 + math.cos(math.pi * progress))


def predict_development(model, data_loader, budget):
    model.eval()
    probabilities, labels, ids = [], [], []
    with torch.no_grad():
        for pixels, target, image_ids in data_loader:
            budget.check()
            probabilities.extend(model(pixels).softmax(dim=1)[:, 1].tolist())
            labels.extend(target.tolist())
            ids.extend(image_ids)
    budget.check()
    return np.array(probabilities), np.array(labels), ids


def publish_best(model, folder, epoch, probabilities, labels, ids, auc, budget):
    """Commit selection metadata only after its referenced checkpoint is complete."""
    threshold = choose_threshold(labels, probabilities)
    budget.check()
    path = folder / f'checkpoint_epoch_{epoch:03d}.pt'
    temporary = path.with_suffix('.pt.tmp')
    torch.save(model.state_dict(), temporary)
    os.replace(temporary, path)
    digest = sha256(path)
    budget.check()
    previous = json.loads((folder / 'best.json').read_text()) if (folder / 'best.json').exists() else None
    best = {'epoch': epoch, 'validation_auc': float(auc), 'threshold': threshold,
            'validation_ids': ids, 'validation_labels': labels.tolist(),
            'validation_probabilities': probabilities.tolist(),
            'checkpoint': path.name, 'checkpoint_sha256': digest,
            'charged_seconds_at_selection': budget.elapsed()}
    write_json(folder / 'best.json', best)
    if previous and previous['checkpoint'] != path.name:
        old = folder / previous['checkpoint']
        if old.parent.resolve() == folder.resolve() and old.exists():
            old.unlink()
    return best


def fit_neural(config, train, val, folder, budget):
    options = {k: config[k] for k in ('depth', 'rank', 'lora_depth') if k in config}
    model = build_model(config['method'], **options)
    params = parameter_counts(model)
    write_json(folder / 'run_metadata.json', {'parameters': params,
                'target_modules': getattr(model, 'target_modules', []),
                'n_train': len(train), 'n_validation': len(val), 'cache_hit': False})
    training = Images(train, training=config.get('augmentation', True), seed=config['seed'],
                      size=config.get('image_size', 224))
    validation = Images(val, size=config.get('image_size', 224))
    train_loader = loader(training, shuffle=True, seed=config['seed'])
    val_loader = loader(validation)
    weights = torch.tensor(len(train) / (2 * np.bincount(train.label, minlength=2)), dtype=torch.float32)
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                  lr=config['lr'], weight_decay=config['weight_decay'])
    best_auc, stale, best = -math.inf, 0, None
    history, reason, step = [], 'epoch_limit', 0
    try:
        for epoch in range(config['max_epochs']):
            budget.check()
            training.epoch = epoch
            model.train()
            epoch_start = budget.elapsed()
            losses = []
            for pixels, labels, _ in train_loader:
                budget.check()
                for group in optimizer.param_groups:
                    group['lr'] = config['lr'] * lr_multiplier(step, len(train_loader), config['max_epochs'])
                optimizer.zero_grad(set_to_none=True)
                loss = torch.nn.functional.cross_entropy(model(pixels), labels, weight=weights)
                if not torch.isfinite(loss):
                    raise RuntimeError('Non-finite training loss')
                loss.backward()
                budget.check()
                optimizer.step()
                losses.append((float(loss.detach()), len(labels)))
                step += 1
            probabilities, labels, ids = predict_development(model, val_loader, budget)
            auc = float(roc_auc_score(labels, probabilities))
            if auc > best_auc + 1e-12:
                best = publish_best(model, folder, epoch + 1, probabilities, labels, ids, auc, budget)
                best_auc, stale = auc, 0
            else:
                stale += 1
            history.append({'epoch': epoch + 1, 'validation_auc': auc,
                            'weighted_loss_batch_mean': sum(a * n for a, n in losses) / sum(n for _, n in losses),
                            'seconds': budget.elapsed() - epoch_start,
                            'learning_rate_last_step': optimizer.param_groups[0]['lr']})
            write_json(folder / 'history.json', {'epochs': history})
            print(config['method'], 'epoch', epoch + 1, 'completed', flush=True)
            if stale >= config['patience']:
                reason = 'early_stopping'
                break
    except BudgetExpired:
        reason = 'time_cap'
    return {'parameters': params, 'target_modules': getattr(model, 'target_modules', []),
            'epochs_completed': len(history), 'stop_reason': reason, 'best': best,
            'cache_hit': False, 'cache_credit_seconds': 0.}


def _extract(model, data_loader, budget):
    features, labels, ids = [], [], []
    with torch.no_grad():
        for pixels, target, image_ids in data_loader:
            budget.check()
            features.append(model(pixels).numpy())
            labels.extend(target.tolist())
            ids.extend(image_ids)
    budget.check()
    return np.concatenate(features), np.array(labels), ids


def fit_lp(config, train, val, folder, budget):
    pin = json.loads((ROOT / 'configs/backbone.json').read_text())
    key = config_hash({'train': train[['image_id', 'sha256', 'label']].to_dict('records'),
                       'val': val[['image_id', 'sha256', 'label']].to_dict('records'),
                       'seed': config['seed'], 'views': 4, 'image_size': config.get('image_size', 224),
                       'backbone': pin, 'transform_code': sha256(ROOT / 'src/datasets.py'),
                       'model_code': sha256(ROOT / 'src/models.py'),
                       'environment': sha256(ROOT / 'requirements.lock')})
    cache = ROOT / 'data/cache/features' / key
    metadata_path, features_path = cache / 'metadata.json', cache / 'features.npz'
    hit = metadata_path.exists() and features_path.exists()
    if hit:
        metadata = json.loads(metadata_path.read_text())
        if metadata['key'] != key or sha256(features_path) != metadata['features_sha256']:
            raise RuntimeError('Corrupt feature cache')
        budget.debit_cache(metadata['cold_setup_seconds'])
        with np.load(features_path, allow_pickle=False) as arrays:
            x, y, xv, yv = [arrays[k].copy() for k in ('x', 'y', 'xv', 'yv')]
    else:
        started = time.perf_counter()
        model = build_model('LP').eval()
        x, y, _ = _extract(model, loader(Images(train, training=True, seed=config['seed'], views=4)), budget)
        xv, yv, val_ids = _extract(model, loader(Images(val)), budget)
        cold_setup = time.perf_counter() - started
        cache.mkdir(parents=True, exist_ok=True)
        temporary = cache / 'features.tmp'
        with temporary.open('wb') as stream:
            np.savez_compressed(stream, x=x, y=y, xv=xv, yv=yv)
        os.replace(temporary, features_path)
        metadata = {'key': key, 'features_sha256': sha256(features_path),
                    'cold_setup_seconds': cold_setup, 'val_ids': val_ids,
                    'backbone_parameters': parameter_counts(model)['total']}
        write_json(metadata_path, metadata)
        del model
    budget.check()
    count = int(x.shape[1] + 1)
    write_json(folder / 'run_metadata.json', {'parameters': {'trainable': count,
                'total': metadata['backbone_parameters'] + count}, 'target_modules': [],
                'n_train': len(train), 'n_validation': len(val), 'cache_hit': hit,
                'cache_key': key, 'cold_feature_setup_seconds': metadata['cold_setup_seconds']})
    probe = LogisticRegression(C=config['C'], class_weight='balanced', solver='lbfgs',
                               tol=1e-4, max_iter=1000, random_state=config['seed'])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        probe.fit(x, y)
    probabilities = probe.predict_proba(xv)[:, 1]
    threshold = choose_threshold(yv, probabilities)
    budget.check()
    model_path = folder / 'linear_probe.json'
    write_json(model_path, {'coef': probe.coef_.tolist(), 'intercept': probe.intercept_.tolist(),
                            'classes': probe.classes_.tolist()})
    best = {'epoch': None, 'validation_auc': float(roc_auc_score(yv, probabilities)),
            'threshold': threshold, 'validation_ids': metadata['val_ids'],
            'validation_labels': yv.tolist(), 'validation_probabilities': probabilities.tolist(),
            'checkpoint': model_path.name, 'checkpoint_sha256': sha256(model_path),
            'charged_seconds_at_selection': budget.elapsed()}
    budget.check()
    write_json(folder / 'best.json', best)
    count = int(probe.coef_.size + probe.intercept_.size)
    return {'parameters': {'trainable': count, 'total': metadata['backbone_parameters'] + count},
            'target_modules': [], 'epochs_completed': None, 'stop_reason': 'solver_finished',
            'optimizer_iterations': probe.n_iter_.tolist(),
            'optimizer_warnings': [str(w.message) for w in caught], 'best': best,
            'cache_hit': hit, 'cache_credit_seconds': budget.credit,
            'cache_key': key, 'cold_feature_setup_seconds': metadata['cold_setup_seconds']}


def worker(config_path: Path):
    config = json.loads(config_path.read_text())
    from src.protocol import validate_run_config
    validate_run_config(config)
    folder = config_path.parent
    limiter = setup_cpu(config['seed'], config['threads'])
    budget = Budget(folder, config['cap_seconds'])
    train, val = development_rows(config['fraction'], config['seed'])
    # Recheck selected original pixels on every attempt, including cache hits.
    for frame in (train, val):
        for row in frame.to_dict('records'):
            if sha256(ROOT / row['path']) != row['sha256']:
                raise RuntimeError('Development image checksum mismatch: ' + row['image_id'])
    if config['purpose'] == 'smoke':
        # 2% of 341 with four/class floor is 8: identical to the frozen 1% subset.
        if len(train) != 8:
            raise ValueError('Smoke must use the audited eight-image subset')
    try:
        fit = (fit_lp if config['method'] == 'LP' else fit_neural)(config, train, val, folder, budget)
    except BudgetExpired:
        fit = {'best': None, 'stop_reason': 'time_cap', 'cache_credit_seconds': budget.credit}
    fit.update(config_hash=config_hash(config), charged_wall_seconds=budget.elapsed(),
               actual_fit_wall_seconds=time.perf_counter() - budget.started,
               n_train=len(train), n_validation=len(val),
               status='PASS' if fit['best'] is not None else 'FAIL_NO_CHECKPOINT')
    write_json(folder / 'fit.json', fit)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    worker(parser.parse_args().config)
