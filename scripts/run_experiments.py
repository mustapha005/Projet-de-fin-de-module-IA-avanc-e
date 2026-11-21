"""Run the frozen grid serially, retaining attempts and validating completed work."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluate import final_evaluation
from src.protocol import validate_run_config, verify_frozen
from src.runtime import config_hash, setup_cpu, sha256, write_json
from src.supervise import run_training


def configuration(contract, method, purpose, fraction, seed, hp, **extra):
    return {'method': method, 'purpose': purpose, 'fraction': fraction, 'seed': seed,
            **{k: contract[k] for k in ['threads', 'cap_seconds', 'max_epochs', 'patience', 'image_size']},
            **hp, **extra}


def completed_attempt(cell, config):
    """Completed fits may be reused; interrupted fits never extend their budget."""
    if not cell.exists():
        return None
    for folder in sorted(cell.glob('attempt_*')):
        path = folder / 'supervised.json'
        if not path.exists():
            continue
        record = json.loads(path.read_text())
        if record['config_hash'] != config_hash(config):
            raise RuntimeError('Existing cell has a different configuration')
        if record['status'] == 'PASS':
            best = record['best']
            if sha256(folder / best['checkpoint']) != best['checkpoint_sha256']:
                raise RuntimeError('Completed checkpoint changed')
            return folder, record
    return None


def fit_cell(name, config):
    validate_run_config(config)
    cell = ROOT / 'data/cache/runs' / name
    previous = completed_attempt(cell, config)
    if previous:
        print('Verified completed fit:', name, flush=True)
        return previous
    attempts = sorted(cell.glob('attempt_*')) if cell.exists() else []
    folder = cell / f'attempt_{len(attempts) + 1:03d}'
    print('Starting:', name, 'attempt', len(attempts) + 1, flush=True)
    return folder, run_training(config, folder)


def tune(contract, methods):
    search = json.loads((ROOT / 'configs/search.json').read_text())
    for method in methods:
        ledger = []
        for index, hp in enumerate(search[method]):
            name = f'tune_{method}_{index:02d}'
            config = configuration(contract, method, 'tune', .1, 0, hp)
            try:
                folder, record = fit_cell(name, config)
                entry = {'index': index, 'hyperparameters': hp, 'status': 'PASS',
                         'best_validation_auc': record['best']['validation_auc'],
                         'supervised_path': (folder / 'supervised.json').relative_to(ROOT).as_posix(),
                         'supervised_sha256': sha256(folder / 'supervised.json')}
            except RuntimeError as error:
                # Record numerical/cap failures; do not add replacement candidates.
                entry = {'index': index, 'hyperparameters': hp, 'status': 'FAIL', 'error': str(error)}
                write_json(ROOT / 'results/tuning' / f'{method}_candidate_{index:02d}.json', entry)
                raise
            ledger.append(entry)
            write_json(ROOT / 'results/tuning' / f'{method}_candidate_{index:02d}.json', entry)
            print('Tuning candidate complete:', method, index + 1, '/', len(search[method]), flush=True)
        successful = [entry for entry in ledger if entry['status'] == 'PASS']
        best = successful[0]
        for entry in successful[1:]:
            if entry['best_validation_auc'] > best['best_validation_auc'] + 1e-12:
                best = entry
        selection = {'method': method, 'hyperparameters': best['hyperparameters'],
                     'selected_index': best['index'], 'criterion': 'validation_roc_auc',
                     'tie_policy': 'first_in_ascending_search_list_within_1e-12',
                     'selected_utc': datetime.now(timezone.utc).isoformat(),
                     'ledger': ledger}
        write_json(ROOT / 'configs/frozen' / f'{method}.json', selection)
        print('Selected configuration:', method, best['hyperparameters'], flush=True)


def final_cell(contract, name, config):
    path = ROOT / 'results' / config['purpose'] / f'{name}.json'
    if path.exists():
        result = json.loads(path.read_text())
        validate_run_config(config)
        if result['config_hash'] != config_hash(config):
            raise RuntimeError('Saved final result has a different configuration')
        for cohort in result['evaluation']['cohorts'].values():
            if sha256(ROOT / result['prediction_folder'] / cohort['predictions_file']) != cohort['predictions_sha256']:
                raise RuntimeError('Saved predictions changed')
        print('Verified completed final result:', name, flush=True)
        return
    folder, fit = fit_cell(name, config)
    prediction_folder = ROOT / 'results/predictions' / name
    evaluation = final_evaluation(config, fit['best'], folder, prediction_folder)
    tag = subprocess.check_output(['git', 'rev-parse', 'protocol-frozen'], cwd=ROOT, text=True).strip()
    result = {'status': 'PASS', 'run_id': name, 'config': config, 'config_hash': config_hash(config),
              'frozen_commit': tag, 'completed_utc': datetime.now(timezone.utc).isoformat(),
              'reference_machine': contract['reference_machine'], 'protected_sha256': contract['protected_sha256'],
              'attempt_path': folder.relative_to(ROOT).as_posix(),
              'prediction_folder': prediction_folder.relative_to(ROOT).as_posix(),
              'fit': fit, 'evaluation': evaluation,
              'auc_gap': evaluation['cohorts']['internal']['metrics']['roc_auc'] - evaluation['cohorts']['external']['metrics']['roc_auc']}
    write_json(path, result)
    print('Final result committed:', name, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['tune', 'main', 'ablation'], required=True)
    parser.add_argument('--methods', nargs='+', choices=['LP', 'PFT', 'LoRA', 'CNN'], default=['LP', 'PFT', 'LoRA', 'CNN'])
    parser.add_argument('--limit', type=int, help='Bound final cells this invocation; incomplete grids remain explicit')
    args = parser.parse_args()
    contract = verify_frozen()
    limiter = setup_cpu(0, contract['threads'])
    if args.phase == 'tune':
        tune(contract, args.methods)
        return
    count = 0
    variants = [('main', None, {})] if args.phase == 'main' else [
        ('lora_last2', 'LoRA', {'lora_depth': 2}), ('lora_rank4', 'LoRA', {'rank': 4}),
        ('lora_rank16', 'LoRA', {'rank': 16}), ('pft_depth4', 'PFT', {'depth': 4}),
        ('lora_no_augmentation', 'LoRA', {'augmentation': False})]
    for variant, required_method, extra in variants:
        for method in args.methods:
            if required_method is not None and method != required_method:
                continue
            selection = json.loads((ROOT / 'configs/frozen' / f'{method}.json').read_text())
            fractions = contract['fractions'] if variant in {'main', 'lora_last2'} else [.1]
            for fraction in fractions:
                for seed in contract['seeds']:
                    options = extra if args.phase == 'main' else {**extra, 'ablation_name': variant}
                    config = configuration(contract, method, args.phase, fraction, seed, selection['hyperparameters'], **options)
                    name = f'{variant}_{method}_{int(100 * fraction):03d}_s{seed}'
                    final_cell(contract, name, config)
                    count += 1
                    if args.limit and count >= args.limit:
                        return


if __name__ == '__main__':
    main()
