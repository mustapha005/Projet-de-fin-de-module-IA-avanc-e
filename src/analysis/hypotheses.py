"""Planned paired contrasts and the frozen H1–H3 clause rules (docs/PROTOCOL.md)."""
from itertools import combinations
from pathlib import Path

import numpy as np

from src.analysis.collect import COHORTS, FM_METHODS, FRACTIONS, METHODS, aligned, select
from src.stats import compound_verdict, paired_auc_difference, paired_gap_difference


def auc_contrast(root: Path, runs: list[dict], a: str, b: str, fraction: float, cohort: str,
                 variant_a: str = 'main', variant_b: str = 'main') -> dict:
    """AUC(a) − AUC(b) on one cohort, paired by seed and image."""
    labels, pa, ids_a = aligned(root, select(runs, a, fraction, variant_a), cohort)
    labels_b, pb, ids_b = aligned(root, select(runs, b, fraction, variant_b), cohort)
    if ids_a != ids_b or not np.array_equal(labels, labels_b):
        raise ValueError('Methods are not paired on identical test images')
    result = paired_auc_difference(labels, pa, pb)
    return {'kind': 'auc', 'a': a, 'b': b, 'variant_a': variant_a, 'variant_b': variant_b,
            'fraction': fraction, 'cohort': cohort, **result}


def gap_contrast(root: Path, runs: list[dict], a: str, b: str, fraction: float) -> dict:
    """Gap(a) − gap(b), gap = AUC_internal − AUC_external."""
    cells = {m: select(runs, m, fraction) for m in (a, b)}
    yi, ai, _ = aligned(root, cells[a], 'internal')
    _, bi, _ = aligned(root, cells[b], 'internal')
    yo, ao, _ = aligned(root, cells[a], 'external')
    _, bo, _ = aligned(root, cells[b], 'external')
    result = paired_gap_difference(yi, ai, bi, yo, ao, bo)
    return {'kind': 'gap', 'a': a, 'b': b, 'variant_a': 'main', 'variant_b': 'main',
            'fraction': fraction, 'cohort': 'internal_minus_external', **result}


def all_contrasts(root: Path, runs: list[dict]) -> list[dict]:
    """Every planned main-grid pair, both cohorts, plus every gap pair."""
    out = []
    for fraction in FRACTIONS:
        for a, b in combinations(METHODS, 2):
            for cohort in COHORTS:
                out.append(auc_contrast(root, runs, a, b, fraction, cohort))
            out.append(gap_contrast(root, runs, a, b, fraction))
    return out


def find(contrasts: list[dict], kind: str, a: str, b: str, fraction: float, cohort: str) -> dict:
    """Return the contrast oriented as a − b, flipping a stored b − a contrast."""
    for c in contrasts:
        if c['kind'] != kind or not np.isclose(c['fraction'], fraction) or c['cohort'] != cohort:
            continue
        if (c['a'], c['b']) == (a, b):
            return c
        if (c['a'], c['b']) == (b, a):
            return flip(c)
    raise KeyError((kind, a, b, fraction, cohort))


def flip(c: dict) -> dict:
    swap = {'a_better': 'b_better', 'b_better': 'a_better',
            'a_larger_gap': 'b_larger_gap', 'b_larger_gap': 'a_larger_gap',
            'no_detectable_difference': 'no_detectable_difference'}
    lower, upper = c['ci95']
    return {**c, 'a': c['b'], 'b': c['a'], 'mean': -c['mean'], 'ci95': [-upper, -lower],
            'per_seed': [-x for x in c['per_seed']],
            'per_seed_ci95': [[-u, -l] for l, u in c['per_seed_ci95']],
            'direction': swap[c['direction']]}


def _directional(c: dict, positive: str, negative: str) -> str:
    return {positive: 'supported', negative: 'rejected'}.get(c['direction'], 'inconclusive')


def h1(contrasts: list[dict]) -> dict:
    low = find(contrasts, 'auc', 'LP', 'LoRA', .01, 'internal')
    high = find(contrasts, 'auc', 'LoRA', 'LP', 1., 'internal')
    clauses = {'LP_not_worse_than_LoRA_at_1pct': _directional(low, 'a_better', 'b_better'),
               'LoRA_beats_LP_at_100pct': _directional(high, 'a_better', 'b_better')}
    return {'clauses': clauses, 'verdict': compound_verdict(list(clauses.values())),
            'evidence': [low, high]}


def h2(contrasts: list[dict], trainable: dict[str, float]) -> dict:
    ranking_pairs, opposite, matching = [], False, True
    for fraction in FRACTIONS:
        for a, b in combinations(FM_METHODS, 2):
            inside = find(contrasts, 'auc', a, b, fraction, 'internal')
            outside = find(contrasts, 'auc', a, b, fraction, 'external')
            detect_in = inside['direction'] != 'no_detectable_difference'
            detect_out = outside['direction'] != 'no_detectable_difference'
            if detect_in and detect_out and inside['direction'] != outside['direction']:
                opposite = True
            if not (detect_in and detect_out and inside['direction'] == outside['direction']):
                matching = False
            ranking_pairs.append({'fraction': fraction, 'a': a, 'b': b,
                                  'internal': inside['direction'], 'external': outside['direction']})
    ranking = 'rejected' if opposite else ('supported' if matching else 'inconclusive')
    order = sorted(FM_METHODS, key=lambda m: trainable[m])
    gap_pairs, grows, all_shrink = [], False, True
    for fraction in FRACTIONS:
        for low, high in combinations(order, 2):
            c = find(contrasts, 'gap', high, low, fraction, 'internal_minus_external')
            grows |= c['direction'] == 'a_larger_gap'
            all_shrink &= c['direction'] == 'b_larger_gap'
            gap_pairs.append({'fraction': fraction, 'higher_trainable': high, 'lower_trainable': low,
                              'mean_gap_difference': c['mean'], 'ci95': c['ci95'], 'direction': c['direction']})
    gap = 'rejected' if grows else ('supported' if all_shrink else 'inconclusive')
    clauses = {'ranking_preserved_externally': ranking, 'gap_does_not_grow_with_trainable_parameters': gap}
    return {'clauses': clauses, 'verdict': compound_verdict(list(clauses.values())),
            'trainable_order': order, 'ranking_pairs': ranking_pairs, 'gap_pairs': gap_pairs}


def h3(contrasts: list[dict], cohort: str = 'internal') -> dict:
    pairs = [find(contrasts, 'auc', m, 'CNN', f, cohort) for f in (.01, .1) for m in FM_METHODS]
    directions = [p['direction'] for p in pairs]
    verdict = ('rejected' if 'b_better' in directions else
               'supported' if all(d == 'a_better' for d in directions) else 'inconclusive')
    return {'cohort': cohort, 'verdict': verdict,
            'pairs': [{'method': p['a'], 'fraction': p['fraction'], 'mean_auc_difference': p['mean'],
                       'ci95': p['ci95'], 'larger_method_sd': p['larger_method_sd'],
                       'direction': p['direction']} for p in pairs]}


def verdicts(contrasts: list[dict], trainable: dict[str, float]) -> dict:
    return {'H1': h1(contrasts), 'H2': h2(contrasts, trainable), 'H3': h3(contrasts, 'internal'),
            'H3_external_secondary': h3(contrasts, 'external'),
            'rule': ('Detectable only if |mean difference| exceeds the larger per-seed SD and the 95% '
                     'class-stratified paired bootstrap CI excludes 0 in the same direction. '
                     'Compound: any rejected clause rejects; all supported supports; else inconclusive.')}
