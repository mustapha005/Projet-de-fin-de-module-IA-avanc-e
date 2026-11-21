"""Analysis code on synthetic fixtures only: no real test prediction is read."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from src.analysis import hypotheses as H
from src.analysis.collect import FRACTIONS, METHODS, SEEDS, aligned, load_runs, select
from src.analysis.make_tables import build
from src.runtime import sha256, write_json
from src.stats import metrics

PARAMS = {'LP': 769, 'LoRA': 222722, 'PFT': 3550000, 'CNN': 11177538}


def write_run(root: Path, name: str, method: str, fraction: float, seed: int, signal: dict,
              purpose: str = 'main', variant: str | None = None):
    """One fake final record whose metrics are recomputed from its fake predictions."""
    rng = np.random.default_rng([seed, METHODS.index(method), int(fraction * 100), len(name)])
    folder = root / 'results/predictions' / name
    folder.mkdir(parents=True, exist_ok=True)
    cohorts, threshold = {}, .5
    for cohort, (n0, n1) in {'internal': (30, 20), 'external': (40, 30)}.items():
        labels = np.r_[np.zeros(n0, int), np.ones(n1, int)]
        logits = signal[cohort] * (2 * labels - 1) + rng.normal(size=labels.size)
        frame = pd.DataFrame({'image_id': [f'{cohort}/img{i:03d}' for i in range(labels.size)],
                              'label': labels, 'probability': 1 / (1 + np.exp(-logits))})
        path = folder / f'{cohort}_predictions.csv'
        path.write_text(frame.to_csv(index=False, lineterminator='\n', float_format='%.17g'), newline='\n')
        cohorts[cohort] = {'predictions_file': path.name, 'predictions_sha256': sha256(path),
                           'n_images': len(frame), 'inference_seconds_per_image': .05,
                           'metrics': metrics(frame.label, frame.probability, threshold)}
    config = {'method': method, 'fraction': fraction, 'seed': seed, 'purpose': purpose}
    if variant:
        config['ablation_name'] = variant
    capped = method == 'LoRA' and fraction == 1.
    record = {'status': 'PASS', 'config': config, 'prediction_folder': f'results/predictions/{name}',
              'evaluation': {'threshold': threshold, 'cohorts': cohorts},
              'auc_gap': cohorts['internal']['metrics']['roc_auc'] - cohorts['external']['metrics']['roc_auc'],
              'fit': {'supervisor_killed_at_cap': capped, 'process_cpu_seconds': 1000. + seed,
                      'peak_rss_bytes': 3 * 2 ** 30,
                      'fit': {'parameters': {'trainable': PARAMS[method], 'total': PARAMS[method] + 22e6},
                              'n_train': {.01: 8, .1: 33, 1.: 341}[fraction],
                              'stop_reason': 'time_cap' if capped else 'early_stopping',
                              'epochs_completed': None if method == 'LP' else 10 + seed,
                              'charged_wall_seconds': 1440. if capped else 600. + seed,
                              'cache_hit': False, 'cache_credit_seconds': 0.},
                      'best': {'charged_seconds_at_selection': 300. + seed, 'epoch': 3, 'validation_auc': .8}}}
    write_json(root / 'results' / purpose / f'{name}.json', record)


def fixture(root: Path, signals) -> None:
    for method in METHODS:
        for fraction in FRACTIONS:
            for seed in SEEDS:
                write_run(root, f'main_{method}_{int(100 * fraction):03d}_s{seed}', method, fraction, seed,
                          signals(method, fraction))


def contrast(a, b, fraction, cohort, direction, kind='auc'):
    return {'kind': kind, 'a': a, 'b': b, 'variant_a': 'main', 'variant_b': 'main', 'fraction': fraction,
            'cohort': cohort, 'mean': .1 if direction.startswith('a') else -.1, 'ci95': [.05, .15],
            'per_seed': [.1, .1, .1], 'per_seed_ci95': [[0, .2]] * 3, 'larger_method_sd': .01,
            'direction': direction}


def grid(default='no_detectable_difference', overrides=None):
    """All stored contrasts in combinations(METHODS) order with chosen directions."""
    overrides = overrides or {}
    out = []
    for fraction in FRACTIONS:
        for i, a in enumerate(METHODS):
            for b in METHODS[i + 1:]:
                for cohort in ('internal', 'external'):
                    out.append(contrast(a, b, fraction, cohort, overrides.get(('auc', a, b, fraction, cohort), default)))
                gap_default = default.replace('better', 'larger_gap')
                out.append(contrast(a, b, fraction, 'internal_minus_external',
                                    overrides.get(('gap', a, b, fraction), gap_default), 'gap'))
    return out


class VerdictRules(unittest.TestCase):
    def test_flip_reorients_direction_and_interval(self):
        c = H.find(grid(overrides={('auc', 'LP', 'LoRA', .01, 'internal'): 'b_better'}), 'auc', 'LoRA', 'LP', .01, 'internal')
        self.assertEqual(c['direction'], 'a_better')
        self.assertEqual(c['ci95'], [-.15, -.05])
        self.assertAlmostEqual(c['mean'], .1)

    def test_h1_clauses(self):
        nothing = H.h1(grid())
        self.assertEqual(nothing['verdict'], 'inconclusive')
        both = H.h1(grid(overrides={('auc', 'LP', 'LoRA', .01, 'internal'): 'a_better',
                                    ('auc', 'LP', 'LoRA', 1., 'internal'): 'b_better'}))
        self.assertEqual(both['clauses'], {'LP_not_worse_than_LoRA_at_1pct': 'supported',
                                           'LoRA_beats_LP_at_100pct': 'supported'})
        self.assertEqual(both['verdict'], 'supported')
        reject = H.h1(grid(overrides={('auc', 'LP', 'LoRA', .01, 'internal'): 'b_better'}))
        self.assertEqual(reject['verdict'], 'rejected')
        # A tie never supports "not worse": no noninferiority margin exists.
        self.assertEqual(nothing['clauses']['LP_not_worse_than_LoRA_at_1pct'], 'inconclusive')

    def test_h2_ranking_and_gap(self):
        order = {'LP': 769, 'LoRA': 222722, 'PFT': 3550000}
        self.assertEqual(H.h2(grid(), order)['verdict'], 'inconclusive')
        self.assertEqual(H.h2(grid(), order)['trainable_order'], ['LP', 'LoRA', 'PFT'])
        opposite = grid(overrides={('auc', 'LP', 'PFT', .1, 'internal'): 'a_better',
                                   ('auc', 'LP', 'PFT', .1, 'external'): 'b_better'})
        self.assertEqual(H.h2(opposite, order)['clauses']['ranking_preserved_externally'], 'rejected')
        # Stored (LP, LoRA) gap with b larger means higher-count LoRA has the larger gap: rejects.
        grows = grid(overrides={('gap', 'LP', 'LoRA', 1.): 'b_larger_gap'})
        self.assertEqual(H.h2(grows, order)['clauses']['gap_does_not_grow_with_trainable_parameters'], 'rejected')
        shrink = {}
        for f in FRACTIONS:
            shrink[('gap', 'LP', 'LoRA', f)] = 'a_larger_gap'   # LP gap larger: LoRA − LP negative
            shrink[('gap', 'LP', 'PFT', f)] = 'a_larger_gap'
            shrink[('gap', 'PFT', 'LoRA', f)] = 'b_larger_gap'  # LoRA gap larger: PFT − LoRA negative
        self.assertEqual(H.h2(grid(overrides=shrink), order)['clauses']['gap_does_not_grow_with_trainable_parameters'], 'supported')
        same = grid(default='a_better')
        self.assertEqual(H.h2(same, order)['clauses']['ranking_preserved_externally'], 'supported')

    def test_h3_requires_all_six(self):
        five = {('auc', m, 'CNN', f, 'internal'): 'a_better' for m in ('LP', 'PFT', 'LoRA') for f in (.01, .1)}
        self.assertEqual(H.h3(grid(overrides=five))['verdict'], 'supported')
        del five[('auc', 'LoRA', 'CNN', .1, 'internal')]
        self.assertEqual(H.h3(grid(overrides=five))['verdict'], 'inconclusive')
        five[('auc', 'LoRA', 'CNN', .1, 'internal')] = 'b_better'
        self.assertEqual(H.h3(grid(overrides=five))['verdict'], 'rejected')


class EndToEnd(unittest.TestCase):
    def test_build_from_synthetic_results(self):
        def signals(method, fraction):
            strong = {'LP': 2.5, 'PFT': 2.5, 'LoRA': 2.5, 'CNN': .0}[method]
            return {'internal': strong, 'external': strong / 2}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fixture(root, signals)
            result = build(root, root / 'tables', root / 'paper/numbers.json')
            self.assertEqual(result['H3']['verdict'], 'supported')
            numbers = json.loads((root / 'paper/numbers.json').read_text())['values']
            runs = load_runs(root)
            labels, probabilities, _ = aligned(root, select(runs, 'PFT', .1), 'external')
            from sklearn.metrics import roc_auc_score
            aucs = [roc_auc_score(labels, p) for p in probabilities]
            self.assertEqual(numbers['main.PFT.10.auc_out.mean'], f'{np.mean(aucs):.3f}')
            self.assertEqual(numbers['cost.LoRA.100.cap_hit'], '3/3')
            for name in ('main_results', 'cost', 'contrasts', 'ablations', 'run_level'):
                self.assertTrue((root / 'tables' / f'{name}.md').exists(), name)

    def test_incomplete_grid_refuses_tables(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            write_run(root, 'main_LP_010_s0', 'LP', .1, 0, {'internal': 1, 'external': 1})
            with self.assertRaises(ValueError):
                build(root, root / 'tables', root / 'paper/numbers.json')

    def test_changed_predictions_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for seed in SEEDS:
                write_run(root, f'main_LP_010_s{seed}', 'LP', .1, seed, {'internal': 1, 'external': 1})
            path = root / 'results/predictions/main_LP_010_s1/internal_predictions.csv'
            path.write_text(path.read_text().replace('0.', '0.9', 1))
            with self.assertRaises(ValueError):
                aligned(root, select(load_runs(root), 'LP', .1), 'internal')


class ErrorAnalysis(unittest.TestCase):
    def test_overlap_partitions_images_and_gallery_is_deterministic(self):
        from src.analysis import error_analysis as E
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fixture(root, lambda m, f: {'internal': 1., 'external': {'CNN': .3}.get(m, .8)})
            runs = load_runs(root)
            table = E.overlap(root, runs)
            for fraction in FRACTIONS:
                self.assertEqual(table[np.isclose(table.fraction, fraction)].n_images.sum(), 70)
            first, second = E.select_gallery(root, runs), E.select_gallery(root, runs)
            self.assertEqual(first, second)
            self.assertLessEqual(len(first), 10)
            types = [g['error_type'] for g in first]
            self.assertEqual(types, sorted(types, key=lambda t: t != 'false_negative'))
            _, labels, _, image_ids = E.run_errors(root, runs, 'LP', 1.)
            strata = pd.DataFrame({'image_id': image_ids, 'label': labels,
                                   **{v: np.where(np.arange(70) % 2, 'a', 'b') for v in E.STRATA}})
            rates = E.stratified_errors(root, runs, strata)
            cell = rates[(rates.method == 'LP') & (rates.fraction == 1.) & (rates.variable == 'BIRADS')]
            self.assertEqual(cell.n.sum(), 70)
            errors, *_ = E.run_errors(root, runs, 'LP', 1.)
            self.assertAlmostEqual((cell.error_rate_mean * cell.n).sum() / 70, errors.mean(), places=12)


if __name__ == '__main__':
    unittest.main()
