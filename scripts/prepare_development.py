"""Create an audited train/validation-only view during data preparation."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from src.runtime import sha256, write_json


def main():
    source = ROOT / 'data/manifests/busi_splits.csv'
    all_rows = pd.read_csv(source, dtype={'phash': str})
    development = all_rows[all_rows.split.isin(['train', 'val'])].copy()
    assert set(development.split) == {'train', 'val'}
    assert not set(development.image_id) & set(all_rows.loc[all_rows.split == 'test', 'image_id'])
    path = ROOT / 'data/cache/development.csv'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(development.to_csv(index=False, lineterminator='\n'), encoding='utf-8', newline='\n')
    write_json(ROOT / 'data/development_view.json', {
        'status': 'PASS', 'source_manifest_sha256': sha256(source),
        'development_sha256': sha256(path), 'path': path.relative_to(ROOT).as_posix(),
        'rows': len(development), 'counts': development.split.value_counts().to_dict(),
        'policy': 'Derived at preparation; training opens this view only, never held-out manifests.'})
    print('Prepared development-only manifest:', len(development), 'records')


if __name__ == '__main__':
    main()
