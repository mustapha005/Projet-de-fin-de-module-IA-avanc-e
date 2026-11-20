"""Rebuild and audit fixed BUSI splits and seed-specific label subsets."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from src.data import audit_splits, label_subsets, split_busi
from scripts.download_data import DATA, write_json

if __name__ == "__main__":
    folder = DATA / "manifests"
    clean = pd.read_csv(folder / "busi_clean.csv", dtype={"phash": str})
    external = pd.read_csv(folder / "breast_external.csv", dtype={"phash": str})
    splits = split_busi(clean)
    subsets = label_subsets(splits)
    report = audit_splits(splits, subsets, external)
    splits.to_csv(folder / "busi_splits.csv", index=False)
    subsets.to_csv(folder / "label_subsets.csv", index=False)
    write_json(DATA / "split_report.json", report)
    print(report)
