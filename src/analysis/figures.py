"""Generated figures (PNG, 300 dpi) from verified results/ records only."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import NullFormatter, ScalarFormatter
import numpy as np

from src.analysis.collect import COHORTS, FRACTIONS, METHODS, aligned, load_runs, run_frame, select
from src.runtime import ROOT

# Three validated categorical slots for the FM methods; the scratch baseline is a
# neutral gray with a dashed line. Markers make identity independent of colour.
STYLE = {'LP': dict(color='#2a78d6', marker='o', linestyle='-'),
         'PFT': dict(color='#eb6834', marker='s', linestyle='-'),
         'LoRA': dict(color='#1baf7a', marker='^', linestyle='-'),
         'CNN': dict(color='#6b6a66', marker='D', linestyle='--')}
COHORT_TITLE = {'internal': 'Internal test (BUSI)', 'external': 'External test (BrEaST)'}
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e4e3df'


def setup():
    plt.rcParams.update({'font.size': 7, 'axes.titlesize': 7.5, 'axes.labelsize': 7,
                         'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5, 'legend.fontsize': 6.5,
                         'axes.edgecolor': MUTED, 'axes.labelcolor': INK, 'xtick.color': MUTED,
                         'ytick.color': MUTED, 'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': .6,
                         'lines.linewidth': 1.4, 'lines.markersize': 4.5, 'savefig.dpi': 300,
                         'font.family': 'DejaVu Sans'})


def save(fig, folder: Path, name: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'{name}.png'
    fig.savefig(path, bbox_inches='tight', facecolor='white', metadata={'Software': None})
    plt.close(fig)
    return path


def learning_curve(frame, folder):
    main = frame[frame.variant == 'main']
    sizes = {f: int(main[np.isclose(main.fraction, f)].n_train.iloc[0]) for f in FRACTIONS}
    fig, axes = plt.subplots(1, 2, figsize=(3.45, 2.25), sharey=True)
    dodge = {'LP': -.045, 'PFT': -.015, 'LoRA': .015, 'CNN': .045}
    for ax, cohort in zip(axes, COHORTS):
        for method in METHODS:
            cell = main[main.method == method].groupby('fraction')[f'roc_auc_{cohort}']
            x = np.array([sizes[f] for f in FRACTIONS]) * 10 ** dodge[method]
            ax.errorbar(x, cell.mean().loc[FRACTIONS], yerr=cell.std(ddof=1).loc[FRACTIONS],
                        label=method, capsize=2, elinewidth=.8, markeredgecolor='white',
                        markeredgewidth=.6, **STYLE[method])
        ax.set_xscale('log')
        ax.set_xticks([sizes[f] for f in FRACTIONS])
        ax.set_xticklabels([f'{sizes[f]}\n({int(100 * f)}%)' for f in FRACTIONS])
        ax.minorticks_off()
        ax.set_title(COHORT_TITLE[cohort])
    fig.supxlabel('Training images (nominal fraction)', fontsize=7, y=.02)
    axes[0].set_ylabel('ROC-AUC (mean ± SD, 3 seeds)')
    axes[0].axhline(.5, color=MUTED, linewidth=.7, linestyle=':')
    axes[1].axhline(.5, color=MUTED, linewidth=.7, linestyle=':')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=4, frameon=False, bbox_to_anchor=(.5, 1.07))
    fig.tight_layout()
    return save(fig, folder, 'fig_learning_curve')


def cost_performance(frame, folder):
    main = frame[frame.variant == 'main']
    fig, ax = plt.subplots(figsize=(3.45, 2.35))
    for method in METHODS:
        cell = main[main.method == method].groupby('fraction')
        x, y = cell.charged_seconds.mean().loc[FRACTIONS], cell.roc_auc_internal.mean().loc[FRACTIONS]
        ax.errorbar(x, y, xerr=cell.charged_seconds.std(ddof=1).loc[FRACTIONS],
                    yerr=cell.roc_auc_internal.std(ddof=1).loc[FRACTIONS], label=method, capsize=2,
                    elinewidth=.8, markeredgecolor='white', markeredgewidth=.6, **STYLE[method])
        ax.annotate(f'{int(100 * FRACTIONS[-1])}%', (x.iloc[-1], y.iloc[-1]), textcoords='offset points',
                    xytext=(4, -2), fontsize=6, color=MUTED)
    ax.set_xscale('log')
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel('Charged training wall-clock per run (s, log scale)')
    ax.set_ylabel('Internal ROC-AUC (mean ± SD)')
    ax.legend(frameon=False, ncol=4, loc='lower center', bbox_to_anchor=(.5, 1.0))
    fig.tight_layout()
    return save(fig, folder, 'fig_cost_performance')


def reliability(root, runs, folder, fraction=1.):
    bins = np.linspace(0, 1, 11)
    fig, axes = plt.subplots(2, 4, figsize=(7.0, 3.6), sharex=True, sharey=True)
    for row, cohort in enumerate(COHORTS):
        for col, method in enumerate(METHODS):
            ax = axes[row, col]
            labels, probabilities, _ = aligned(root, select(runs, method, fraction), cohort)
            ax.plot([0, 1], [0, 1], color=MUTED, linewidth=.7, linestyle=':')
            for seed, p in enumerate(probabilities):
                index = np.clip(np.digitize(p, bins) - 1, 0, 9)
                filled = [b for b in range(10) if np.any(index == b)]
                ax.plot([p[index == b].mean() for b in filled], [labels[index == b].mean() for b in filled],
                        color=STYLE[method]['color'], marker=STYLE[method]['marker'], markersize=3,
                        linewidth=1, alpha=[1, .75, .5][seed], label=f'seed {seed}')
            if row == 0:
                ax.set_title(method)
            if col == 0:
                ax.set_ylabel(f'{COHORT_TITLE[cohort].split(" (")[0]}\nobserved malignant freq.')
            if row == 1:
                ax.set_xlabel('Predicted malignant probability')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_xticks([0, .5, 1])
            ax.set_yticks([0, .5, 1])
    axes[0, 0].legend(frameon=False, loc='upper left')
    fig.suptitle(f'Reliability at nominal {int(100 * fraction)}% labels (10 equal-width bins, one line per seed)', y=1.0)
    fig.tight_layout()
    return save(fig, folder, 'fig_reliability')


def ablations(frame, folder):
    rows = [('main', 'LoRA', 'LoRA, all 12 blocks, r=8 (main)'), ('lora_last2', 'LoRA', 'LoRA, last 2 blocks'),
            ('lora_rank4', 'LoRA', 'LoRA, r=4'), ('lora_rank16', 'LoRA', 'LoRA, r=16'),
            ('lora_no_augmentation', 'LoRA', 'LoRA, no augmentation'),
            ('main', 'PFT', 'PFT, last 2 blocks (main)'), ('pft_depth4', 'PFT', 'PFT, last 4 blocks')]
    present = [r for r in rows if len(frame[(frame.variant == r[0]) & (frame.method == r[1]) & np.isclose(frame.fraction, .1)]) == 3]
    if not present:
        return None
    fig, ax = plt.subplots(figsize=(3.45, .32 * len(present) + .8))
    for i, (variant, method, label) in enumerate(present):
        cell = frame[(frame.variant == variant) & (frame.method == method) & np.isclose(frame.fraction, .1)]
        for cohort, offset, fill in (('internal', -.12, STYLE[method]['color']), ('external', .12, 'white')):
            values = cell[f'roc_auc_{cohort}']
            ax.errorbar(values.mean(), i + offset, xerr=values.std(ddof=1), fmt=STYLE[method]['marker'],
                        color=STYLE[method]['color'], markerfacecolor=fill, capsize=2, elinewidth=.8)
    ax.set_yticks(range(len(present)))
    ax.set_yticklabels([r[2] for r in present])
    ax.invert_yaxis()
    ax.set_xlabel('ROC-AUC, 10% labels (mean ± SD)')
    ax.grid(axis='y', visible=False)
    key = [Line2D([], [], color=MUTED, marker='o', linestyle='', markerfacecolor=MUTED, label='Internal (filled)'),
           Line2D([], [], color=MUTED, marker='o', linestyle='', markerfacecolor='white', label='External (open)')]
    ax.legend(handles=key, frameon=False, ncol=2, loc='lower center', bbox_to_anchor=(.35, 1.0))
    fig.tight_layout()
    return save(fig, folder, 'fig_ablations')


def build(root: Path, folder: Path) -> list[Path]:
    setup()
    runs = load_runs(root, 'main')
    ablation_runs = load_runs(root, 'ablation') if (root / 'results/ablation').exists() else []
    frame = run_frame(runs + ablation_runs)
    paths = [learning_curve(frame, folder), cost_performance(frame, folder), reliability(root, runs, folder),
             ablations(frame, folder)]
    return [p for p in paths if p is not None]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    for path in build(args.root, args.root / 'figures'):
        print('Wrote', path.relative_to(args.root))


if __name__ == '__main__':
    main()
