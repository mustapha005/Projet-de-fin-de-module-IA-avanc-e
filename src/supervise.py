"""Bound a training worker's charged time and preserve only valid checkpoints."""
import json
from pathlib import Path
import subprocess
import sys
import time

import psutil

from src.runtime import ROOT, config_hash, git_commit, sha256, write_json


def process_tree(root):
    """Windows venv python.exe is a launcher; include the actual interpreter."""
    try:
        return [root] + root.children(recursive=True)
    except psutil.NoSuchProcess:
        return []


def terminate_tree(root):
    processes = process_tree(root)
    for process in reversed(processes):
        try:
            process.terminate()
        except psutil.NoSuchProcess:
            pass
    _, alive = psutil.wait_procs(processes, timeout=5)
    for process in alive:
        try:
            process.kill()
        except psutil.NoSuchProcess:
            pass
    _, alive = psutil.wait_procs(alive, timeout=5)
    if alive:
        raise RuntimeError('Could not stop every process in the training worker tree')


def run_training(config: dict, folder: Path) -> dict:
    """Create one immutable attempt; callers explicitly choose a fresh directory."""
    from src.protocol import validate_run_config
    validate_run_config(config)
    if folder.exists() and any(folder.iterdir()):
        raise FileExistsError('Attempt already exists; validate or start a new logged attempt')
    folder.mkdir(parents=True, exist_ok=True)
    write_json(folder / 'config.json', config)
    started = time.perf_counter()
    peak_rss, cpu_seconds, killed, overshoot = 0, 0., False, 0.
    cpu_by_pid, monitored_pids = {}, set()
    with (folder / 'worker.log').open('w', encoding='utf-8') as log:
        child = subprocess.Popen([sys.executable, '-m', 'src.train', '--config', str(folder / 'config.json')],
                                 cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        process = psutil.Process(child.pid)
        try:
            while child.poll() is None:
                rss = 0
                for member in process_tree(process):
                    try:
                        memory = member.memory_info()
                        rss += memory.rss
                        peak_rss = max(peak_rss, getattr(memory, 'peak_wset', memory.rss))
                        cpu_by_pid[member.pid] = max(cpu_by_pid.get(member.pid, 0.), sum(member.cpu_times()[:2]))
                        monitored_pids.add(member.pid)
                    except psutil.NoSuchProcess:
                        continue
                peak_rss = max(peak_rss, rss)
                cpu_seconds = sum(cpu_by_pid.values())
                budget_file = folder / 'budget.json'
                if budget_file.exists():
                    budget = json.loads(budget_file.read_text())
                    charged = time.perf_counter() - budget['started_monotonic'] + budget['credit_seconds']
                    if charged >= budget['seconds']:
                        killed = True
                        overshoot = charged - budget['seconds']
                        terminate_tree(process)
                        break
                elif time.perf_counter() - started > 120:
                    terminate_tree(process)
                    raise RuntimeError('Worker did not initialize within 120 seconds')
                time.sleep(.1)
            child.wait(timeout=10)
        finally:
            if child.poll() is None:
                terminate_tree(process)
                child.wait()
    best_path = folder / 'best.json'
    best = json.loads(best_path.read_text()) if best_path.exists() else None
    if best is not None:
        checkpoint = folder / best['checkpoint']
        if checkpoint.parent.resolve() != folder.resolve() or sha256(checkpoint) != best['checkpoint_sha256']:
            raise RuntimeError('Invalid selected checkpoint transaction')
        if best['charged_seconds_at_selection'] >= config['cap_seconds']:
            raise RuntimeError('Selected checkpoint exceeds the frozen budget')
    fit_path = folder / 'fit.json'
    fit = json.loads(fit_path.read_text()) if fit_path.exists() else {}
    if killed or not fit:
        metadata_path = folder / 'run_metadata.json'
        metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
        budget_path = folder / 'budget.json'
        timing = json.loads(budget_path.read_text()) if budget_path.exists() else {}
        history_path = folder / 'history.json'
        history = json.loads(history_path.read_text())['epochs'] if history_path.exists() else []
        fit = {**metadata, **fit, 'stop_reason': 'time_cap' if killed else 'worker_failure',
               'epochs_completed': max(len(history), (best or {}).get('epoch') or 0) if config['method'] != 'LP' else None,
               'charged_wall_seconds': config['cap_seconds'] + overshoot if killed else None,
               'cache_credit_seconds': timing.get('credit_seconds', 0.),
               'actual_fit_wall_seconds': max(0., config['cap_seconds'] + overshoot - timing.get('credit_seconds', 0.)) if killed else None,
               'best': best, 'status': 'PASS' if best is not None and killed else 'FAIL'}
    allowed_exit = child.returncode == 0 or killed
    valid = best is not None and allowed_exit
    record = {'status': 'PASS' if valid else 'FAIL', 'config': config,
              'config_hash': config_hash(config), 'git_commit': git_commit(),
              'worker_exit_code': child.returncode, 'supervisor_killed_at_cap': killed,
              'deadline_detection_overshoot_seconds': overshoot,
              'total_worker_wall_seconds': time.perf_counter() - started,
              'process_cpu_seconds': cpu_seconds, 'peak_rss_bytes': peak_rss,
              'monitored_process_ids': sorted(monitored_pids),
              'memory_scope': 'Maximum sampled process-tree RSS or individual Windows peak working set, whichever is larger',
              'fit': fit, 'best': best}
    write_json(folder / 'supervised.json', record)
    if not valid:
        raise RuntimeError(f'No valid completed checkpoint: {folder}; inspect worker.log')
    return record
