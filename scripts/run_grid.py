"""Unattended main grid then ablations, resumable, with a power-state log.

Each phase is the ordinary resumable controller (`run_experiments.py`): completed
cells are verified and skipped, interrupted fits restart under the same cap as new
logged attempts, and a test evaluation that was started but not committed fails
closed. A phase that exits with an error is retried a bounded number of times;
nothing is retuned and no frozen setting changes.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import threading
import time

import psutil

ROOT = Path(__file__).resolve().parents[1]


def log(stream, message):
    stream.write(f'{datetime.now(timezone.utc).isoformat()} {message}\n')
    stream.flush()


def power_sampler(path: Path, stop: threading.Event, every: float = 60.):
    """AC/battery state and CPU frequency; timing evidence, never a selection input."""
    new = not path.exists()
    with path.open('a', encoding='utf-8', newline='\n') as stream:
        if new:
            stream.write('utc,power_plugged,battery_percent,cpu_mhz,cpu_percent\n')
        while not stop.is_set():
            battery = psutil.sensors_battery()
            frequency = psutil.cpu_freq()
            stream.write(f'{datetime.now(timezone.utc).isoformat()},'
                         f'{battery.power_plugged if battery else ""},{battery.percent if battery else ""},'
                         f'{frequency.current if frequency else ""},{psutil.cpu_percent(interval=None)}\n')
            stream.flush()
            stop.wait(every)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phases', nargs='+', default=['main', 'ablation'], choices=['main', 'ablation'])
    parser.add_argument('--retries', type=int, default=2)
    args = parser.parse_args()
    folder = ROOT / 'logs'
    folder.mkdir(exist_ok=True)
    stop = threading.Event()
    sampler = threading.Thread(target=power_sampler, args=(folder / 'power_log.csv', stop), daemon=True)
    sampler.start()
    with (folder / 'grid_controller.log').open('a', encoding='utf-8', newline='\n') as stream:
        log(stream, f'START phases={args.phases} pid={psutil.Process().pid}')
        try:
            for phase in args.phases:
                for attempt in range(1, args.retries + 2):
                    log(stream, f'PHASE {phase} invocation {attempt}')
                    with (folder / f'{phase}_controller.log').open('a', encoding='utf-8', newline='\n') as output:
                        code = subprocess.run([sys.executable, str(ROOT / 'scripts/run_experiments.py'), '--phase', phase],
                                              cwd=ROOT, stdout=output, stderr=subprocess.STDOUT).returncode
                    log(stream, f'PHASE {phase} invocation {attempt} exit={code}')
                    if code == 0:
                        break
                    time.sleep(30)
                else:
                    log(stream, f'STOP {phase} failed after {args.retries + 1} invocations; inspect {phase}_controller.log')
                    return 1
            log(stream, 'DONE all phases completed')
            return 0
        finally:
            stop.set()


if __name__ == '__main__':
    sys.exit(main())
