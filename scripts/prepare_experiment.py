"""Prepare, but never automatically tag, a complete experimental contract."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.runtime import sha256, write_json


def main():
    if subprocess.check_output(['git', 'tag', '--list', 'protocol-frozen'], cwd=ROOT, text=True).strip():
        raise RuntimeError('Protocol already frozen; do not regenerate without user review')
    if list((ROOT / 'results').rglob('*')):
        raise RuntimeError('Results must be empty before freeze')
    data = json.loads((ROOT / 'data/pipeline_status.json').read_text())
    assert data['status'] == 'PASS'
    for name, digest in data['manifest_sha256'].items():
        assert sha256(ROOT / 'data/manifests' / name) == digest
    smoke = json.loads((ROOT / 'docs/benchmark/smoke_report.json').read_text())
    assert smoke['status'] == 'PASS' and smoke['process_tree_resource_check'] == 'PASS'
    projection = json.loads((ROOT / 'docs/benchmark/compute_projection.json').read_text())
    assert not projection['fallback_required_at_60_hours']
    machine = json.loads((ROOT / 'docs/machine.json').read_text())
    names = [p.relative_to(ROOT).as_posix() for p in (ROOT / 'src').glob('*.py')]
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT / 'data/manifests').glob('*.csv')]
    names += ['configs/backbone.json', 'configs/search.json', 'configs/busi_published_pairs.json',
              'data/development_view.json', 'requirements.lock', 'docs/PROTOCOL.md']
    for name in names:
        if b'\r\n' in (ROOT / name).read_bytes():
            raise RuntimeError('Nonportable source line endings: ' + name)
    contract = {'freeze_authority': 'protocol-frozen Git tag', 'cap_seconds': projection['proposed_t_max_seconds'],
                'threads': 4, 'interop_threads': 1, 'max_epochs': 50, 'patience': 8,
                'image_size': 224, 'seeds': [0, 1, 2], 'fractions': [.01, .1, 1.],
                'split_seed': 1234, 'lp_augmented_views': 4, 'bootstrap_resamples': 2000,
                'bootstrap_seed': 20261120, 'reference_machine': {k: machine[k] for k in
                  ['cpu', 'platform', 'python', 'physical_cores', 'logical_cores', 'ram_bytes']},
                'package_versions': machine['packages'],
                'protected_sha256': {name: sha256(ROOT / name) for name in sorted(names)},
                'timing_evidence': 'docs/benchmark/benchmark_index.json',
                'projection_hours_with_headroom': projection['with_20_percent_headroom_hours'],
                'budget_fallbacks': []}
    write_json(ROOT / 'configs/experiment.json', contract)
    print('Prepared immutable settings; commit and audit clean checkout before tagging.')


if __name__ == '__main__':
    main()
