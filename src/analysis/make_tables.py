"""Generate every table, contrast, verdict and article number from results/ only."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.collect import (COHORTS, FRACTIONS, METHODS, SEEDS, aligned, load_runs,
                                  run_frame, select)
from src.analysis.hypotheses import all_contrasts, auc_contrast, verdicts
from src.runtime import ROOT, write_json
from src.stats import auc_summary

FRACTION_LABEL = {.01: '1%', .1: '10%', 1.: '100%'}
FRACTION_KEY = {.01: '1', .1: '10', 1.: '100'}
ABLATIONS = [('lora_last2', 'LoRA', FRACTIONS), ('lora_rank4', 'LoRA', [.1]),
             ('lora_rank16', 'LoRA', [.1]), ('pft_depth4', 'PFT', [.1]),
             ('lora_no_augmentation', 'LoRA', [.1])]


def f3(x: float) -> str:
    return f'{x:.3f}'


def pm(values, digits=3) -> str:
    values = np.asarray(values, float)
    return f'{values.mean():.{digits}f} ± {values.std(ddof=1):.{digits}f}'


def ci(bounds) -> str:
    return f'[{bounds[0]:.3f}, {bounds[1]:.3f}]'


def markdown(frame: pd.DataFrame) -> str:
    header = '| ' + ' | '.join(frame.columns) + ' |'
    rule = '|' + '|'.join('---' for _ in frame.columns) + '|'
    body = ['| ' + ' | '.join(str(v) for v in row) + ' |' for row in frame.itertuples(index=False)]
    return '\n'.join([header, rule, *body]) + '\n'


def save(frame: pd.DataFrame, folder: Path, name: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f'{name}.csv').write_text(frame.to_csv(index=False, lineterminator='\n'), encoding='utf-8', newline='\n')
    (folder / f'{name}.md').write_text(markdown(frame), encoding='utf-8', newline='\n')


def main_table(root: Path, runs: list[dict], frame: pd.DataFrame, numbers: dict) -> pd.DataFrame:
    rows = []
    for method in METHODS:
        for fraction in FRACTIONS:
            cell = frame[(frame.variant == 'main') & (frame.method == method) & np.isclose(frame.fraction, fraction)]
            key = f'main.{method}.{FRACTION_KEY[fraction]}'
            row = {'Method': method, 'Labels': f"{FRACTION_LABEL[fraction]} (n={int(cell.n_train.iloc[0])})"}
            for cohort, short in (('internal', 'in'), ('external', 'out')):
                labels, probabilities, _ = aligned(root, select(runs, method, fraction), cohort)
                summary = auc_summary(labels, probabilities)
                row[f'AUC_{short}'] = pm(cell[f'roc_auc_{cohort}'])
                row[f'AUC_{short} 95% CI'] = ci(summary['ci95'])
                numbers[f'{key}.auc_{short}'] = row[f'AUC_{short}']
                numbers[f'{key}.auc_{short}.mean'] = f3(cell[f'roc_auc_{cohort}'].mean())
                numbers[f'{key}.auc_{short}.sd'] = f3(cell[f'roc_auc_{cohort}'].std(ddof=1))
                numbers[f'{key}.auc_{short}.ci'] = row[f'AUC_{short} 95% CI']
            row['Gap'] = pm(cell.auc_gap)
            row['F1_in'] = pm(cell.macro_f1_internal)
            row['F1_out'] = pm(cell.macro_f1_external)
            row['ECE_in'] = pm(cell.ece15_internal)
            row['ECE_out'] = pm(cell.ece15_external)
            numbers[f'{key}.gap'] = row['Gap']
            numbers[f'{key}.gap.mean'] = f3(cell.auc_gap.mean())
            for column in ('F1_in', 'F1_out', 'ECE_in', 'ECE_out'):
                numbers[f'{key}.{column.lower()}'] = row[column]
            rows.append(row)
    return pd.DataFrame(rows)


def cost_table(frame: pd.DataFrame, numbers: dict) -> pd.DataFrame:
    rows = []
    for method in METHODS:
        for fraction in FRACTIONS:
            cell = frame[(frame.variant == 'main') & (frame.method == method) & np.isclose(frame.fraction, fraction)]
            key = f'cost.{method}.{FRACTION_KEY[fraction]}'
            epochs = cell.epochs_completed.dropna()
            row = {'Method': method, 'Labels': FRACTION_LABEL[fraction],
                   'Trainable params': f'{int(cell.trainable_parameters.iloc[0]):,}',
                   'Charged time (s)': pm(cell.charged_seconds, 0),
                   'Time to best (s)': pm(cell.time_to_best_seconds, 0),
                   'Epochs': pm(epochs, 1) if len(epochs) == len(cell) else 'n/a (solver)',
                   'Cap hit': f'{int(cell.cap_hit.sum())}/{len(cell)}',
                   'Peak RSS (GiB)': pm(cell.peak_rss_bytes / 2 ** 30, 2),
                   'Inference (ms/img)': pm((cell.inference_ms_per_image_internal + cell.inference_ms_per_image_external) / 2, 1)}
            for column, name in (('Trainable params', 'params'), ('Charged time (s)', 'time'),
                                 ('Time to best (s)', 'time_to_best'), ('Epochs', 'epochs'),
                                 ('Cap hit', 'cap_hit'), ('Peak RSS (GiB)', 'rss'),
                                 ('Inference (ms/img)', 'inference')):
                numbers[f'{key}.{name}'] = row[column]
            rows.append(row)
    return pd.DataFrame(rows)


def ablation_table(root: Path, runs: list[dict], ablation_runs: list[dict], numbers: dict) -> tuple[pd.DataFrame, list]:
    pool = runs + ablation_runs
    frame = run_frame(pool)
    rows, contrasts = [], []
    for variant, method, fractions in ABLATIONS:
        for fraction in fractions:
            cell = frame[(frame.variant == variant) & np.isclose(frame.fraction, fraction)]
            if len(cell) != len(SEEDS):
                rows.append({'Variant': variant, 'Labels': FRACTION_LABEL[fraction], 'Status': f'missing ({len(cell)}/3 seeds)'})
                continue
            key = f'ablation.{variant}.{FRACTION_KEY[fraction]}'
            row = {'Variant': variant, 'Labels': FRACTION_LABEL[fraction], 'Status': 'complete',
                   'Trainable params': f'{int(cell.trainable_parameters.iloc[0]):,}',
                   'AUC_in': pm(cell.roc_auc_internal), 'AUC_out': pm(cell.roc_auc_external)}
            references = [(method, 'main')] + ([('PFT', 'main')] if variant == 'lora_last2' else [])
            for reference, reference_variant in references:
                for cohort, short in (('internal', 'in'), ('external', 'out')):
                    c = auc_contrast(root, pool, method, reference, fraction, cohort, variant, reference_variant)
                    contrasts.append(c)
                    label = f'Δ vs {reference} ({short})'
                    row[label] = f"{c['mean']:+.3f} {ci(c['ci95'])} {c['direction']}"
                    numbers[f'{key}.vs_{reference}.{short}'] = f"{c['mean']:+.3f}"
            numbers[f'{key}.auc_in'] = row['AUC_in']
            numbers[f'{key}.auc_out'] = row['AUC_out']
            rows.append(row)
    return pd.DataFrame(rows), contrasts


def contrast_frame(contrasts: list[dict]) -> pd.DataFrame:
    return pd.DataFrame([{'kind': c['kind'], 'a': f"{c['variant_a']}:{c['a']}", 'b': f"{c['variant_b']}:{c['b']}",
                          'fraction': c['fraction'], 'cohort': c['cohort'], 'mean_difference': c['mean'],
                          'larger_method_sd': c['larger_method_sd'], 'ci95_lower': c['ci95'][0],
                          'ci95_upper': c['ci95'][1], 'per_seed': json.dumps(c['per_seed']),
                          'direction': c['direction']} for c in contrasts])


def verdict_markdown(result: dict) -> str:
    lines = ['| Hypothesis | Clause | Verdict |', '|---|---|---|']
    for name in ('H1', 'H2'):
        for clause, verdict in result[name]['clauses'].items():
            lines.append(f'| {name} | {clause} | {verdict} |')
        lines.append(f"| {name} | **compound** | **{result[name]['verdict']}** |")
    lines.append(f"| H3 | six internal FM-vs-CNN contrasts | **{result['H3']['verdict']}** |")
    lines.append(f"| H3 (secondary) | six external FM-vs-CNN contrasts | {result['H3_external_secondary']['verdict']} |")
    return '\n'.join(lines) + '\n\n' + result['rule'] + '\n'


def build(root: Path, out_tables: Path, out_numbers: Path) -> dict:
    runs = load_runs(root, 'main')
    ablation_runs = load_runs(root, 'ablation') if (root / 'results/ablation').exists() else []
    frame = run_frame(runs)
    if len(frame) != len(METHODS) * len(FRACTIONS) * len(SEEDS):
        raise ValueError(f'Main grid incomplete: {len(frame)}/36 runs; no tables are generated')
    numbers: dict[str, str] = {}
    save(frame.drop(columns=[]), out_tables, 'run_level')
    save(main_table(root, runs, frame, numbers), out_tables, 'main_results')
    save(cost_table(frame, numbers), out_tables, 'cost')
    contrasts = all_contrasts(root, runs)
    trainable = frame[frame.variant == 'main'].groupby('method').trainable_parameters.mean().to_dict()
    result = verdicts(contrasts, trainable)
    ablations, ablation_contrasts = ablation_table(root, runs, ablation_runs, numbers)
    save(ablations, out_tables, 'ablations')
    save(contrast_frame(contrasts + ablation_contrasts), out_tables, 'contrasts')
    write_json(out_tables / 'hypotheses.json', result)
    (out_tables / 'hypotheses.md').write_text(verdict_markdown(result), encoding='utf-8', newline='\n')
    for name in ('H1', 'H2', 'H3'):
        numbers[f'verdict.{name}'] = result[name]['verdict']
        for clause, verdict in result[name].get('clauses', {}).items():
            numbers[f'verdict.{name}.{clause}'] = verdict
    numbers['verdict.H3_external'] = result['H3_external_secondary']['verdict']
    for method, count in trainable.items():
        numbers[f'params.{method}'] = f'{int(count):,}'
    numbers['runs.main'] = str(len(frame))
    numbers['runs.ablation'] = str(len(ablation_runs))
    numbers['runs.cap_hits'] = str(int(frame.cap_hit.sum()))
    numbers['compute.main_charged_hours'] = f'{frame.charged_seconds.sum() / 3600:.1f}'
    numbers['compute.main_cpu_hours'] = f'{frame.process_cpu_seconds.sum() / 3600:.1f}'
    write_json(out_numbers, {'source': 'Generated by src/analysis/make_tables.py from results/ only',
                             'values': dict(sorted(numbers.items()))})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='Project root holding results/')
    args = parser.parse_args()
    result = build(args.root, args.root / 'tables', args.root / 'paper/numbers.json')
    print(json.dumps({k: result[k]['verdict'] for k in ('H1', 'H2', 'H3', 'H3_external_secondary')}, indent=2))


if __name__ == '__main__':
    main()
