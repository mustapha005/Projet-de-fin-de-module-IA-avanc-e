"""External error typology, error overlap, failure gallery and saliency (protocol + D013).

Runs only after the complete main grid exists. It reads final predictions, the
external clinical workbook and the external images; it never selects models,
thresholds or hyperparameters, and nothing here feeds back into training.
"""
import argparse
from itertools import combinations
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
import torch

from src.analysis.collect import FRACTIONS, METHODS, SEEDS, aligned, load_runs, select
from src.analysis.figures import MUTED, STYLE, save, setup
from src.runtime import ROOT, write_json

STRATA = ['BIRADS', 'Verification', 'Diagnosis', 'pixel_count_tertile', 'luminance_tertile', 'contrast_tertile']
GALLERY_FRACTION = 1.


def external_strata(root: Path) -> pd.DataFrame:
    """Recorded clinical fields plus outcome-independent image statistics."""
    manifest = pd.read_csv(root / 'data/manifests/breast_external.csv', dtype={'phash': str})
    books = list((root / 'data/raw/breast').glob('*.xlsx'))
    if len(books) != 1:
        raise FileNotFoundError('Expected exactly one BrEaST clinical workbook')
    sheets = pd.read_excel(books[0], sheet_name=None)
    clinical = next(f for f in sheets.values() if {'Image_filename', 'Classification'} <= set(f.columns))
    clinical = clinical.assign(image_id='breast/' + clinical.Image_filename.str.strip().str.replace('.png', '', regex=False))
    frame = manifest.merge(clinical[['image_id', 'BIRADS', 'Verification', 'Diagnosis']], on='image_id', how='left',
                           validate='one_to_one')
    if frame[['BIRADS', 'Verification', 'Diagnosis']].isna().all(axis=1).any():
        raise ValueError('External image without clinical record')
    stats = []
    for path in frame.path:
        with Image.open(root / path) as image:
            pixels = np.asarray(image.convert('L'), dtype=float)
        stats.append((pixels.size, pixels.mean(), pixels.std()))
    frame[['pixel_count', 'luminance', 'contrast']] = pd.DataFrame(stats, index=frame.index)
    for column in ('pixel_count', 'luminance', 'contrast'):
        frame[f'{column}_tertile'] = pd.qcut(frame[column], 3, labels=['low', 'mid', 'high']).astype(str)
    for column in ('BIRADS', 'Verification', 'Diagnosis'):
        frame[column] = frame[column].astype(str).str.strip()
    return frame[['image_id', 'label', 'width', 'height', 'pixel_count', 'luminance', 'contrast', *STRATA]]


def run_errors(root: Path, runs: list[dict], method: str, fraction: float, cohort='external'):
    """(seeds, images) boolean error matrix at each run's frozen validation threshold."""
    cell = select(runs, method, fraction)
    labels, probabilities, ids = aligned(root, cell, cohort)
    thresholds = np.array([r['evaluation']['threshold'] for r in cell])[:, None]
    predicted = probabilities >= thresholds
    return predicted != labels.astype(bool), labels, probabilities, ids


def stratified_errors(root, runs, strata: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for method in METHODS:
        for fraction in FRACTIONS:
            errors, labels, _, ids = run_errors(root, runs, method, fraction)
            info = strata.set_index('image_id').loc[ids]
            for variable in STRATA:
                for category, index in info.reset_index().groupby(variable).groups.items():
                    index = np.asarray(index)
                    rates = errors[:, index].mean(axis=1)
                    rows.append({'method': method, 'fraction': fraction, 'variable': variable,
                                 'category': category, 'n': len(index),
                                 'n_malignant': int(labels[index].sum()),
                                 'error_rate_mean': rates.mean(), 'error_rate_sd': rates.std(ddof=1)})
    return pd.DataFrame(rows)


def display_strata(table: pd.DataFrame, fraction=GALLERY_FRACTION) -> pd.DataFrame:
    """Article view: one fraction; clinical categories with n < 5 pooled as 'other'."""
    view = table[np.isclose(table.fraction, fraction)].copy()
    clinical = view.variable.isin(['BIRADS', 'Verification', 'Diagnosis'])
    small = clinical & (view.n < 5)
    view.loc[small, 'category'] = 'other (n<5 each)'
    view['weighted'] = view.error_rate_mean * view.n
    pooled = view.groupby(['variable', 'category', 'method'], sort=False).agg(n=('n', 'sum'), weighted=('weighted', 'sum')).reset_index()
    pooled['error_rate'] = pooled.weighted / pooled.n
    wide = pooled.pivot_table(index=['variable', 'category', 'n'], columns='method', values='error_rate', sort=False)
    wide = wide[METHODS].reset_index()
    for method in METHODS:
        wide[method] = wide[method].map(lambda x: f'{x:.2f}')
    return wide


def majority_errors(root, runs, fraction):
    out = {}
    for method in METHODS:
        errors, labels, probabilities, ids = run_errors(root, runs, method, fraction)
        out[method] = {'ids': ids, 'labels': labels, 'probabilities': probabilities,
                       'majority': errors.sum(axis=0) >= 2}
    return out


def overlap(root, runs) -> pd.DataFrame:
    rows = []
    for fraction in FRACTIONS:
        errors = majority_errors(root, runs, fraction)
        matrix = np.vstack([errors[m]['majority'] for m in METHODS])
        for size in range(1, len(METHODS) + 1):
            for combo in combinations(range(len(METHODS)), size):
                exact = matrix[list(combo)].all(axis=0) & ~np.delete(matrix, combo, axis=0).any(axis=0)
                rows.append({'fraction': fraction, 'methods_wrong': '+'.join(METHODS[i] for i in combo),
                             'n_images': int(exact.sum())})
        rows.append({'fraction': fraction, 'methods_wrong': 'none', 'n_images': int((~matrix.any(axis=0)).sum())})
    return pd.DataFrame(rows)


def select_gallery(root, runs, n_each=5) -> list[dict]:
    """D013: FN/FP balance; rank by #methods wrong, wrong-direction probability, then ID."""
    errors = majority_errors(root, runs, GALLERY_FRACTION)
    ids, labels = errors['LP']['ids'], errors['LP']['labels']
    wrong = np.vstack([errors[m]['majority'] for m in METHODS])
    probability = np.stack([errors[m]['probabilities'] for m in METHODS])   # (methods, seeds, images)
    wrong_direction = np.where(labels == 1, 1 - probability, probability).mean(axis=(0, 1))
    candidates = []
    for i, image_id in enumerate(ids):
        if wrong[:, i].any():
            candidates.append({'image_id': image_id, 'label': int(labels[i]),
                               'error_type': 'false_negative' if labels[i] == 1 else 'false_positive',
                               'methods_wrong': [m for m, w in zip(METHODS, wrong[:, i]) if w],
                               'mean_wrong_direction_probability': float(wrong_direction[i])})
    candidates.sort(key=lambda c: (-len(c['methods_wrong']), -c['mean_wrong_direction_probability'], c['image_id']))
    chosen = {t: [c for c in candidates if c['error_type'] == t][:n_each] for t in ('false_negative', 'false_positive')}
    shortfall = 2 * n_each - sum(len(v) for v in chosen.values())
    taken = {c['image_id'] for v in chosen.values() for c in v}
    extra = [c for c in candidates if c['image_id'] not in taken][:shortfall]
    return chosen['false_negative'] + chosen['false_positive'] + extra


def rollout(model, pixels: torch.Tensor) -> np.ndarray:
    """CLS attention rollout (Abnar & Zuidema): head-mean, +I, row-normalised, multiplied."""
    backbone = model.backbone
    with torch.no_grad():
        attentions = backbone(pixel_values=pixels, output_attentions=True).attentions
    result = torch.eye(attentions[0].shape[-1])
    for attention in attentions:
        a = attention[0].mean(dim=0) + torch.eye(attention.shape[-1])
        result = (a / a.sum(dim=-1, keepdim=True)) @ result
    patches = result[0, 1:]
    side = int(patches.numel() ** .5)
    return patches.reshape(side, side).numpy()


def grad_cam(model, pixels: torch.Tensor) -> np.ndarray:
    """Grad-CAM on ResNet-18 layer4 for the predicted class."""
    store = {}

    def keep(module, inputs, output):
        store['a'] = output
        output.register_hook(lambda grad: store.__setitem__('g', grad))

    forward = model.layer4.register_forward_hook(keep)
    try:
        model.zero_grad(set_to_none=True)
        logits = model(pixels.requires_grad_(True))
        logits[0, logits[0].argmax()].backward()
    finally:
        forward.remove()
    weights = store['g'][0].mean(dim=(1, 2))
    cam = torch.relu((weights[:, None, None] * store['a'][0]).sum(dim=0)).detach().numpy()
    return cam / cam.max() if cam.max() > 0 else cam


def saliency_figure(root, runs, gallery, folder) -> Path:
    from src.datasets import Images, MEAN, STD
    from src.evaluate import load_selected_model
    manifest = pd.read_csv(root / 'data/manifests/breast_external.csv', dtype={'phash': str}).set_index('image_id')
    rows = manifest.loc[[g['image_id'] for g in gallery]].reset_index()
    images = Images(rows)
    models = {}
    for method in METHODS:
        run = select(runs, method, GALLERY_FRACTION)[0]          # seed 0 (D013)
        best = run['fit']['best']
        models[method] = load_selected_model(run['config'], best, root / run['attempt_path'])[0]
    fig, axes = plt.subplots(len(gallery), 1 + len(METHODS), figsize=(7.0, 1.45 * len(gallery)))
    for r, entry in enumerate(gallery):
        pixels = images[r][0][None]
        shown = (pixels[0, 0] * STD[0] + MEAN[0]).clamp(0, 1).numpy()
        axes[r, 0].imshow(shown, cmap='gray')
        axes[r, 0].set_ylabel(f"{entry['image_id'].split('/')[-1]}\n{entry['error_type'].replace('_', ' ')}", fontsize=6)
        for c, method in enumerate(METHODS, start=1):
            heat = grad_cam(models[method], pixels.clone()) if method == 'CNN' else rollout(models[method], pixels)
            heat = np.asarray(Image.fromarray((255 * heat / max(heat.max(), 1e-12)).astype(np.uint8)).resize((224, 224), Image.BILINEAR)) / 255
            axes[r, c].imshow(shown, cmap='gray')
            axes[r, c].imshow(heat, cmap='inferno', alpha=.45)
            wrong = method in entry['methods_wrong']
            if r == 0:
                axes[r, c].set_title(method + (' (rollout)' if method != 'CNN' else ' (Grad-CAM)'), fontsize=6.5)
            axes[r, c].set_xlabel('wrong' if wrong else 'right', fontsize=5.5, color=MUTED)
        for ax in axes[r]:
            ax.set_xticks([])
            ax.set_yticks([])
            ax.grid(False)
    axes[0, 0].set_title('Input (centre crop)', fontsize=6.5)
    fig.tight_layout()
    return save(fig, folder, 'fig_failure_gallery')


def overlap_figure(table: pd.DataFrame, folder: Path) -> Path:
    view = table[np.isclose(table.fraction, GALLERY_FRACTION) & (table.methods_wrong != 'none') & (table.n_images > 0)]
    view = view.sort_values('n_images')
    fig, ax = plt.subplots(figsize=(3.45, .2 * len(view) + .7))
    ax.barh(view.methods_wrong, view.n_images, color=MUTED, height=.6)
    for y, value in enumerate(view.n_images):
        ax.text(value + .3, y, str(value), va='center', fontsize=6)
    ax.set_xlabel('External images with majority error')
    ax.grid(axis='y', visible=False)
    fig.tight_layout()
    return save(fig, folder, 'fig_error_overlap')


def build(root: Path, tables: Path, figures: Path, saliency=True) -> dict:
    setup()
    runs = load_runs(root, 'main')
    if len(runs) != 36:
        raise ValueError(f'Error analysis requires the complete main grid (found {len(runs)}/36)')
    strata = external_strata(root)
    stratified = stratified_errors(root, runs, strata)
    tables.mkdir(parents=True, exist_ok=True)
    stratified.to_csv(tables / 'error_strata_all.csv', index=False, lineterminator='\n')
    from src.analysis.make_tables import save as save_table
    save_table(display_strata(stratified), tables, 'error_strata_100')
    overlaps = overlap(root, runs)
    save_table(overlaps, tables, 'error_overlap')
    gallery = select_gallery(root, runs)
    write_json(tables / 'failure_gallery.json', {'selection_rule': 'D013 (5 FN + 5 FP at nominal 100%)',
                                                 'images': gallery})
    paths = [overlap_figure(overlaps, figures)]
    if saliency and gallery:
        paths.append(saliency_figure(root, runs, gallery, figures))
    strata.drop(columns=['label']).to_csv(tables / 'external_image_properties.csv', index=False, lineterminator='\n')
    return {'gallery': [g['image_id'] for g in gallery], 'figures': [p.name for p in paths]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--no-saliency', action='store_true')
    args = parser.parse_args()
    print(json.dumps(build(args.root, args.root / 'tables', args.root / 'figures', not args.no_saliency), indent=2))


if __name__ == '__main__':
    main()
