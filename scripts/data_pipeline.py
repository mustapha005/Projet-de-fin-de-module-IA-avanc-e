"""Acquire, inventory, clean, split, and audit SAN-1 data without model evaluation."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import imagehash
import pandas as pd
from PIL import Image

from scripts.download_data import DATA, main as download, sha256_file, write_json
from src.data import audit_known_groups, audit_splits, deduplicate, label_subsets, near_pairs, published_constraints, split_busi


def image_record(path: Path, cohort: str, label: int) -> dict:
    """Read original pixels once for deterministic size/hash inventory."""
    with Image.open(path) as image:
        image.load()
        width, height = image.size
        phash = str(imagehash.phash(image.convert("L"), hash_size=8))
        mode = image.mode
    return {"image_id": f"{cohort}/{path.stem}", "path": path.relative_to(ROOT).as_posix(),
            "label": label, "class_name": {0: "benign", 1: "malignant"}[label],
            "cohort": cohort, "sha256": sha256_file(path), "phash": phash,
            "width": width, "height": height, "mode": mode}


def inventory_busi() -> tuple[pd.DataFrame, dict]:
    """Reject unexpected file labels; count normal images separately from masks."""
    records = []
    counts = Counter()
    images = sorted((DATA / "raw" / "busi").rglob("*.png"))
    if not images:
        raise FileNotFoundError("No BUSI PNGs: run scripts/download_data.py first")
    for path in images:
        category = path.parent.name.lower()
        if category not in {"benign", "malignant", "normal"}:
            raise ValueError(f"Unrecognized BUSI class folder: {path}")
        if "_mask" in path.stem.lower():
            counts["mask_files"] += 1
            continue
        if not re.fullmatch(rf"{category} \(\d+\)", path.stem):
            raise ValueError(f"Unexpected BUSI image name: {path.name}")
        counts[category] += 1
        if category != "normal":
            records.append(image_record(path, "busi", int(category == "malignant")))
    frame = pd.DataFrame(records)
    if frame.image_id.duplicated().any():
        raise ValueError("Multiple copies of the BUSI image tree detected")
    return frame, dict(counts)


def inventory_breast() -> tuple[pd.DataFrame, dict]:
    """Use the published Classification column, never BI-RADS-derived labels."""
    folder = DATA / "raw" / "breast"
    books = list(folder.glob("*.xlsx"))
    if len(books) != 1:
        raise ValueError(f"Expected one BrEaST workbook, found {len(books)}")
    sheets = pd.read_excel(books[0], sheet_name=None)
    candidates = [(name, frame) for name, frame in sheets.items()
                  if {"Image_filename", "Classification"} <= set(frame.columns)]
    if len(candidates) != 1:
        raise ValueError(f"Cannot identify clinical sheet. Schemas: {[(n, list(f.columns)) for n, f in sheets.items()]}")
    sheet_name, metadata = candidates[0]
    if metadata.Image_filename.isna().any() or metadata.Image_filename.duplicated().any():
        raise ValueError("Missing or repeated BrEaST image filenames")
    paths = {}
    for path in folder.rglob("*.png"):
        if path.name in paths:
            raise ValueError(f"Duplicate BrEaST filename: {path.name}")
        paths[path.name] = path
    records = []
    counts = Counter()
    for row in metadata.to_dict("records"):
        category = str(row["Classification"]).strip().lower()
        if category not in {"benign", "malignant", "normal"}:
            raise ValueError(f"Unrecognized BrEaST Classification: {category!r}")
        filename = str(row["Image_filename"]).strip()
        if filename not in paths:
            raise FileNotFoundError(f"Missing BrEaST image: {filename}")
        counts[category] += 1
        if category != "normal":
            records.append(image_record(paths[filename], "breast", int(category == "malignant")))
    report = {"class_counts": dict(counts), "metadata_rows": len(metadata),
              "sheet": sheet_name, "columns": list(metadata.columns),
              "label_source": "Classification", "normal_excluded": counts["normal"],
              "raw_png_files_including_masks": len(paths)}
    return pd.DataFrame(records), report


def write_frame(path: Path, frame: pd.DataFrame) -> None:
    """Write a deterministic manifest, protecting any frozen experimental split."""
    content = frame.to_csv(index=False, lineterminator="\n")
    frozen = subprocess.run(["git", "tag", "--list", "protocol-frozen"], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout.strip()
    if frozen and path.exists() and path.read_text(encoding="utf-8") != content:
        raise RuntimeError(f"Frozen manifest would change: {path}; user review required")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".csv.part")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)


def verify_manifest_files(frame: pd.DataFrame) -> None:
    """Recheck raw files against the recorded inventory, including on offline runs."""
    for row in frame.to_dict("records"):
        path = ROOT / row["path"]
        if sha256_file(path) != row["sha256"]:
            raise ValueError(f"Raw image checksum mismatch: {path}")


def run(offline: bool = False) -> dict:
    """Execute Phase 0 data processing; no model, tuning, or prediction is imported."""
    write_json(DATA / "pipeline_status.json", {"status": "IN_PROGRESS"})
    if not offline:
        download()
    folder = DATA / "manifests"
    folder.mkdir(parents=True, exist_ok=True)
    # Previously recorded inventories must still match, before any regeneration.
    for name in ("busi_inventory", "breast_external"):
        path = folder / f"{name}.csv"
        if path.exists():
            verify_manifest_files(pd.read_csv(path, dtype={"phash": str}))
    busi, busi_counts = inventory_busi()
    external, external_counts = inventory_breast()
    known_pairs, forbidden_ids = published_constraints(ROOT / "configs" / "busi_published_pairs.json")
    clean, dedup = deduplicate(busi, known_pairs=known_pairs, forbidden_ids=forbidden_ids)
    published_audit = audit_known_groups(clean, known_pairs, forbidden_ids)
    cross_pairs = near_pairs(clean, external)
    external_internal_pairs = near_pairs(external)
    write_json(DATA / "dedup_report.json", dedup)
    write_json(DATA / "cohort_overlap_report.json", {
        "cross_cohort_pairs": cross_pairs,
        "external_internal_pairs": external_internal_pairs,
        "external_policy": "Retain external cohort unchanged; report within-cohort similarity"})
    splits = split_busi(clean)
    subsets = label_subsets(splits)
    report = audit_splits(splits, subsets, external)
    report.update(published_audit)
    for name, frame in [("busi_inventory", busi), ("busi_clean", clean),
                        ("breast_external", external.assign(split="external")),
                        ("busi_splits", splits), ("label_subsets", subsets)]:
        write_frame(folder / f"{name}.csv", frame)
    write_json(DATA / "inventory_report.json", {
        "busi": busi_counts, "breast": external_counts,
        "busi_retained_class_counts": {str(k): int(v) for k, v in clean.label.value_counts().items()},
        "busi_image_sizes": {"min_width": int(busi.width.min()), "max_width": int(busi.width.max()),
                             "min_height": int(busi.height.min()), "max_height": int(busi.height.max())},
    })
    report["manifest_sha256"] = {p.name: sha256_file(p) for p in sorted(folder.glob("*.csv"))}
    write_json(DATA / "split_report.json", report)
    write_json(DATA / "pipeline_status.json", {"status": "PASS", "phase": "data_preparation",
                                               "manifest_sha256": report["manifest_sha256"]})
    print(json.dumps({"status": report["status"], "busi_raw": busi_counts,
                      "busi_retained": len(clean), "removed": dedup["removed_images"],
                      "conflict_images": dedup["conflict_images"],
                      "external": external_counts["class_counts"],
                      "splits": report["split_counts"], "subsets": report["subsets"],
                      "cross_cohort_pairs": len(cross_pairs)}, indent=2), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Use downloaded/extracted data; no network calls")
    args = parser.parse_args()
    try:
        run(offline=args.offline)
    except Exception as error:
        failure = {"status": "FAIL", "error": f"{type(error).__name__}: {error}"}
        write_json(DATA / "last_data_failure.json", failure)
        write_json(DATA / "pipeline_status.json", failure)
        raise
