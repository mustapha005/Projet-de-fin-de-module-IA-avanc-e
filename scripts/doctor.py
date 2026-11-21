"""Record the actual reference-host environment without collecting credentials."""
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

import psutil

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cpu = platform.processor()
    if sys.platform == "win32":
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                           r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
            cpu = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
    report = {
        "cpu": cpu, "platform": platform.platform(), "python": platform.python_version(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": os.cpu_count(), "ram_bytes": psutil.virtual_memory().total,
        "packages": dict(sorted((d.metadata["Name"], d.version)
                                for d in importlib.metadata.distributions())),
        "reference_machine_frozen": bool(subprocess.check_output(
            ["git", "tag", "--list", "protocol-frozen"], cwd=ROOT, text=True).strip()),
    }
    target = ROOT / "docs" / "machine.json"
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
