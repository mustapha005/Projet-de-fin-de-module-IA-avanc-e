"""Binary metrics and paired, class-stratified uncertainty for fixed trained seeds."""
import numpy as np
from scipy.stats import rankdata
from sklearn.metrics import f1_score, roc_auc_score


def validate_predictions(labels, probabilities):
    labels = np.asarray(labels)
    probabilities = np.asarray(probabilities, dtype=float)
    if labels.ndim != 1 or set(np.unique(labels)) != {0, 1}:
        raise ValueError('Both binary classes are required')
    if probabilities.shape[-1] != len(labels) or probabilities.ndim not in {1, 2}:
        raise ValueError('Prediction shape must be (images,) or (seeds, images)')
    if not np.isfinite(probabilities).all() or np.any((probabilities < 0) | (probabilities > 1)):
        raise ValueError('Probabilities must be finite and in [0,1]')
    return labels.astype(int), probabilities


def choose_threshold(labels, probabilities) -> float:
    """Choose validation macro-F1 with deterministic closeness/smaller tie rules."""
    labels, probabilities = validate_predictions(labels, probabilities)
    if probabilities.ndim != 1:
        raise ValueError('Select each run threshold separately')
    candidates = np.unique(np.r_[0., probabilities, np.nextafter(1., np.inf)])
    scores = np.array([f1_score(labels, probabilities >= t, average='macro', zero_division=0)
                       for t in candidates])
    tied = candidates[np.isclose(scores, scores.max(), rtol=0, atol=1e-12)]
    return float(min(tied, key=lambda t: (abs(t - .5), t)))


def top_label_ece(labels, probabilities, bins=15) -> float:
    labels, probabilities = validate_predictions(labels, probabilities)
    if probabilities.ndim != 1:
        raise ValueError('ECE expects one prediction per image')
    confidence = np.maximum(probabilities, 1 - probabilities)
    correct = ((probabilities >= .5).astype(int) == labels).astype(float)
    membership = np.minimum((confidence * bins).astype(int), bins - 1)
    return float(sum(abs(np.sum(correct[membership == b] - confidence[membership == b]))
                     for b in range(bins)) / len(labels))


def metrics(labels, probabilities, threshold=.5) -> dict:
    labels, probabilities = validate_predictions(labels, probabilities)
    if probabilities.ndim != 1 or not np.isfinite(threshold):
        raise ValueError('One probability vector and a finite threshold are required')
    return {'roc_auc': float(roc_auc_score(labels, probabilities)),
            'macro_f1': float(f1_score(labels, probabilities >= threshold,
                                       average='macro', zero_division=0)),
            'ece15': top_label_ece(labels, probabilities)}


def stratified_indices(labels, n_resamples=2000, seed=20261120):
    labels = np.asarray(labels)
    if set(np.unique(labels)) != {0, 1} or n_resamples < 2:
        raise ValueError('Binary labels and at least two resamples are required')
    rng = np.random.default_rng(seed)
    return np.concatenate([rng.choice(np.flatnonzero(labels == c),
                                     size=(n_resamples, np.sum(labels == c)), replace=True)
                           for c in (0, 1)], axis=1)


def _auc_batch(labels, probabilities):
    """Mann–Whitney rank AUC, with average ranks for tied probabilities."""
    positives = labels.sum(axis=1)
    negatives = labels.shape[1] - positives
    ranks = rankdata(probabilities, method='average', axis=1)
    return ((ranks * labels).sum(axis=1) - positives * (positives + 1) / 2) / (positives * negatives)


def bootstrap_auc(labels, probabilities, indices):
    labels, probabilities = validate_predictions(labels, probabilities)
    if probabilities.ndim == 1:
        probabilities = probabilities[None, :]
    return np.array([_auc_batch(labels[indices], predictions[indices]) for predictions in probabilities])


def _summary(values, draws):
    means = draws.mean(axis=0)
    return {'per_seed': np.asarray(values).tolist(), 'mean': float(np.mean(values)),
            'sample_sd': float(np.std(values, ddof=1)),
            'ci95': np.quantile(means, [.025, .975]).tolist(),
            'per_seed_ci95': np.quantile(draws, [.025, .975], axis=1).T.tolist()}


def auc_summary(labels, probabilities, n_resamples=2000, seed=20261120):
    labels, probabilities = validate_predictions(labels, probabilities)
    if probabilities.ndim != 2 or len(probabilities) != 3:
        raise ValueError('Exactly three trained seeds are required')
    indices = stratified_indices(labels, n_resamples, seed)
    draws = bootstrap_auc(labels, probabilities, indices)
    values = [roc_auc_score(labels, p) for p in probabilities]
    return _summary(values, draws)


def _contrast(values_a, values_b, draws_a, draws_b):
    difference = np.asarray(values_a) - np.asarray(values_b)
    result = _summary(difference, draws_a - draws_b)
    result['larger_method_sd'] = float(max(np.std(values_a, ddof=1), np.std(values_b, ddof=1)))
    lower, upper = result['ci95']
    delta = result['mean']
    detectable = abs(delta) > result['larger_method_sd'] and ((delta > 0 and lower > 0) or (delta < 0 and upper < 0))
    result['direction'] = ('a_better' if delta > 0 else 'b_better') if detectable else 'no_detectable_difference'
    result['interpretation'] = 'Conditional on these trained seeds and image-level independence; no multiplicity adjustment.'
    return result


def paired_auc_difference(labels, probabilities_a, probabilities_b, n_resamples=2000, seed=20261120):
    labels, a = validate_predictions(labels, probabilities_a)
    _, b = validate_predictions(labels, probabilities_b)
    if a.shape != b.shape or a.ndim != 2 or len(a) != 3:
        raise ValueError('Methods must align exactly on three seeds and image IDs')
    indices = stratified_indices(labels, n_resamples, seed)
    return _contrast([roc_auc_score(labels, p) for p in a], [roc_auc_score(labels, p) for p in b],
                     bootstrap_auc(labels, a, indices), bootstrap_auc(labels, b, indices))


def paired_gap_difference(labels_in, a_in, b_in, labels_out, a_out, b_out,
                          n_resamples=2000, seed=20261120):
    """Compare AUC gaps with independent cohorts, paired methods/seeds within each."""
    yi, ai = validate_predictions(labels_in, a_in)
    _, bi = validate_predictions(yi, b_in)
    yo, ao = validate_predictions(labels_out, a_out)
    _, bo = validate_predictions(yo, b_out)
    if ai.shape != bi.shape or ao.shape != bo.shape or any(x.ndim != 2 or len(x) != 3 for x in (ai, bi, ao, bo)):
        raise ValueError('Exactly three aligned seeds per cohort are required')
    seeds = np.random.SeedSequence(seed).spawn(2)
    ii = stratified_indices(yi, n_resamples, seeds[0])
    io = stratified_indices(yo, n_resamples, seeds[1])
    gap_a = [roc_auc_score(yi, pi) - roc_auc_score(yo, po) for pi, po in zip(ai, ao)]
    gap_b = [roc_auc_score(yi, pi) - roc_auc_score(yo, po) for pi, po in zip(bi, bo)]
    result = _contrast(gap_a, gap_b, bootstrap_auc(yi, ai, ii) - bootstrap_auc(yo, ao, io),
                       bootstrap_auc(yi, bi, ii) - bootstrap_auc(yo, bo, io))
    result['direction'] = {'a_better': 'a_larger_gap', 'b_better': 'b_larger_gap',
                            'no_detectable_difference': 'no_detectable_difference'}[result['direction']]
    return result


def compound_verdict(clauses):
    if not clauses or any(v not in {'supported', 'rejected', 'inconclusive'} for v in clauses):
        raise ValueError('Valid nonempty clause verdicts required')
    return 'rejected' if 'rejected' in clauses else ('supported' if all(v == 'supported' for v in clauses) else 'inconclusive')
