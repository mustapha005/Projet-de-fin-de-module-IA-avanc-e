"""Phase 5 gate: every number in the built article must trace to a generated source.

Allowed sources: values in paper/numbers.json and paper/numbers_protocol.json (generated
from results/, data reports and the frozen contract), cells of the generated tables in
tables/, and the protocol design constants in paper/allowed_constants.json (each with a
justification). Citation markers, identifiers such as ResNet-18 or H1, and the reference
list are excluded. Run with the paper environment (python-docx).
"""
import argparse
import json
from pathlib import Path
import re
import sys

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
NUMBER = re.compile(r'(?<![A-Za-z0-9_.])(?<![A-Za-z]-)(?<![A-Za-z]/)(\d[\d,]*(?:\.\d+)?)')
CITATION = re.compile(r'\[\d+(?:\s*[,–-]\s*\d+)*\]')


def tokens(text: str) -> list[str]:
    return [m.replace(',', '') for m in NUMBER.findall(CITATION.sub(' ', text))]


def document_text(path: Path) -> list[str]:
    """Paragraph and table-cell texts before the References heading."""
    document = Document(path)
    texts = []
    for block in document.element.body.iterchildren():
        tag = block.tag.rsplit('}', 1)[-1]
        if tag == 'p':
            text = ''.join(node.text or '' for node in block.iter() if node.tag.endswith('}t'))
            if re.fullmatch(r'\s*References\s*', text):
                break
            texts.append(text)
        elif tag == 'tbl':
            for node in block.iter():
                if node.tag.endswith('}tc'):
                    texts.append(''.join(t.text or '' for t in node.iter() if t.tag.endswith('}t')))
    return texts


def allowed() -> tuple[set[str], dict[str, str]]:
    values = set()
    for name in ('numbers.json', 'numbers_protocol.json'):
        path = ROOT / 'paper' / name
        if path.exists():
            for value in json.loads(path.read_text(encoding='utf-8'))['values'].values():
                values.update(tokens(str(value)))
    for path in (ROOT / 'tables').glob('*.md'):
        values.update(tokens(path.read_text(encoding='utf-8')))
    constants = json.loads((ROOT / 'paper/allowed_constants.json').read_text(encoding='utf-8'))['constants']
    return values, {str(k): v for k, v in constants.items()}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--docx', type=Path, default=ROOT / 'paper/build/SDIA2026_SAN-1_GROUP_13_article.docx')
    args = parser.parse_args()
    generated, constants = allowed()
    orphans, by_constant, checked = [], {}, 0
    for text in document_text(args.docx):
        for token in tokens(text):
            checked += 1
            if token in generated:
                continue
            if token in constants:
                by_constant[token] = constants[token]
                continue
            start = text.find(token)
            orphans.append({'number': token, 'context': text[max(0, start - 60):start + 40]})
    report = {'status': 'PASS' if not orphans else 'FAIL', 'numbers_checked': checked,
              'orphan_count': len(orphans), 'orphans': orphans,
              'allowed_by_protocol_constant': by_constant}
    out = ROOT / 'docs/reviews/number_audit.json'
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: report[k] for k in ('status', 'numbers_checked', 'orphan_count')}, indent=2))
    for orphan in orphans:
        print('ORPHAN', orphan['number'], '|', orphan['context'].replace('\n', ' '))
    sys.exit(0 if not orphans else 1)


if __name__ == '__main__':
    main()
