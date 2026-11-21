"""Project the fixed workload from measured timings without using any AUC."""
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.runtime import write_json, sha256


def main():
    path = ROOT / 'docs/benchmark/benchmark_index.json'
    source = json.loads(path.read_text())
    records = source['records']
    assert source['status'] == 'PASS' and len(records) == 12
    lookup = {(r['method'], r['fraction']): r for r in records}
    slow = max(lookup[m, 1.]['epoch_seconds'] for m in ['PFT', 'LoRA', 'CNN'])
    cap = math.ceil(max(10 * slow, 1.25 * lookup['LP', 1.]['cold_lp_seconds']) / 60) * 60
    rows = []

    def add(phase, method, fraction, runs, train_factor=1.):
        r = lookup[method, fraction]
        if method == 'LP':
            fit = min(cap, r['cold_lp_seconds'])
        else:
            fit = min(cap, r['model_load_seconds'] + 50 * (train_factor * r['train_seconds'] + r['validation_seconds']))
        # Per-image validation forward cost is the only measured inference proxy.
        inference = r['validation_seconds'] * (74 + 252) / r['n_validation'] if phase != 'tuning' else 0.
        rows.append({'phase': phase, 'method': method, 'fraction': fraction, 'runs': runs,
                     'estimated_fit_seconds_per_run': fit,
                     'estimated_final_inference_seconds_per_run': inference,
                     'estimated_seconds': runs * (fit + inference)})

    for method in ['LP', 'PFT', 'LoRA', 'CNN']:
        add('tuning', method, .1, 5 if method == 'LP' else 6)
        for fraction in [.01, .1, 1.]:
            add('main', method, fraction, 3)
    for fraction in [.01, .1, 1.]:
        add('ablation_lora_last2', 'LoRA', fraction, 3)  # conservative all-block timing
    add('ablation_lora_rank4', 'LoRA', .1, 3, train_factor=1.1)
    add('ablation_lora_rank16', 'LoRA', .1, 3, train_factor=1.1)
    add('ablation_pft_depth4', 'PFT', .1, 3, train_factor=2.)
    add('ablation_no_augmentation', 'LoRA', .1, 3)
    seconds = sum(r['estimated_seconds'] for r in rows)
    output = {'status': 'PROJECTION_ONLY', 'benchmark_sha256': sha256(path),
              'proposed_t_max_seconds': cap, 'threads': 4, 'epochs': 50,
              'tuning_runs': 23, 'main_runs': 36, 'ablation_runs': 21,
              'estimated_elapsed_cpu_hours': seconds / 3600,
              'with_20_percent_headroom_hours': seconds * 1.2 / 3600,
              'fallback_required_at_60_hours': seconds * 1.2 > 60 * 3600,
              'rows': rows,
              'assumptions': ['No early stopping benefit assumed.',
                              'Every isolated LP run pays its cold feature setup, even cache hits.',
                              'Ablation costs are proxies; last2 LoRA uses all12 cost; ranks add 10% train time; PFT4 doubles train time.',
                              'Held-out inference estimated by validation seconds/image; no held-out prediction was made.',
                              '20% covers setup, checkpoint I/O and timing variation; prolonged throttling can exceed this estimate.',
                              'Hours are elapsed on this CPU, not aggregate thread/core-hours.']}
    write_json(ROOT / 'docs/benchmark/compute_projection.json', output)
    print(json.dumps({k: v for k, v in output.items() if k not in {'rows', 'assumptions'}}, indent=2))


if __name__ == '__main__':
    main()
