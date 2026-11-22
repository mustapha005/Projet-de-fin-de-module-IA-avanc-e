"""Phase 5 gate for the LaTeX article: structure, references and number provenance.

No LaTeX toolchain is installed on the reference machine, so this script is the only
check before Overleaf compiles. It verifies that the sources are ASCII, balanced and
self-contained, that every citation and cross-reference resolves, that every \\val macro
used is generated, and that every numeric literal in the hand-written prose traces to
paper/numbers*.json, a generated table, or a protocol constant in allowed_constants.json.
It cannot prove the document compiles or count pages; Overleaf does that.

    .venv/Scripts/python.exe scripts/audit_latex.py [--final]
"""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
LATEX = ROOT / 'paper/latex'
# Same number grammar as scripts/audit_numbers.py, so both gates agree.
NUMBER = re.compile(r'(?<![A-Za-z0-9_.])(?<![A-Za-z]-)(?<![A-Za-z]/)(\d[\d,]*(?:\.\d+)?)')
REFERENCE_RANGE = (15, 25)
ABSTRACT_WORDS = (150, 250)
DRAFT = re.compile(r'DRAFT-[A-Z]+|\bTODO\b|\bFIXME\b|\bXXX\b|Given Name Surname|dept\. name of')


def tokens(text: str) -> list[str]:
    return [m.replace(',', '') for m in NUMBER.findall(text)]


def strip_comments(text: str) -> str:
    return re.sub(r'(?<!\\)%.*', '', text)


def prose(text: str) -> str:
    """The hand-written body, with identifiers and generated values removed."""
    text = text.split('\\begin{document}', 1)[-1].split('\\bibliographystyle', 1)[0]
    text = strip_comments(text)
    text = re.sub(r'\\texttt\{[^{}]*\}', ' ', text)                     # file and tag names
    text = re.sub(r'\\(?:cite|ref|label|input|graphicspath)\{[^{}]*\}', ' ', text)
    text = re.sub(r'\\includegraphics(?:\[[^\]]*\])?\{[^{}]*\}', ' ', text)
    text = re.sub(r'10\.\d{4,9}/\S+', ' ', text)                        # DOIs
    text = re.sub(r'CC BY 4\.0', ' ', text)                             # licence identifier
    text = re.sub(r'\\val[A-Za-z]+', ' ', text)                         # generated values
    text = re.sub(r'\\[A-Za-z]+\*?', ' ', text)
    text = re.sub(r'\\.', ' ', text, flags=re.S)
    return re.sub(r'[{}$]', ' ', text)


def allowed_numbers() -> tuple[set[str], dict[str, str]]:
    values = set()
    for name in ('numbers.json', 'numbers_protocol.json'):
        for value in json.loads((ROOT / 'paper' / name).read_text(encoding='utf-8'))['values'].values():
            values.update(tokens(str(value)))
    for path in (ROOT / 'tables').glob('*.md'):
        values.update(tokens(path.read_text(encoding='utf-8')))
    for path in sorted((LATEX / 'tables').glob('*.tex')):
        values.update(tokens(path.read_text(encoding='utf-8')))
    constants = json.loads((ROOT / 'paper/allowed_constants.json').read_text(encoding='utf-8'))
    return values, {str(k): v for k, v in constants['constants'].items()}


def check_balance(name: str, text: str, problems: list[str]) -> None:
    body = strip_comments(text)
    depth = 0
    for match in re.finditer(r'(?<!\\)[{}]', body):
        depth += 1 if match.group() == '{' else -1
        if depth < 0:
            problems.append(f'{name}: unmatched closing brace at offset {match.start()}')
            return
    if depth:
        problems.append(f'{name}: {depth} unclosed brace(s)')
    stack = []
    for match in re.finditer(r'\\(begin|end)\{([^{}]*)\}', body):
        kind, environment = match.groups()
        if kind == 'begin':
            stack.append(environment)
        elif not stack or stack.pop() != environment:
            problems.append(f'{name}: \\end{{{environment}}} does not match the open environment')
            return
    if stack:
        problems.append(f'{name}: unclosed environment(s) {stack}')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--final', action='store_true',
                        help='also refuse draft markers and an out-of-range abstract')
    args = parser.parse_args()
    problems, report = [], {}
    main_path = LATEX / 'main.tex'
    text = main_path.read_text(encoding='utf-8')

    sources = sorted(LATEX.rglob('*.tex')) + [LATEX / 'refs.bib']
    for path in sources:
        content = path.read_text(encoding='utf-8')
        name = path.relative_to(LATEX).as_posix()
        for index, character in enumerate(content):
            if ord(character) > 127:
                line = content.count('\n', 0, index) + 1
                problems.append(f'{name}: non-ASCII {character!r} on line {line}')
                break
        check_balance(name, content, problems)
    report['sources_checked'] = len(sources)

    body = strip_comments(text)
    inputs = re.findall(r'\\input\{([^{}]*)\}', body)
    graphics = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^{}]*)\}', body)
    for target in inputs:
        if not (LATEX / (target if target.endswith('.tex') else target + '.tex')).exists():
            problems.append(f'missing \\input target: {target}')
    for target in graphics:
        if not (LATEX / 'figures' / target).exists():
            problems.append(f'missing figure: {target}')
    if any(t.startswith(('/', '..')) or ':' in t for t in inputs + graphics):
        problems.append('a path leaves paper/latex; the Overleaf project must be self-contained')
    report['inputs'] = len(inputs)
    report['figures'] = len(graphics)

    bib = (LATEX / 'refs.bib').read_text(encoding='utf-8')
    defined_keys = set(re.findall(r'@\w+\{\s*([^,\s]+)\s*,', bib))
    cited = set()
    for group in re.findall(r'\\cite\{([^{}]*)\}', body):
        cited.update(k.strip() for k in group.split(','))
    for key in sorted(cited - defined_keys):
        problems.append(f'citation without a bibliography entry: {key}')
    for key in sorted(defined_keys - cited):
        problems.append(f'bibliography entry never cited: {key}')
    if not REFERENCE_RANGE[0] <= len(defined_keys) <= REFERENCE_RANGE[1]:
        problems.append(f'{len(defined_keys)} references, outside {REFERENCE_RANGE}')
    report['references'] = len(defined_keys)
    report['citations'] = len(cited)

    labels = set(re.findall(r'\\label\{([^{}]*)\}', body))
    for target in sorted(set(re.findall(r'\\ref\{([^{}]*)\}', body)) - labels):
        problems.append(f'\\ref to a missing label: {target}')
    report['labels'] = len(labels)

    defined_macros = set(re.findall(r'\\newcommand\{\\(val[A-Za-z]+)\}',
                                    (LATEX / 'numbers.tex').read_text(encoding='utf-8')))
    used = set()
    for path in sorted(LATEX.rglob('*.tex')):
        if path.name != 'numbers.tex':
            used.update(re.findall(r'\\(val[A-Za-z]+)', strip_comments(
                path.read_text(encoding='utf-8'))))
    for macro in sorted(used - defined_macros):
        problems.append(f'undefined value macro: \\{macro}')
    report['macros_defined'] = len(defined_macros)
    report['macros_used'] = len(used)

    abstract = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', body, re.S)
    if not abstract:
        problems.append('no abstract found')
        words = 0
    else:
        cleaned = re.sub(r'\\val[A-Za-z]+', 'x', abstract.group(1))
        cleaned = re.sub(r'\\[A-Za-z]+\*?|[{}$\\]', ' ', cleaned)
        words = len(cleaned.split())
        if args.final and not ABSTRACT_WORDS[0] <= words <= ABSTRACT_WORDS[1]:
            problems.append(f'abstract is {words} words, outside {ABSTRACT_WORDS}')
    report['abstract_words'] = words

    drafts = DRAFT.findall(body)
    if args.final and drafts:
        problems.append(f'draft or template markers remain: {sorted(set(drafts))}')
    report['draft_markers'] = len(drafts)

    generated, constants = allowed_numbers()
    text_prose = prose(text)
    orphans, by_constant, checked = [], {}, 0
    for token in tokens(text_prose):
        checked += 1
        if token in generated:
            continue
        if token in constants:
            by_constant[token] = constants[token]
            continue
        index = text_prose.find(token)
        orphans.append({'number': token,
                        'context': ' '.join(text_prose[max(0, index - 70):index + 30].split())})
    report['numbers_checked'] = checked
    report['orphan_count'] = len(orphans)
    report['allowed_by_protocol_constant'] = by_constant
    report['orphans'] = orphans
    if orphans:
        problems.append(f'{len(orphans)} prose number(s) without a generated source')

    report['status'] = 'PASS' if not problems else 'FAIL'
    report['problems'] = problems
    out = ROOT / 'docs/reviews/latex_audit.json'
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n',
                   encoding='utf-8', newline='\n')
    print(json.dumps({k: report[k] for k in
                      ('status', 'sources_checked', 'references', 'citations', 'labels',
                       'figures', 'macros_used', 'abstract_words', 'numbers_checked',
                       'orphan_count')}, indent=2))
    for orphan in orphans:
        print('ORPHAN', orphan['number'], '|', orphan['context'])
    for problem in problems:
        if 'without a generated source' not in problem:
            print('PROBLEM', problem)
    sys.exit(0 if not problems else 1)


if __name__ == '__main__':
    main()
