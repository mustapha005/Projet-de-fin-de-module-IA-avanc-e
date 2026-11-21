"""Verify immutable scientific inputs before tuning, final training or evaluation."""
import json
import platform
import subprocess
import importlib.metadata

import psutil

from src.runtime import ROOT, sha256


def verify_frozen() -> dict:
    result = subprocess.run(['git', 'show', 'protocol-frozen:configs/experiment.json'],
                             cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError('No committed frozen experiment contract')
    frozen = json.loads(result.stdout)
    current = json.loads((ROOT / 'configs/experiment.json').read_text())
    if current != frozen:
        raise RuntimeError('Frozen experiment settings changed; user review required')
    for name, digest in frozen['protected_sha256'].items():
        if sha256(ROOT / name) != digest:
            raise RuntimeError(f'Frozen input changed: {name}; user review required')
    machine = frozen['reference_machine']
    if platform.python_version() != machine['python'] or platform.platform() != machine['platform']:
        raise RuntimeError('Interpreter/platform differs from the reference machine')
    if psutil.cpu_count(logical=False) != machine['physical_cores'] or psutil.cpu_count() != machine['logical_cores']:
        raise RuntimeError('CPU core count differs from the reference machine')
    if psutil.virtual_memory().total != machine['ram_bytes']:
        raise RuntimeError('Installed RAM differs from the reference machine')
    if platform.system() == 'Windows':
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
            cpu = winreg.QueryValueEx(key, 'ProcessorNameString')[0].strip()
        if cpu != machine['cpu']:
            raise RuntimeError('CPU model differs from the reference machine')
    for name, version in frozen['package_versions'].items():
        if importlib.metadata.version(name) != version:
            raise RuntimeError(f'Installed package changed: {name}')
    return frozen


def validate_run_config(config: dict) -> dict | None:
    if config.get('purpose') == 'smoke':
        if config['max_epochs'] != 2 or config['fraction'] != .01 or config['seed'] != 0:
            raise ValueError('Smoke exception is limited to the two-epoch development fixture')
        return None
    frozen = verify_frozen()
    for field in ('threads', 'max_epochs', 'patience', 'cap_seconds'):
        if config[field] != frozen[field]:
            raise ValueError(f'Run changes frozen {field}')
    if config['seed'] not in frozen['seeds'] or config['fraction'] not in frozen['fractions']:
        raise ValueError('Run changes frozen seed or fraction')
    if config.get('image_size') != frozen['image_size']:
        raise ValueError('Run changes frozen input resolution')
    if config['purpose'] == 'tune' and (config['fraction'] != .1 or config['seed'] != 0):
        raise ValueError('Tuning outside seed-0 10% is forbidden')
    if config['purpose'] not in {'tune', 'main', 'ablation'}:
        raise ValueError('Unknown experiment purpose')
    method = config['method']
    if method not in {'LP', 'PFT', 'LoRA', 'CNN'}:
        raise ValueError('Unknown method')
    hp = {k: config[k] for k in (('C',) if method == 'LP' else ('lr', 'weight_decay'))}
    if config['purpose'] == 'tune':
        search = json.loads((ROOT / 'configs/search.json').read_text())
        if hp not in search[method]:
            raise ValueError('Hyperparameters outside the frozen search')
    else:
        selection = json.loads((ROOT / 'configs/frozen' / f'{method}.json').read_text())
        if hp != selection['hyperparameters']:
            raise ValueError('Final run differs from selected hyperparameters')
    expected = {'depth': 2, 'rank': 8, 'lora_depth': 12, 'augmentation': True}
    if config['purpose'] == 'ablation':
        name = config.get('ablation_name')
        variants = {'lora_last2': ('LoRA', {'lora_depth': 2}),
                    'lora_rank4': ('LoRA', {'rank': 4}), 'lora_rank16': ('LoRA', {'rank': 16}),
                    'pft_depth4': ('PFT', {'depth': 4}), 'lora_no_augmentation': ('LoRA', {'augmentation': False})}
        if name not in variants or variants[name][0] != method:
            raise ValueError('Unregistered ablation')
        if name != 'lora_last2' and config['fraction'] != .1:
            raise ValueError('This ablation is restricted to 10%')
        expected.update(variants[name][1])
    if any(config.get(k, default) != default for k, default in expected.items()):
        raise ValueError('Run changes the registered adaptation/augmentation setting')
    return frozen
