"""Record installed primary library license evidence without copying package data."""
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['torch', 'torchvision', 'transformers', 'peft', 'scikit-learn',
         'numpy', 'scipy', 'Pillow', 'ImageHash', 'pandas', 'matplotlib']


def main():
    entries = []
    for name in NAMES:
        dist = metadata.distribution(name)
        files = [f for f in dist.files or [] if
                 ('dist-info/' in str(f).replace('\\', '/')) and
                 ('license' in f.name.lower() or f.name.upper() == 'COPYING')]
        evidence = []
        for item in files:
            path = Path(dist.locate_file(item))
            content = path.read_bytes()
            evidence.append({'path_in_distribution': str(item),
                             'sha256': hashlib.sha256(content).hexdigest(),
                             'text': content.decode('utf-8', errors='replace')})
        info = dist.metadata
        entries.append({'name': name, 'version': dist.version,
                        'license_metadata': info.get('License-Expression') or info.get('License'),
                        'project_urls': info.get_all('Project-URL') or [],
                        'license_files': evidence})
    path = ROOT / 'docs' / 'software_license_evidence.json'
    path.write_text(json.dumps({'source': 'Installed pinned wheel metadata and license files',
                               'packages': entries}, indent=2) + '\n', encoding='utf-8', newline='\n')
    for entry in entries:
        value = entry['license_metadata'] or ''
        print(entry['name'], entry['version'], repr(value[:100]),
              'license_files=', len(entry['license_files']))


if __name__ == '__main__':
    main()
