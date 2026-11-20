"""Check bibliography/verified-ledger consistency; not a replacement for source reading."""
from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    ledger = json.loads((ROOT / 'docs/reference_verification.json').read_text(encoding='utf-8'))
    refs = ledger['references']
    keys = re.findall(r'^@\w+\{([^,]+),', (ROOT / 'paper/refs.bib').read_text(encoding='utf-8'), re.M)
    assert len(keys) == len(set(keys)), 'Duplicate BibTeX keys'
    assert set(keys) == {r['key'] for r in refs}, 'Bibliography/verification mismatch'
    assert len(refs) == len({r['key'] for r in refs}), 'Duplicate ledger keys'
    assert all(r['verified_url'].startswith('https://') and r['verification'] for r in refs)
    recent = sum(2024 <= r['year'] <= 2026 for r in refs)
    assert 15 <= len(refs) <= 25 and recent > len(refs) / 2
    assert ledger['reference_count'] == len(refs)
    assert ledger['recent_2024_2026_count'] == recent
    print(json.dumps({'status': 'PASS', 'references': len(refs), 'recent': recent,
                      'year_counts': dict(Counter(r['year'] for r in refs)),
                      'scope': 'Identity checks are documented separately; this verifies ledger consistency.'}, indent=2))


if __name__ == '__main__':
    main()
