"""Download/verify BUSI; the shared acquisition pipeline also obtains BrEaST."""
from download_data import DATA, SOURCES, fetch, safe_extract, write_json
import json

if __name__ == "__main__":
    manifest = DATA / "provenance.json"
    provenance = json.loads(manifest.read_text()) if manifest.exists() else {}
    archive = fetch("busi", SOURCES["busi"], provenance)
    target = DATA / "raw" / "busi"
    safe_extract(archive, target)
    write_json(target / ".extracted.json", {"archive_sha256": provenance["busi"]["sha256"]})
