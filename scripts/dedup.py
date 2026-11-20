"""Rebuild the cleaned BUSI manifest from its original image inventory."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from src.data import deduplicate
from scripts.download_data import DATA, write_json

if __name__ == "__main__":
    original = pd.read_csv(DATA / "manifests" / "busi_inventory.csv", dtype={"phash": str})
    clean, report = deduplicate(original)
    clean.to_csv(DATA / "manifests" / "busi_clean.csv", index=False)
    write_json(DATA / "dedup_report.json", report)
    print(f"Retained {len(clean)} of {len(original)} BUSI images")
