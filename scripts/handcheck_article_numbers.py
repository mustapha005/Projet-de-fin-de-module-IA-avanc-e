"""Phase 5 gate: recompute ten article numbers from the rawest available source.

This is deliberately independent of src/analysis: AUCs are recomputed with scikit-learn
from the stored per-image prediction CSVs, costs and parameter counts are read from the
per-run records, and cohort sizes are counted in the manifests. Each result is compared
with the value the article actually prints, which is the macro body in
paper/latex/numbers.tex. Writes docs/reviews/article_handcheck.json.

    .venv/Scripts/python.exe scripts/handcheck_article_numbers.py
"""
import json
from pathlib import Path
import re
import statistics
import sys

import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
SEEDS = (0, 1, 2)


def macro_bodies() -> dict[str, str]:
    """Macro name -> printed text, taken from the generated numbers.tex."""
    text = (ROOT / 'paper/latex/numbers.tex').read_text(encoding='utf-8')
    bodies = {}
    for name, body, key in re.findall(
            r'\\newcommand\{\\(val[A-Za-z]+)\}\{(.*?)\\xspace\}% (\S+)', text):
        bodies[key] = body.replace('$\\pm$', '+-').replace('$-$', '-').strip()
    return bodies


def cell_runs(method: str, fraction: str) -> list[dict]:
    return [json.loads((ROOT / 'results/main' / f'main_{method}_{fraction}_s{s}.json')
                       .read_text(encoding='utf-8')) for s in SEEDS]


def auc_from_predictions(method: str, fraction: str, cohort: str) -> list[float]:
    """Recompute AUC with scikit-learn from the stored prediction CSVs."""
    values = []
    for run in cell_runs(method, fraction):
        folder = ROOT / run['prediction_folder']
        frame = pd.read_csv(folder / f'{cohort}_predictions.csv')
        values.append(roc_auc_score(frame.label, frame.probability))
    return values


def spread(values: list[float], digits=3) -> str:
    return f'{statistics.mean(values):.{digits}f} +- {statistics.stdev(values):.{digits}f}'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    printed = macro_bodies()
    checks = []

    def record(key, recomputed, source):
        checks.append({'article_key': key, 'printed_in_article': printed.get(key),
                       'recomputed': recomputed, 'recomputed_from': source,
                       'match': printed.get(key) == recomputed})

    for method, fraction, cohort in [('LoRA', '100', 'internal'), ('LoRA', '100', 'external'),
                                     ('LP', '100', 'internal'), ('CNN', '001', 'internal'),
                                     ('PFT', '100', 'external')]:
        key = f'main.{method}.{int(fraction)}.auc_{"in" if cohort == "internal" else "out"}'
        record(key, spread(auc_from_predictions(method, fraction, cohort)),
               f'sklearn roc_auc_score over results/predictions/.../{cohort}_predictions.csv')

    internal = auc_from_predictions('LP', '100', 'internal')
    external = auc_from_predictions('LP', '100', 'external')
    record('main.LP.100.gap.mean',
           f'{statistics.mean([a - b for a, b in zip(internal, external)]):.3f}',
           'per-seed internal minus external AUC, both recomputed from predictions')

    runs = cell_runs('LoRA', '100')
    record('cost.LoRA.100.time',
           f'{statistics.mean(r["fit"]["fit"]["charged_wall_seconds"] for r in runs):.0f} +- '
           f'{statistics.stdev(r["fit"]["fit"]["charged_wall_seconds"] for r in runs):.0f}',
           'charged_wall_seconds in results/main/main_LoRA_100_s*.json')
    record('cost.LoRA.100.epochs',
           spread([float(r['fit']['fit']['epochs_completed']) for r in runs], 1),
           'epochs_completed in results/main/main_LoRA_100_s*.json')
    counts = {r['fit']['fit']['parameters']['trainable'] for r in runs}
    record('params.LoRA', f'{counts.pop():,}' if len(counts) == 1 else 'INCONSISTENT',
           'fit.parameters.trainable in results/main/main_LoRA_100_s*.json')

    record('runs.main', str(len(list((ROOT / 'results/main').glob('*.json')))),
           'file count in results/main/')
    capped = [p.stem for p in sorted((ROOT / 'results/main').glob('*.json'))
              if json.loads(p.read_text(encoding='utf-8'))['fit']['fit']['stop_reason'] == 'time_cap']
    record('runs.cap_hits', str(len(capped)),
           'stop_reason == time_cap in results/main/*.json')

    manifest = pd.read_csv(ROOT / 'data/manifests/breast_external.csv', dtype={'phash': str})
    record('data.breast.total', str(len(manifest)),
           'row count in data/manifests/breast_external.csv')

    failures = [c for c in checks if not c['match']]
    report = {'status': 'PASS' if not failures else 'FAIL', 'checked': len(checks),
              'mismatches': len(failures), 'capped_runs': capped, 'checks': checks}
    out = ROOT / 'docs/reviews/article_handcheck.json'
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'status': report['status'], 'checked': report['checked'],
                      'mismatches': report['mismatches'], 'capped_runs': capped}, indent=2))
    for check in checks:
        flag = 'ok  ' if check['match'] else 'FAIL'
        print(f'{flag} {check["article_key"]}: article={check["printed_in_article"]!r} '
              f'recomputed={check["recomputed"]!r}')
    sys.exit(0 if not failures else 1)


if __name__ == '__main__':
    main()
