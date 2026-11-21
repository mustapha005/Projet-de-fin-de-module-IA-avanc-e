"""Measure development-only CPU work; never calculate test or selection scores."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def worker(args):
    import numpy as np
    import psutil
    from sklearn.linear_model import LogisticRegression
    import torch
    from src.datasets import Images, development_rows, loader
    from src.models import build_model, parameter_counts
    from src.runtime import setup_cpu

    limiter = setup_cpu(0, args.threads)
    train, val = development_rows(args.fraction, 0)
    process = psutil.Process()
    cpu_start = sum(process.cpu_times()[:2])
    started = time.perf_counter()
    model = build_model(args.method)
    load_seconds = time.perf_counter() - started
    counts = parameter_counts(model)
    training = Images(train, training=True, seed=0, views=4 if args.method == 'LP' else 1,
                      size=args.cnn_size if args.method == 'CNN' else 224)
    validation = Images(val, size=args.cnn_size if args.method == 'CNN' else 224)
    train_loader = loader(training, shuffle=args.method != 'LP')
    val_loader = loader(validation)
    weights = torch.tensor(len(train) / (2 * np.bincount(train.label, minlength=2)), dtype=torch.float32)
    optimizer = None if args.method == 'LP' else torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=.0003, weight_decay=.01)
    # Separate one batch warm-up from the measured full pass; no score is computed.
    warm = time.perf_counter()
    pixels, labels, _ = next(iter(train_loader))
    if optimizer is None:
        model.eval()
        with torch.no_grad():
            model(pixels)
    else:
        model.train()
        loss = torch.nn.functional.cross_entropy(model(pixels), labels, weight=weights)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
    warm_seconds = time.perf_counter() - warm
    started = time.perf_counter()
    if args.method == 'LP':
        features, labels_all = [], []
        for i, (pixels, labels, _) in enumerate(train_loader):
            with torch.no_grad():
                features.append(model(pixels).numpy())
            labels_all.append(labels.numpy())
            if i % 8 == 0:
                print('LP extraction batch', i + 1, '/', len(train_loader), flush=True)
        extraction_seconds = time.perf_counter() - started
        started = time.perf_counter()
        probe = LogisticRegression(C=1., class_weight='balanced', solver='lbfgs', max_iter=1000, tol=1e-4)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            probe.fit(np.concatenate(features), np.concatenate(labels_all))
        fit_seconds = time.perf_counter() - started
        optimizer_warnings = [str(item.message) for item in caught]
        counts['trainable'] = int(probe.coef_.size + probe.intercept_.size)
        counts['total'] += counts['trainable']
        training_seconds = extraction_seconds + fit_seconds
    else:
        model.train()
        for i, (pixels, labels, _) in enumerate(train_loader):
            optimizer.zero_grad(set_to_none=True)
            loss = torch.nn.functional.cross_entropy(model(pixels), labels, weight=weights)
            if not torch.isfinite(loss):
                raise RuntimeError('Non-finite benchmark loss')
            loss.backward()
            optimizer.step()
            print(args.method, 'training batch', i + 1, '/', len(train_loader), flush=True)
        training_seconds = time.perf_counter() - started
        extraction_seconds, fit_seconds, optimizer_warnings = None, None, []
    model.eval()
    started = time.perf_counter()
    with torch.no_grad():
        for pixels, labels, _ in val_loader:
            output = model(pixels)
            if args.method == 'LP':
                probe.predict_proba(output.numpy())
            else:
                output.softmax(dim=1)
    validation_seconds = time.perf_counter() - started
    memory = process.memory_info()
    record = {'status': 'PASS', 'purpose': 'timing_only_no_performance_scores',
              'method': args.method, 'fraction': args.fraction, 'seed': 0,
              'n_train': len(train), 'n_validation': len(val),
              'training_views': training.views, 'batch_size': train_loader.batch_size,
              'image_size': args.cnn_size if args.method == 'CNN' else 224,
              'threads': args.threads, 'interop_threads': 1, 'loader_workers': 0,
              'parameters': counts, 'target_modules': getattr(model, 'target_modules', []),
              'model_load_seconds': load_seconds, 'warmup_seconds': warm_seconds,
              'train_seconds': training_seconds, 'validation_seconds': validation_seconds,
              'epoch_seconds': None if args.method == 'LP' else training_seconds + validation_seconds,
              'cold_lp_seconds': load_seconds + training_seconds + validation_seconds if args.method == 'LP' else None,
              'feature_extraction_seconds': extraction_seconds, 'optimizer_fit_seconds': fit_seconds,
              'optimizer_warnings': optimizer_warnings,
              'process_cpu_seconds': sum(process.cpu_times()[:2]) - cpu_start,
              'peak_rss_bytes': getattr(memory, 'peak_wset', memory.rss),
              'finished_utc': datetime.now(timezone.utc).isoformat()}
    from src.runtime import write_json
    write_json(Path(args.output), record)


def coordinator(args):
    from src.runtime import config_hash, git_commit, sha256, write_json
    folder = ROOT / 'docs/benchmark'
    folder.mkdir(parents=True, exist_ok=True)
    dependencies = ['src/datasets.py', 'src/models.py', 'src/runtime.py', 'scripts/benchmark_cpu.py',
                    'configs/backbone.json', 'data/development_view.json', 'data/manifests/label_subsets.csv']
    fingerprint = config_hash({p: sha256(ROOT / p) for p in dependencies})
    records = []
    for method in args.methods:
        for fraction in args.fractions:
            path = folder / f'{method}_{int(fraction * 100):03d}_t{args.threads}.json'
            if path.exists():
                record = json.loads(path.read_text())
                if record.get('fingerprint') == fingerprint and record.get('status') == 'PASS':
                    records.append(record)
                    print('Verified completed benchmark:', path.name, flush=True)
                    continue
                raise RuntimeError(f'Stale benchmark {path}; archive before remeasurement')
            partial = folder / (path.stem + '.worker.json')
            command = [sys.executable, str(Path(__file__).resolve()), '--worker', '--method', method,
                       '--fraction', str(fraction), '--threads', str(args.threads),
                       '--cnn-size', str(args.cnn_size), '--output', str(partial)]
            started = time.perf_counter()
            print('Starting timing-only benchmark:', method, fraction, flush=True)
            try:
                subprocess.run(command, cwd=ROOT, check=True, timeout=1800)
            except (subprocess.SubprocessError, OSError) as error:
                write_json(path.with_suffix('.failed.json'), {'status': 'FAIL', 'fingerprint': fingerprint,
                                                             'error': str(error)})
                raise
            record = json.loads(partial.read_text())
            record.update(fingerprint=fingerprint, git_commit=git_commit(),
                          total_worker_wall_seconds=time.perf_counter() - started)
            write_json(path, record)
            partial.unlink()
            records.append(record)
            print('Completed:', method, fraction, 'train=', round(record['train_seconds'], 2),
                  'val=', round(record['validation_seconds'], 2), 'peak GiB=',
                  round(record['peak_rss_bytes'] / 1024 ** 3, 3), flush=True)
    write_json(folder / 'benchmark_index.json', {'status': 'PASS', 'fingerprint': fingerprint,
                                                'cells': len(records), 'records': records})
    print('Benchmark cells completed:', len(records), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--method', choices=['LP', 'PFT', 'LoRA', 'CNN'])
    parser.add_argument('--fraction', type=float)
    parser.add_argument('--methods', nargs='+', default=['LP', 'PFT', 'LoRA', 'CNN'])
    parser.add_argument('--fractions', nargs='+', type=float, default=[.01, .1, 1.])
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--cnn-size', type=int, default=224)
    parser.add_argument('--output')
    args = parser.parse_args()
    worker(args) if args.worker else coordinator(args)
