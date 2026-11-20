"""Check current splits against published duplicates independently of pHash."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from scripts.download_data import write_json
from src.data import article_image_id, audit_known_groups, published_constraints


def image_id(number: int) -> str:
    return article_image_id(number)


def main():
    published = json.loads((ROOT / "configs" / "busi_published_pairs.json").read_text())
    splits = pd.read_csv(ROOT / "data" / "manifests" / "busi_splits.csv").set_index("image_id")
    remaining = []
    normal_conflicts = []
    for left, right in published["pairs"]:
        a, b = image_id(left), image_id(right)
        if a in splits.index and b in splits.index:
            remaining.append({"left": a, "right": b, "left_split": splits.loc[a, "split"],
                              "right_split": splits.loc[b, "split"],
                              "crosses_split": splits.loc[a, "split"] != splits.loc[b, "split"]})
        if left <= 647 < right and a in splits.index:
            normal_conflicts.append({"included": a, "normal_duplicate": b})
    report = {"source": published["source_url"], "published_pairs": published["pair_count"],
              "retained_duplicate_pairs": remaining,
              "crossing_pairs": sum(p["crosses_split"] for p in remaining),
              "retained_normal_conflicts": normal_conflicts,
              "status": "PASS" if not remaining and not normal_conflicts else "FAIL"}
    pairs, forbidden = published_constraints(ROOT / "configs" / "busi_published_pairs.json")
    try:
        report.update(audit_known_groups(splits.reset_index(), pairs, forbidden))
    except ValueError as error:
        report.update(status="FAIL", graph_error=str(error))
    write_json(ROOT / "data" / "published_duplicate_audit.json", report)
    print(json.dumps(report, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
