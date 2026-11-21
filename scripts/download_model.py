"""Acquire a revision-pinned public DINOv2 checkpoint without executing remote code."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(ROOT / ".cache" / "huggingface"))
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
from huggingface_hub import HfApi, snapshot_download


def main():
    config_path = ROOT / "configs" / "backbone.json"
    model_id = "facebook/dinov2-small"
    if config_path.exists():
        previous = json.loads(config_path.read_text(encoding="utf-8"))
        revision = previous["revision"]
    else:
        previous = None
        revision = HfApi(token=False).model_info(model_id).sha
    folder = ROOT / "weights" / "dinov2-small"
    snapshot_download(repo_id=model_id, revision=revision, token=False,
                      local_dir=folder, allow_patterns=["config.json", "preprocessor_config.json", "model.safetensors"],
                      max_workers=2)
    checksums = {}
    for name in ("config.json", "preprocessor_config.json", "model.safetensors"):
        path = folder / name
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        checksums[name] = {"sha256": digest, "bytes": path.stat().st_size}
    if previous and previous["files"] != checksums:
        raise ValueError("Pinned checkpoint files changed")
    architecture = json.loads((folder / "config.json").read_text())
    preprocessing = json.loads((folder / "preprocessor_config.json").read_text())
    report = {"model_id": model_id, "revision": revision, "license": "Apache-2.0",
              "source_url": f"https://huggingface.co/{model_id}/tree/{revision}",
              "local_path": folder.relative_to(ROOT).as_posix(), "files": checksums,
              "hidden_size": architecture["hidden_size"],
              "num_hidden_layers": architecture["num_hidden_layers"],
              "patch_size": architecture["patch_size"],
              "image_mean": preprocessing["image_mean"], "image_std": preprocessing["image_std"],
              "experiment_image_size": 224, "trust_remote_code": False}
    config_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
