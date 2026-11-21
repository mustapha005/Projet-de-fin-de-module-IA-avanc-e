"""Build the article: article.md + numbers + tables -> DOCX (pandoc) -> PDF (Word) -> page PNGs.

Run with the paper environment from the project root:
    .venv-paper/Scripts/python.exe paper/build.py            # draft: missing numbers shown as [[key]]
    .venv-paper/Scripts/python.exe paper/build.py --final    # fails on any missing number or DRAFT marker
"""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import subprocess

import fitz
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import pypandoc

PAPER = Path(__file__).resolve().parent
ROOT = PAPER.parent
BUILD = PAPER / 'build'
NAME = 'SDIA2026_SAN-1_GROUP_13_article'
PLACEHOLDER = re.compile(r'\{\{([A-Za-z0-9_.%-]+)\}\}')
TABLE = re.compile(r'^\{\{table:([a-z0-9_]+)(:wide)?\|(.+?)\}\}\s*$', re.M)
WIDE = re.compile(r'^\{\{wide-(start|end)\}\}\s*$', re.M)


def numbers() -> dict[str, str]:
    values = {}
    for name in ('numbers_protocol.json', 'numbers.json'):
        path = PAPER / name
        if path.exists():
            values.update(json.loads(path.read_text(encoding='utf-8'))['values'])
    return values


def marker(kind: str) -> str:
    return f'\n::: {{custom-style="SectionMarker"}}\n{kind}\n:::\n'


def fill(text: str, final: bool) -> tuple[str, list[str]]:
    missing = []

    def table(match):
        name, wide, caption = match.groups()
        path = ROOT / 'tables' / f'{name}.md'
        if not path.exists():
            missing.append(f'table:{name}')
            body = f'[[table:{name} not generated]]'
        else:
            body = path.read_text(encoding='utf-8').strip()
        block = f'\n{body}\n\nTable: {caption}\n'
        return (marker('WIDE-START') + block + marker('WIDE-END')) if wide else block

    text = TABLE.sub(table, text)
    text = WIDE.sub(lambda m: marker('WIDE-' + m.group(1).upper()), text)
    values = numbers()

    def number(match):
        key = match.group(1)
        if key in values:
            return values[key]
        missing.append(key)
        return f'[[{key}]]'

    text = PLACEHOLDER.sub(number, text)
    if final:
        drafts = re.findall(r'DRAFT-[A-Z]+', text)
        if missing or drafts:
            raise SystemExit(f'Final build refused. Missing: {sorted(set(missing))}; draft markers: {drafts}')
    return text, missing


def section_properties(template, columns: int):
    properties = copy.deepcopy(template)
    for child in list(properties):
        if child.tag in (qn('w:cols'), qn('w:type')):
            properties.remove(child)
    kind = OxmlElement('w:type')
    kind.set(qn('w:val'), 'continuous')
    properties.insert(0, kind)
    cols = OxmlElement('w:cols')
    cols.set(qn('w:num'), str(columns))
    cols.set(qn('w:space'), '283')
    properties.append(cols)
    return properties


def postprocess(path: Path) -> None:
    """Single-column title block and wide blocks; ruled tables; continuous sections."""
    document = Document(path)
    body = document.element.body
    final = body.sectPr
    kind = OxmlElement('w:type')
    kind.set(qn('w:val'), 'continuous')
    final.insert(0, kind)
    ending_columns = {'TITLE-END': 1, 'WIDE-START': 2, 'WIDE-END': 1}
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if paragraph.style.name == 'SectionMarker' and text in ending_columns:
            for run in paragraph.runs:
                run.text = ''
            paragraph._p.get_or_add_pPr().append(section_properties(final, ending_columns[text]))
    for table in document.tables:
        properties = table._tbl.tblPr
        borders = OxmlElement('w:tblBorders')
        for edge in ('top', 'bottom'):
            element = OxmlElement(f'w:{edge}')
            element.set(qn('w:val'), 'single')
            element.set(qn('w:sz'), '8')
            element.set(qn('w:color'), '000000')
            borders.append(element)
        properties.append(borders)
        header = table.rows[0]
        for cell in header.cells:
            shading = cell._tc.get_or_add_tcPr()
            bottom = OxmlElement('w:tcBorders')
            line = OxmlElement('w:bottom')
            line.set(qn('w:val'), 'single')
            line.set(qn('w:sz'), '4')
            bottom.append(line)
            shading.append(bottom)
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.first_line_indent = 0
                    for run in p.runs:
                        run.font.size = document.styles['Normal'].font.size * 0.7
    document.save(path)


def to_pdf(docx: Path, pdf: Path) -> None:
    """Microsoft Word export (LibreOffice is unavailable on the reference laptop; D014)."""
    script = (f"$w = New-Object -ComObject Word.Application; $w.Visible = $false; "
              f"$d = $w.Documents.Open('{docx}', $false, $true); "
              f"$d.ExportAsFixedFormat('{pdf}', 17); $d.Close($false); $w.Quit()")
    subprocess.run(['powershell', '-NoProfile', '-Command', script], check=True)


def inspect(pdf: Path, abstract: str) -> dict:
    pages = BUILD / 'pages'
    pages.mkdir(parents=True, exist_ok=True)
    for old in pages.glob('*.png'):
        old.unlink()
    with fitz.open(pdf) as document:
        reference_page = None
        for index, page in enumerate(document):
            page.get_pixmap(dpi=110).save(pages / f'page-{index + 1:02d}.png')
            if reference_page is None and re.search(r'^\s*References\s*$', page.get_text(), re.M | re.I):
                reference_page = index + 1
        total = len(document)
    words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.%-]*", abstract))
    return {'pages_total': total, 'references_start_page': reference_page,
            'pages_before_references_page': (reference_page - 1) if reference_page else total,
            'abstract_words': words, 'page_images': str(pages.relative_to(ROOT))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    BUILD.mkdir(exist_ok=True)
    source = (PAPER / 'article.md').read_text(encoding='utf-8')
    filled, missing = fill(source, args.final)
    abstract = re.search(r'abstract: \|\n((?:  .*\n)+)', filled).group(1)
    filled_path = BUILD / 'article.filled.md'
    filled_path.write_text(filled, encoding='utf-8', newline='\n')
    docx = BUILD / f'{NAME}.docx'
    pypandoc.convert_file(str(filled_path), 'docx', outputfile=str(docx), extra_args=[
        '--citeproc', f'--bibliography={PAPER / "refs.bib"}', f'--csl={PAPER / "ieee.csl"}',
        f'--reference-doc={PAPER / "template_2col.docx"}', f'--lua-filter={PAPER / "ieee_headings.lua"}',
        f'--resource-path={PAPER}{os.pathsep}{ROOT}'])
    postprocess(docx)
    pdf = BUILD / f'{NAME}.pdf'
    to_pdf(docx, pdf)
    report = {'mode': 'final' if args.final else 'draft', 'missing_numbers': sorted(set(missing)),
              **inspect(pdf, abstract), 'docx': str(docx.relative_to(ROOT)), 'pdf': str(pdf.relative_to(ROOT))}
    (BUILD / 'build_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
