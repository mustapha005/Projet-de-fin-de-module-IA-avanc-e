"""Print compact experiment progress and observed costs without exposing test scores."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    records = []
    unfinished = []
    for folder in sorted((ROOT / 'data/cache/runs').glob('*/attempt_*')):
        path = folder / 'supervised.json'
        if path.exists():
            records.append(json.loads(path.read_text()))
        else:
            history_path = folder / 'history.json'
            epochs = len(json.loads(history_path.read_text())['epochs']) if history_path.exists() else 0
            unfinished.append({'attempt': folder.relative_to(ROOT).as_posix(), 'complete_epochs_logged': epochs,
                               'state': 'unfinished; liveness not inferred from files'})
    tuning = {}
    for method, expected in [('LP', 5), ('PFT', 6), ('LoRA', 6), ('CNN', 6)]:
        candidates = [json.loads(p.read_text()) for p in (ROOT / 'results/tuning').glob(f'{method}_candidate_*.json')]
        tuning[method] = {'completed': sum(x['status'] == 'PASS' for x in candidates), 'expected': expected,
                          'selection_saved': (ROOT / 'configs/frozen' / f'{method}.json').exists()}
    print(json.dumps({'tuning': tuning, 'main_completed': len(list((ROOT / 'results/main').glob('*.json'))),
                       'main_expected': 36, 'ablations_completed': len(list((ROOT / 'results/ablation').glob('*.json'))),
                       'ablations_expected': 21, 'completed_attempts': len(records),
                       'observed_worker_wall_hours': sum(r['total_worker_wall_seconds'] for r in records) / 3600,
                       'observed_process_cpu_hours': sum(r['process_cpu_seconds'] for r in records) / 3600,
                       'cost_scope': 'Completed tuning/final attempts, including worker startup; excludes unfinished work, benchmark, smoke, downloads and research.',
                       'unfinished_attempts': unfinished}, indent=2))


if __name__ == '__main__':
    main()
