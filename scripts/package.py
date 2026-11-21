"""Phase 7: assemble deliverables/ with the exact course file names and audit the code zip.

The code archive is `git archive HEAD`, so only committed files are included: raw data,
downloads, caches, weights and environments are Git-ignored and cannot enter it. The
archive is then scanned for forbidden paths/extensions and likely secrets.
"""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'SDIA2026_SAN-1_GROUP_13'
OUT = ROOT / 'deliverables'
FORBIDDEN_PARTS = ('data/raw/', 'data/downloads/', 'data/cache/', 'weights/', '.venv', '.cache/', '.inputs/', 'logs/')
FORBIDDEN_SUFFIXES = ('.pt', '.pth', '.safetensors', '.npz', '.ckpt', '.bin', '.env', '.part')
SECRET = re.compile(r'(api[_-]?key|secret|password|token)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{16,}', re.I)


def main():
    if subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True).stdout.strip():
        sys.exit('Commit all work before packaging: the archive is built from HEAD.')
    OUT.mkdir(exist_ok=True)
    archive = OUT / f'{PREFIX}_code.zip'
    subprocess.run(['git', 'archive', '--format=zip', f'--prefix={PREFIX}/', '-o', str(archive), 'HEAD'], cwd=ROOT, check=True)
    problems = []
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        for name in names:
            relative = name.split('/', 1)[-1]
            if any(part in relative for part in FORBIDDEN_PARTS) and not relative.endswith(('README.md', '.gitkeep')):
                problems.append(f'forbidden path: {name}')
            if relative.lower().endswith(FORBIDDEN_SUFFIXES):
                problems.append(f'forbidden file type: {name}')
            if relative.endswith(('.py', '.json', '.md', '.txt', '.yml', '.toml', '.lock', '.csv')):
                text = bundle.read(name).decode('utf-8', errors='replace')
                if SECRET.search(text):
                    problems.append(f'possible secret: {name}')
            if relative.startswith('data/') and relative.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.xlsx')):
                problems.append(f'dataset image/metadata file: {name}')
    copies = {}
    for source, target in [(ROOT / 'paper/build' / f'{PREFIX}_article.pdf', f'{PREFIX}_article.pdf'),
                           (ROOT / 'paper/build' / f'{PREFIX}_article.docx', f'{PREFIX}_article.docx'),
                           (ROOT / 'slides/build' / f'{PREFIX}_presentation.pptx', f'{PREFIX}_presentation.pptx')]:
        if source.exists():
            shutil.copy2(source, OUT / target)
            copies[target] = True
        else:
            copies[target] = False
    report = {'code_zip': archive.name, 'files_in_zip': len(names), 'zip_bytes': archive.stat().st_size,
              'problems': problems, 'deliverables_copied': copies,
              'status': 'PASS' if not problems and all(copies.values()) else 'FAIL'}
    (ROOT / 'docs/reviews/package_audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))
    sys.exit(0 if report['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
