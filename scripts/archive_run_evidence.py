"""Make completed worker evidence portable without publishing weights or images."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.runtime import sha256, write_json


def main():
    count = 0
    for path in sorted((ROOT / 'data/cache/runs').glob('*/attempt_*/supervised.json')):
        folder = path.parent
        record = json.loads(path.read_text())
        history = folder / 'history.json'
        log = folder / 'worker.log'
        payload = {'worker_evidence': record, 'supervised_sha256': sha256(path),
                   'epoch_history': json.loads(history.read_text())['epochs'] if history.exists() else [],
                   'worker_log': log.read_text(encoding='utf-8', errors='replace') if log.exists() else '',
                   'policy': 'No weights, images or feature vectors included; validation predictions document selection.'}
        target = ROOT / 'results/run_evidence' / f'{folder.parent.name}_{folder.name}.json'
        write_json(target, payload)
        count += 1
    print('Archived complete worker evidence:', count, 'attempts')


if __name__ == '__main__':
    main()
