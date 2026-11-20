"""Download public datasets with checksums, resumable reuse, and safe ZIP extraction."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import stat
import time
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = {
    "busi": {
        "filename": "Dataset_BUSI.zip",
        "urls": ["https://scholar.cu.edu.eg/Dataset_BUSI.zip",
                 "https://www.kaggle.com/api/v1/datasets/download/aryashah2k/breast-ultrasound-images-dataset"],
        "extract_to": "busi",
    },
    "breast_images": {
        "filename": "BrEaST-Lesions_USG-images_and_masks-Dec-15-2023.zip",
        "urls": ["https://www.cancerimagingarchive.net/wp-content/uploads/BrEaST-Lesions_USG-images_and_masks-Dec-15-2023.zip"],
        "extract_to": "breast",
    },
    "breast_metadata": {
        "filename": "BrEaST-Lesions-USG-clinical-data-Dec-15-2023.xlsx",
        "urls": ["https://www.cancerimagingarchive.net/wp-content/uploads/BrEaST-Lesions-USG-clinical-data-Dec-15-2023.xlsx"],
    },
}


def sha256_file(path: Path) -> str:
    """Hash a file without loading an entire archive into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value) -> None:
    """Atomically replace a JSON record after serializing successfully."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def safe_extract(archive: Path, target: Path) -> None:
    """Reject traversal/symlinks and publish a marker only after CRC validation."""
    target.mkdir(parents=True, exist_ok=True)
    root = target.resolve()
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            name = member.filename.replace("\\", "/")
            path = Path(name)
            resolved = (root / path).resolve()
            if (path.is_absolute() or ".." in path.parts or ":" in name
                    or not resolved.is_relative_to(root)
                    or stat.S_ISLNK(member.external_attr >> 16)):
                raise ValueError(f"Unsafe ZIP member: {member.filename}")
        bad = bundle.testzip()
        if bad:
            raise ValueError(f"Corrupt ZIP member: {bad}")
        bundle.extractall(root)


def fetch(name: str, specification: dict, provenance: dict) -> Path:
    """Fetch one archive; fail closed on changed cached files or non-ZIP responses."""
    target = DATA / "downloads" / specification["filename"]
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = provenance.get(name)
    if target.exists():
        actual_hash = sha256_file(target)
        if not existing or existing["sha256"] != actual_hash:
            raise ValueError(f"Unrecorded or altered download: {target}. Review before reuse.")
        print(f"Verified cached {name}: {actual_hash}", flush=True)
        return target
    errors = []
    for url in specification["urls"]:
        for attempt in range(2):
            temporary = target.with_suffix(target.suffix + ".part")
            try:
                print(f"Requesting {name}, source {specification['urls'].index(url) + 1}, attempt {attempt + 1}", flush=True)
                request = urllib.request.Request(url, headers={"User-Agent": "SAN1-academic-reproducibility/0.1"})
                with urllib.request.urlopen(request, timeout=45) as response:
                    first = response.read(4096)
                    if not first.startswith(b"PK"):
                        raise ValueError("Download is not a ZIP/XLSX file (possibly a challenge page)")
                    expected_size = response.headers.get("Content-Length")
                    print(f"{name}: valid ZIP header, expected bytes={expected_size}", flush=True)
                    count = len(first)
                    next_report = 4 * 1024 * 1024
                    with temporary.open("wb") as stream:
                        stream.write(first)
                        stream.flush()
                        while chunk := response.read1(64 * 1024):
                            stream.write(chunk)
                            stream.flush()
                            count += len(chunk)
                            if count >= next_report:
                                print(f"{name}: {count / 1024**2:.1f} MiB downloaded", flush=True)
                                next_report += 4 * 1024 * 1024
                    if expected_size and count != int(expected_size):
                        raise ValueError(f"Incomplete download: {count}/{expected_size}")
                with zipfile.ZipFile(temporary) as archive:
                    if archive.testzip():
                        raise ValueError("ZIP CRC validation failed")
                digest = sha256_file(temporary)
                prior = provenance.get(name)
                if prior and prior["sha256"] != digest:
                    raise ValueError("Source content changed from the recorded version; manual review required")
                provenance[name] = {"source_url": url, "filename": target.name,
                                    "sha256": digest, "bytes": count,
                                    "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
                                    "failed_sources": errors}
                temporary.replace(target)
                write_json(DATA / "provenance.json", provenance)
                print(f"Downloaded and verified {name}: {digest}", flush=True)
                return target
            except (urllib.error.URLError, ValueError, OSError, zipfile.BadZipFile) as error:
                errors.append({"url": url, "attempt": attempt + 1,
                               "error": f"{type(error).__name__}: {error}"})
                print(f"{name}: {errors[-1]['error']}", flush=True)
                if isinstance(error, ValueError):
                    break
                time.sleep(1)
    write_json(DATA / "download_failures.json", {"dataset": name, "errors": errors})
    raise RuntimeError(f"No usable source for {name}. See data/download_failures.json")


def main() -> None:
    manifest_path = DATA / "provenance.json"
    provenance = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    for name in ("breast_metadata", "breast_images", "busi"):
        specification = SOURCES[name]
        archive = fetch(name, specification, provenance)
        if "extract_to" in specification:
            target = DATA / "raw" / specification["extract_to"]
            marker = target / ".extracted.json"
            digest = provenance[name]["sha256"]
            if marker.exists():
                if json.loads(marker.read_text())["archive_sha256"] != digest:
                    raise ValueError(f"Archive mismatch at {target}; review extraction")
            else:
                safe_extract(archive, target)
                write_json(marker, {"archive_sha256": digest})
                print(f"Extracted {name}", flush=True)
        else:
            target = DATA / "raw" / "breast" / archive.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(archive, target)


if __name__ == "__main__":
    main()
