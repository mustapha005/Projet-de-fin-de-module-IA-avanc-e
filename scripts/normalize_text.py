"""Pre-freeze one-time LF migration; verify CSV contents are unchanged."""
import csv
import io
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    tags = subprocess.check_output(['git', 'tag', '--list', 'protocol-frozen'], cwd=ROOT, text=True)
    if tags.strip():
        raise RuntimeError('Normalization after freeze needs explicit review')
    names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                                    cwd=ROOT).decode().split('\0')
    changed = []
    for name in sorted(set(filter(None, names))):
        path = ROOT / name
        if path.suffix not in {'.py', '.json', '.md', '.csv', '.yml', '.yaml', '.lock', '.txt', '.bib'} and path.name not in {'Makefile', '.gitattributes', '.gitignore'}:
            continue
        original = path.read_bytes()
        updated = original.replace(b'\r\n', b'\n')
        if original == updated:
            continue
        if path.suffix == '.csv':
            assert list(csv.reader(io.StringIO(original.decode('utf-8')))) == list(csv.reader(io.StringIO(updated.decode('utf-8'))))
        if path.suffix == '.json':
            assert json.loads(original) == json.loads(updated)
        path.write_bytes(updated)
        changed.append(name)
    report = {'status': 'PASS', 'csv_and_json_semantics_unchanged': True,
              'changed_files': changed, 'policy': 'UTF-8 source bytes use LF across Windows and clean Git checkouts.'}
    (ROOT / 'docs/reviews/line_ending_migration.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('Normalized', len(changed), 'text files; parsed CSV/JSON content unchanged')


if __name__ == '__main__':
    main()
