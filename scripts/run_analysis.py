"""Regenerate every table, figure, verdict and article number from results/ (make analysis)."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis import error_analysis, figures, make_tables, protocol_numbers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-saliency', action='store_true', help='Skip checkpoint-based overlays')
    args = parser.parse_args()
    # The grid audit recomputes saved metrics and fails on hash/threshold/deadline problems.
    for phase in ('main', 'ablation'):
        subprocess.run([sys.executable, str(ROOT / 'scripts/audit_experiments.py'), '--phase', phase], cwd=ROOT, check=True)
    protocol_numbers.write(ROOT)
    verdicts = make_tables.build(ROOT, ROOT / 'tables', ROOT / 'paper/numbers.json')
    written = [p.name for p in figures.build(ROOT, ROOT / 'figures')]
    errors = error_analysis.build(ROOT, ROOT / 'tables', ROOT / 'figures', saliency=not args.no_saliency)
    print(json.dumps({'verdicts': {k: verdicts[k]['verdict'] for k in ('H1', 'H2', 'H3', 'H3_external_secondary')},
                      'figures': written + errors['figures'], 'gallery': errors['gallery']}, indent=2))


if __name__ == '__main__':
    main()
