"""Article numbers that come from data reports and the frozen contract, not results."""
import json
from pathlib import Path

from src.runtime import ROOT


def load(root: Path, relative: str) -> dict:
    return json.loads((root / relative).read_text(encoding='utf-8'))


def protocol_numbers(root: Path = ROOT) -> dict[str, str]:
    inventory = load(root, 'data/inventory_report.json')
    dedup = load(root, 'data/dedup_report.json')
    splits = load(root, 'data/split_report.json')
    published = load(root, 'data/published_duplicate_audit.json')
    contract = json.loads(__import__('subprocess').check_output(
        ['git', 'show', 'protocol-frozen:configs/experiment.json'], cwd=root, text=True, encoding='utf-8'))
    backbone = load(root, 'configs/backbone.json')
    search = load(root, 'configs/search.json')
    busi, breast = inventory['busi'], inventory['breast']['class_counts']
    counts = splits['split_counts']
    n = {}
    n['data.busi.benign_raw'] = str(busi['benign'])
    n['data.busi.malignant_raw'] = str(busi['malignant'])
    n['data.busi.normal_excluded'] = str(busi['normal'])
    n['data.busi.binary_raw'] = str(dedup['input_images'])
    n['data.busi.retained'] = str(dedup['retained_images'])
    n['data.busi.removed'] = str(dedup['removed_images'])
    n['data.busi.conflict_images'] = str(dedup['conflict_images'])
    n['data.busi.conflict_components'] = str(dedup['conflict_components'])
    n['data.busi.hamming'] = str(dedup['hamming_threshold'])
    n['data.busi.published_pairs'] = str(published['published_pairs'])
    rejected = load(root, 'docs/reviews/phash_only/published_duplicate_audit.json')
    n['data.phash_only.crossing_pairs'] = str(sum(p['crosses_split'] for p in rejected['retained_duplicate_pairs']))
    retained = inventory['busi_retained_class_counts']
    n['data.busi.retained_benign'] = str(retained['0'])
    n['data.busi.retained_malignant'] = str(retained['1'])
    for split in ('train', 'val', 'test'):
        total = counts[split]['benign'] + counts[split]['malignant']
        n[f'data.busi.{split}'] = str(total)
        n[f'data.busi.{split}.benign'] = str(counts[split]['benign'])
        n[f'data.busi.{split}.malignant'] = str(counts[split]['malignant'])
    n['data.breast.benign'] = str(breast['benign'])
    n['data.breast.malignant'] = str(breast['malignant'])
    n['data.breast.normal_excluded'] = str(breast['normal'])
    n['data.breast.total'] = str(breast['benign'] + breast['malignant'])
    n['data.breast.metadata_rows'] = str(inventory['breast']['metadata_rows'])
    for subset in splits['subsets']:
        if subset['seed'] != 0:
            continue
        key = {0.01: '1', 0.1: '10', 1.0: '100'}[subset['nominal_fraction']]
        n[f'data.subset.{key}.n'] = str(subset['n'])
        n[f'data.subset.{key}.benign'] = str(subset['benign'])
        n[f'data.subset.{key}.malignant'] = str(subset['malignant'])
        n[f'data.subset.{key}.actual_pct'] = f"{100 * subset['actual_fraction']:.2f}"
    machine = contract['reference_machine']
    n['hw.cpu'] = machine['cpu'].replace('(R)', '').replace('(TM)', '').replace(' CPU', '')
    n['hw.physical_cores'] = str(machine['physical_cores'])
    n['hw.logical_cores'] = str(machine['logical_cores'])
    n['hw.ram_gib'] = f"{machine['ram_bytes'] / 2 ** 30:.1f}"
    n['hw.python'] = machine['python']
    n['protocol.cap_seconds'] = f"{contract['cap_seconds']:,}"
    n['protocol.cap_minutes'] = str(contract['cap_seconds'] // 60)
    n['protocol.threads'] = str(contract['threads'])
    n['protocol.max_epochs'] = str(contract['max_epochs'])
    n['protocol.patience'] = str(contract['patience'])
    n['protocol.split_seed'] = str(contract['split_seed'])
    n['protocol.bootstrap_resamples'] = f"{contract['bootstrap_resamples']:,}"
    n['protocol.bootstrap_seed'] = str(contract['bootstrap_seed'])
    n['protocol.lp_views'] = str(contract['lp_augmented_views'])
    n['protocol.projection_hours'] = f"{contract['projection_hours_with_headroom']:.1f}"
    n['protocol.image_size'] = str(contract['image_size'])
    n['protocol.search.LP'] = str(len(search['LP']))
    n['protocol.search.PFT'] = str(len(search['PFT']))
    n['protocol.search.LoRA'] = str(len(search['LoRA']))
    n['protocol.search.CNN'] = str(len(search['CNN']))
    n['backbone.revision_short'] = backbone['revision'][:7]
    n['backbone.hidden_size'] = str(backbone['hidden_size'])
    n['backbone.layers'] = str(backbone['num_hidden_layers'])
    n['backbone.patch_size'] = str(backbone['patch_size'])
    for method in ('LP', 'PFT', 'LoRA', 'CNN'):
        path = root / 'configs/frozen' / f'{method}.json'
        if not path.exists():
            continue
        selection = json.loads(path.read_text(encoding='utf-8'))
        for name, value in selection['hyperparameters'].items():
            n[f'tuning.{method}.{name}'] = f'{value:g}'
        best = max(entry['best_validation_auc'] for entry in selection['ledger'] if entry['status'] == 'PASS')
        n[f'tuning.{method}.val_auc'] = f'{best:.3f}'
    return n


def write(root: Path = ROOT) -> Path:
    from src.runtime import write_json
    path = root / 'paper/numbers_protocol.json'
    write_json(path, {'source': 'Generated by src/analysis/protocol_numbers.py from data reports, '
                                'the protocol-frozen contract and configs/frozen/',
                      'values': protocol_numbers(root)})
    return path


if __name__ == '__main__':
    print('Wrote', write())
