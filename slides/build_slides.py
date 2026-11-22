"""Build the editable 16:9 defense deck from generated numbers, tables and figures.

Run with the paper environment from the project root:
    .venv-paper/Scripts/python.exe slides/build_slides.py [--final]
Text boxes and tables are native PowerPoint objects; figures are generated PNGs (300 dpi).
Every number comes from paper/numbers*.json or tables/*.csv, so it matches the article.
"""
import argparse
import csv
import json
from pathlib import Path
import re

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'slides/build/SDIA2026_SAN-1_GROUP_13_presentation.pptx'
INK, MUTED, ACCENT, RULE = RGBColor(0x0b, 0x0b, 0x0b), RGBColor(0x52, 0x51, 0x4e), RGBColor(0x2a, 0x78, 0xd6), RGBColor(0xd9, 0xd8, 0xd4)
FILL = {'LP': RGBColor(0x2a, 0x78, 0xd6), 'PFT': RGBColor(0xeb, 0x68, 0x34), 'LoRA': RGBColor(0x1b, 0xaf, 0x7a), 'CNN': RGBColor(0x6b, 0x6a, 0x66)}
MEMBERS = ['Mustapha AARAB', 'Aya AGRIGAH', 'Badr Eddine TOUBANI']
PLACEHOLDER = re.compile(r'\{\{([A-Za-z0-9_.%-]+)\}\}')

# (title, bullets, visual, notes, presenter index). visual: None | ('figure', name) |
# ('table', csv name, columns) | ('methods',). DRAFT- bullets are rewritten after results.
SLIDES = [
    ('Frugal adaptation of a self-supervised ViT for breast ultrasound',
     ['Linear probing vs partial fine-tuning vs LoRA, against a scratch CNN',
      'Fixed CPU budget · 1 / 10 / 100% labels · unseen acquisition center',
      'Mustapha AARAB · Aya AGRIGAH · Badr Eddine TOUBANI — ENSET Mohammedia, Master SDIA'],
     None, 'Introduce the team and the one-sentence question. Stress: measured answer, not an application.', 0),
    ('Problem and gap',
     ['Foundation models promise transfer, but labels, compute and a new site constrain real use',
      'Reviews list compute cost, data scarcity and domain adaptation as open problems',
      'Prior adaptation comparisons use GPUs and mostly one in-distribution test set',
      'Gap: a controlled CPU-budget comparison that is also tested on an unseen center'],
     None, 'Cite the 2026 IEEE TMI review (Niu et al.) and PEFT studies (Lian; Dutt). Our angle: equal wall-clock cap on a laptop CPU plus external test.', 0),
    ('Research question and pre-registered hypotheses',
     ['Q: Does the LP / PFT / LoRA ranking depend on the label fraction, and does it survive a center change?',
      'H1: LP not worse than LoRA at 1%; LoRA beats LP at 100% (internal AUC)',
      'H2: Ranking preserved externally; gap does not grow with trainable parameters',
      'H3: All three FM strategies beat the scratch CNN at 1% and 10%',
      'Counts only if |Δ| > larger seed SD AND 95% paired-bootstrap CI excludes 0'],
     None, 'Hypotheses and the decision rule were committed before any training (protocol-frozen tag). Without a margin, a tie cannot support "not worse".', 0),
    ('Data and center shift',
     ['Internal: BUSI (Egypt) — {{data.busi.binary_raw}} benign/malignant images → {{data.busi.retained}} after near-duplicate removal',
      'pHash ≤ {{data.busi.hamming}} bits ∪ published duplicate list; {{data.phash_only.crossing_pairs}} crossing pairs found and fixed before freeze',
      'Split 70/15/15 (seed {{protocol.split_seed}}): {{data.busi.train}} / {{data.busi.val}} / {{data.busi.test}}',
      'Label fractions per seed: {{data.subset.1.n}} / {{data.subset.10.n}} / {{data.subset.100.n}} images (floor 4 per class)',
      'External: BrEaST (Poland) — {{data.breast.total}} cases, used only for final evaluation'],
     None, 'Explain why nominal 1% is really {{data.subset.1.actual_pct}}%: the four-per-class floor. Patient IDs are unavailable, so independence is image-level only.', 0),
    ('Four strategies, one encoder', [], ('methods',),
     'DINOv2 ViT-S/14 for LP, PFT, LoRA; ResNet-18 from scratch as the honest baseline. Same augmentation, epochs, cap and tuning budget for all.', 0),
    ('What "fixed compute budget" means',
     ['Every run: same epoch limit ({{protocol.max_epochs}}) and same wall-clock cap T_MAX = {{protocol.cap_seconds}} s',
      'Reference laptop: {{hw.cpu}}, {{protocol.threads}} threads, {{hw.ram_gib}} GiB RAM, no GPU',
      'Charged: loading, preprocessing, LP feature extraction (even on cache hits), training, validation, checkpoints',
      'T_MAX set from a pre-freeze benchmark; a parent supervisor enforces it',
      'Logged per run: trainable params, time, time-to-best, CPU time, peak RAM, cap hit'],
     None, 'LoRA trains few parameters but still back-propagates through the whole network: parameter count is not compute.', 1),
    ('Protocol rigor',
     ['Splits, seeds, search, stopping, threshold, statistics, cap, machine frozen in Git before any run',
      'Tuning: seed 0, 10% only, ≤ 6 configurations per method, validation AUC',
      'Threshold: max validation macro-F1, applied unchanged to both tests',
      'One test evaluation per reported run; two post-hoc exceptions disclosed',
      '3 seeds × 3 fractions × 4 methods = 36 runs; class-stratified paired bootstrap ({{protocol.bootstrap_resamples}} resamples)'],
     None, 'How do we know the test set was used once? The development loader refuses test rows and evaluation is a lock-file transaction. Post-hoc exceptions, no selection: one cell rerun twice for reproducibility, saliency on 10 external images.', 1),
    ('Main results', ['DRAFT-RESULTS'], ('table', 'main_results', ['Method', 'Labels', 'AUC_in', 'AUC_out', 'Gap']),
     'DRAFT-NOTES', 1),
    ('Does the ranking survive the center change?', ['DRAFT-RESULTS'], ('figure', 'fig_learning_curve'), 'DRAFT-NOTES', 1),
    ('Cost versus performance', ['DRAFT-RESULTS'], ('figure', 'fig_cost_performance'), 'DRAFT-NOTES', 1),
    ('Ablations: where and how to adapt', ['DRAFT-RESULTS'], ('figure', 'fig_ablations'), 'DRAFT-NOTES', 2),
    ('Error analysis on the external center', ['DRAFT-RESULTS'], ('figure', 'fig_error_overlap'), 'DRAFT-NOTES', 2),
    ('Answers to H1–H3',
     ['H1: {{verdict.H1}}', 'H2: {{verdict.H2}}', 'H3: {{verdict.H3}} (external analogue: {{verdict.H3_external}})', 'DRAFT-RESULTS'],
     None, 'DRAFT-NOTES', 2),
    ('Limitations and threats to validity',
     ['Small tests ({{data.busi.test}} internal, {{data.breast.total}} external): wide intervals',
      'Image-level split only; BUSI has no patient IDs',
      'Center shift confounded with scanner, population and reference standard',
      'One backbone, binary task, CPU-only; wall-clock cap sensitive to machine load',
      'Exploratory verdicts, no multiplicity correction'],
     None, 'Be direct: these limits bound the claim; they do not invalidate the measurement.', 2),
    ('Conclusion and perspectives', ['DRAFT-RESULTS'], None, 'DRAFT-NOTES', 2),
]


def values() -> dict[str, str]:
    merged = {}
    for name in ('numbers_protocol.json', 'numbers.json'):
        path = ROOT / 'paper' / name
        if path.exists():
            merged.update(json.loads(path.read_text(encoding='utf-8'))['values'])
    return merged


def fill(text: str, numbers: dict, missing: list) -> str:
    def replace(match):
        if match.group(1) in numbers:
            return numbers[match.group(1)]
        missing.append(match.group(1))
        return f'[[{match.group(1)}]]'
    return PLACEHOLDER.sub(replace, text)


def textbox(slide, left, top, width, height, lines, size=18, color=INK, bold=False, bullet=True):
    box = slide.shapes.add_textbox(left, top, width, height)
    frame = box.text_frame
    frame.word_wrap = True
    for i, line in enumerate(lines):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        p.text = ('•  ' if bullet else '') + line
        p.space_after = Pt(8)
        for run in p.runs:
            run.font.size, run.font.color.rgb, run.font.bold, run.font.name = Pt(size), color, bold, 'Calibri'
    return box


def header(slide, title, number, presenter):
    textbox(slide, Inches(.5), Inches(.3), Inches(12.3), Inches(.8), [title], 30, INK, True, False)
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(.5), Inches(1.1), Inches(1.2), Emu(38100))
    line.fill.solid()
    line.fill.fore_color.rgb = ACCENT
    line.line.fill.background()
    textbox(slide, Inches(.5), Inches(7.0), Inches(12.3), Inches(.4),
            [f'SAN-1 · GROUP_13 · {number}/{len(SLIDES)} · presenter: {MEMBERS[presenter]}'], 11, MUTED, False, False)


def methods_diagram(slide, numbers, missing):
    rows = [('LP', 'Frozen DINOv2 → cached features → logistic regression', '{{params.LP}} trainable'),
            ('PFT', 'Frozen blocks 1–10 → train blocks 11–12 + norm + head', '{{params.PFT}} trainable'),
            ('LoRA', 'Frozen DINOv2 + rank-8 adapters on q/k/v in all 12 blocks + head', '{{params.LoRA}} trainable'),
            ('CNN', 'ResNet-18 from random initialization, all layers trained', '{{params.CNN}} trainable')]
    for i, (name, text, tag) in enumerate(rows):
        top = Inches(1.6 + 1.25 * i)
        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(.6), top, Inches(1.6), Inches(.9))
        badge.fill.solid()
        badge.fill.fore_color.rgb = FILL[name]
        badge.line.fill.background()
        badge.text_frame.text = name
        for p in badge.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            for run in p.runs:
                run.font.size, run.font.bold, run.font.color.rgb = Pt(22), True, RGBColor(255, 255, 255)
        box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2.4), top, Inches(10.3), Inches(.9))
        box.fill.solid()
        box.fill.fore_color.rgb = RGBColor(0xf4, 0xf3, 0xf0)
        box.line.color.rgb = RULE
        box.text_frame.text = f'{text}   ({fill(tag, numbers, missing)})'
        for p in box.text_frame.paragraphs:
            for run in p.runs:
                run.font.size, run.font.color.rgb = Pt(17), INK


def native_table(slide, name, columns, top=Inches(1.5)):
    path = ROOT / 'tables' / f'{name}.csv'
    if not path.exists():
        textbox(slide, Inches(.6), top, Inches(12), Inches(1), [f'[[table:{name} not generated]]'], 18, MUTED)
        return
    with path.open(encoding='utf-8') as stream:
        rows = [[row[c] for c in columns] for row in csv.DictReader(stream)]
    shape = slide.shapes.add_table(len(rows) + 1, len(columns), Inches(.6), top, Inches(12.1), Inches(.3 * (len(rows) + 1)))
    for j, column in enumerate(columns):
        shape.table.cell(0, j).text = column
    for i, row in enumerate(rows, start=1):
        for j, value in enumerate(row):
            shape.table.cell(i, j).text = value
    for cell in (shape.table.cell(i, j) for i in range(len(rows) + 1) for j in range(len(columns))):
        for p in cell.text_frame.paragraphs:
            for run in p.runs:
                run.font.size = Pt(12)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    numbers, missing, drafts = values(), [], []
    deck = Presentation()
    deck.slide_width, deck.slide_height = Inches(13.333), Inches(7.5)
    blank = deck.slide_layouts[6]
    for number, (title, bullets, visual, notes, presenter) in enumerate(SLIDES, start=1):
        slide = deck.slides.add_slide(blank)
        header(slide, fill(title, numbers, missing), number, presenter)
        lines = [fill(b, numbers, missing) for b in bullets]
        drafts += [line for line in lines + [notes] if 'DRAFT-' in line]
        width = Inches(5.6) if visual and visual[0] == 'figure' else Inches(12.2)
        if lines:
            textbox(slide, Inches(.6), Inches(1.5), width, Inches(5.2), lines, 18 if width == Inches(12.2) else 16)
        if visual and visual[0] == 'figure':
            path = ROOT / 'figures' / f'{visual[1]}.png'
            if path.exists():
                slide.shapes.add_picture(str(path), Inches(6.5), Inches(1.5), width=Inches(6.4))
            else:
                missing.append(f'figure:{visual[1]}')
        elif visual and visual[0] == 'table':
            native_table(slide, visual[1], visual[2], Inches(2.4))
        elif visual and visual[0] == 'methods':
            methods_diagram(slide, numbers, missing)
        slide.notes_slide.notes_text_frame.text = (f'Presenter: {MEMBERS[presenter]}.\n' + fill(notes, numbers, missing))
    if args.final and (missing or drafts):
        raise SystemExit(f'Final deck refused. Missing: {sorted(set(missing))}; draft slides: {len(drafts)}')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    deck.save(OUT)
    print(json.dumps({'slides': len(SLIDES), 'missing': sorted(set(missing)), 'draft_markers': len(drafts),
                      'output': str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == '__main__':
    main()
