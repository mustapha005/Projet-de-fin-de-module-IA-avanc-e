"""Download/verify the BrEaST image archive and clinical metadata."""
from download_data import DATA, SOURCES, fetch, safe_extract, write_json
import json
import shutil

if __name__ == "__main__":
    manifest = DATA / "provenance.json"
    provenance = json.loads(manifest.read_text()) if manifest.exists() else {}
    archive = fetch("breast_images", SOURCES["breast_images"], provenance)
    target = DATA / "raw" / "breast"
    safe_extract(archive, target)
    write_json(target / ".extracted.json", {"archive_sha256": provenance["breast_images"]["sha256"]})
    metadata = fetch("breast_metadata", SOURCES["breast_metadata"], provenance)
    shutil.copy2(metadata, target / metadata.name)
