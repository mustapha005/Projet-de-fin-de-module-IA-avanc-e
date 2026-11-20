"""Download public datasets with checksums, resumable reuse, and safe ZIP extraction."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
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


def transfer(url: str, temporary: Path, name: str) -> int:
    """Resume a source-matched partial download, validating HTTP range semantics."""
    state_path = temporary.with_suffix(temporary.suffix + ".json")
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    offset = temporary.stat().st_size if temporary.exists() and state.get("url") == url else 0
    if offset and offset == state.get("total_bytes"):
        with zipfile.ZipFile(temporary) as complete:
            if complete.testzip():
                raise ValueError("Complete partial archive failed CRC validation")
        return offset
    headers = {"User-Agent": "SAN1-academic-reproducibility/0.1", "Accept-Encoding": "identity"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
        validator = state.get("etag") or state.get("last_modified")
        if validator:
            headers["If-Range"] = validator
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=90) as response:
        first = response.read(4096)
        if response.status == 206:
            matched = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", response.headers.get("Content-Range", ""))
            if not offset or not matched or int(matched[1]) != offset:
                raise ValueError("Invalid Content-Range; refusing to append unrelated bytes")
            expected_size = int(matched[3])
            if state.get("total_bytes") and state["total_bytes"] != expected_size:
                raise ValueError("Source size changed during resume")
            if state.get("etag") and response.headers.get("ETag") not in (None, state["etag"]):
                raise ValueError("Source ETag changed during resume")
            mode = "ab"
        elif response.status == 200:
            if not first.startswith(b"PK"):
                raise ValueError("Download is not a ZIP/XLSX file (possibly a challenge page)")
            offset = 0
            length = response.headers.get("Content-Length")
            expected_size = int(length) if length else None
            mode = "wb"
        else:
            raise ValueError(f"Unexpected HTTP status: {response.status}")
        write_json(state_path, {"url": url, "etag": response.headers.get("ETag"),
                                "last_modified": response.headers.get("Last-Modified"),
                                "total_bytes": expected_size})
        count = offset + len(first)
        next_report = (count // (4 * 1024**2) + 1) * 4 * 1024**2
        print(f"{name}: {'resuming' if offset else 'starting'} at {offset} bytes, total={expected_size}", flush=True)
        with temporary.open(mode) as stream:
            stream.write(first)
            stream.flush()
            while chunk := response.read1(64 * 1024):
                stream.write(chunk)
                stream.flush()
                count += len(chunk)
                if count >= next_report:
                    print(f"{name}: {count / 1024**2:.1f} MiB downloaded", flush=True)
                    next_report += 4 * 1024**2
        if expected_size and count != expected_size:
            raise OSError(f"Incomplete download: {count}/{expected_size}; partial bytes retained")
    return count


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
        for attempt in range(6):
            temporary = target.with_suffix(target.suffix + ".part")
            try:
                print(f"Requesting {name}, source {specification['urls'].index(url) + 1}, attempt {attempt + 1}", flush=True)
                count = transfer(url, temporary, name)
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
