"""Deterministic, label-aware data cleaning and disjoint split construction."""
from collections import defaultdict
import math

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def phash_distance(left: str, right: str) -> int:
    """Return the Hamming distance between hexadecimal perceptual hashes."""
    return (int(left, 16) ^ int(right, 16)).bit_count()


def near_pairs(records: pd.DataFrame, other: pd.DataFrame | None = None,
               distance: int = 4) -> list[dict]:
    """Enumerate all near-duplicate pairs (cross-cohort when other is provided)."""
    left = records.to_dict("records")
    right = left if other is None else other.to_dict("records")
    pairs = []
    for i, first in enumerate(left):
        for second in right[i + 1:] if other is None else right:
            delta = phash_distance(first["phash"], second["phash"])
            if delta <= distance:
                pairs.append({"left": first["image_id"], "right": second["image_id"],
                              "hamming": delta, "label_conflict": int(first["label"]) != int(second["label"])})
    return pairs


def deduplicate(records: pd.DataFrame, distance: int = 4) -> tuple[pd.DataFrame, dict]:
    """Collapse single-label components; exclude every mixed-label component."""
    records = records.sort_values("image_id").reset_index(drop=True)
    if records.image_id.duplicated().any():
        raise ValueError("Image IDs must be unique")
    parents = {image_id: image_id for image_id in records.image_id}

    def find(image_id):
        while parents[image_id] != image_id:
            parents[image_id] = parents[parents[image_id]]
            image_id = parents[image_id]
        return image_id

    pairs = near_pairs(records, distance=distance)
    for pair in pairs:
        first, second = find(pair["left"]), find(pair["right"])
        parents[max(first, second)] = min(first, second)
    components = defaultdict(list)
    for image_id in parents:
        components[find(image_id)].append(image_id)
    lookup = records.set_index("image_id")
    keep = []
    clusters = []
    for members in sorted(components.values()):
        members.sort()
        labels = sorted(set(int(lookup.loc[item, "label"]) for item in members))
        representative = members[0] if len(labels) == 1 else None
        if representative:
            keep.append(representative)
        if len(members) > 1:
            clusters.append({"members": members, "labels": labels,
                             "representative": representative,
                             "action": "keep_one" if representative else "quarantine_conflict"})
    clean = records[records.image_id.isin(keep)].copy()
    report = {
        "algorithm": "imagehash.phash(hash_size=8), Hamming<=4, connected components",
        "hamming_threshold": distance, "input_images": len(records),
        "retained_images": len(clean), "removed_images": len(records) - len(clean),
        "conflict_components": sum(c["action"] == "quarantine_conflict" for c in clusters),
        "conflict_images": sum(len(c["members"]) for c in clusters if c["action"] == "quarantine_conflict"),
        "clusters": clusters, "near_pairs": pairs,
    }
    return clean, report


def split_busi(records: pd.DataFrame, seed: int = 1234) -> pd.DataFrame:
    """Stratified 70/15/15 image split after cleaning, independent of run seeds."""
    if records.image_id.duplicated().any():
        raise ValueError("Duplicate image IDs")
    ordered = records.sort_values("image_id").reset_index(drop=True)
    train, remaining = train_test_split(ordered, test_size=0.30, random_state=seed,
                                         stratify=ordered.label)
    val, test = train_test_split(remaining, test_size=0.50, random_state=seed,
                                stratify=remaining.label)
    return pd.concat([train.assign(split="train"), val.assign(split="val"),
                      test.assign(split="test")]).sort_values("image_id").reset_index(drop=True)


def label_subsets(splits: pd.DataFrame, seeds=(0, 1, 2)) -> pd.DataFrame:
    """Draw seed-specific, nested class-stratified subsets from training only."""
    train = splits[splits.split == "train"].copy()
    if set(train.label) != {0, 1}:
        raise ValueError("Both training classes are required")
    output = []
    for seed in seeds:
        generator = np.random.default_rng(seed)
        classes = {}
        for label in (0, 1):
            items = sorted(train.loc[train.label == label, "image_id"])
            if len(items) < 4:
                raise ValueError("At least four training images per class are required")
            classes[label] = generator.permutation(items).tolist()
        for fraction in (0.01, 0.1, 1.0):
            for label, items in classes.items():
                count = len(items) if fraction == 1.0 else max(4, math.floor(len(items) * fraction))
                for image_id in items[:count]:
                    output.append({"seed": seed, "fraction": fraction,
                                   "image_id": image_id, "label": label})
    return pd.DataFrame(output)


def audit_splits(splits: pd.DataFrame, subsets: pd.DataFrame,
                 external: pd.DataFrame) -> dict:
    """Fail if data overlap, near-duplicates, or non-nested training subsets exist."""
    if splits.image_id.duplicated().any() or external.image_id.duplicated().any():
        raise ValueError("Repeated image IDs")
    if set(splits.label) != {0, 1} or not set(external.label) <= {0, 1}:
        raise ValueError("Nonbinary ground-truth labels")
    if set(subsets.seed) != {0, 1, 2} or set(subsets.fraction) != {0.01, 0.1, 1.0}:
        raise ValueError("Unexpected seeds or fractions")
    if set(splits.split) != {"train", "val", "test"}:
        raise ValueError("Expected train/val/test splits")
    for split in ("train", "val", "test"):
        if set(splits.loc[splits.split == split, "label"]) != {0, 1}:
            raise ValueError(f"Missing class in {split}")
    pairs = near_pairs(splits)
    mapping = splits.set_index("image_id").split.to_dict()
    crossing = [pair for pair in pairs if mapping[pair["left"]] != mapping[pair["right"]]]
    external_pairs = near_pairs(splits, external)
    exact_overlap = sorted(set(splits.sha256) & set(external.sha256))
    if crossing or external_pairs or exact_overlap:
        raise ValueError(f"Leakage: within={len(crossing)}, cross-cohort={len(external_pairs)}, exact={len(exact_overlap)}")
    train = set(splits.loc[splits.split == "train", "image_id"])
    if set(subsets.image_id) - train:
        raise ValueError("Validation/test image entered a label subset")
    truth = splits.set_index("image_id").label
    if not (subsets.image_id.map(truth).to_numpy() == subsets.label.to_numpy()).all():
        raise ValueError("Subset labels disagree with the source manifest")
    counts = []
    for seed in (0, 1, 2):
        seed_rows = subsets[subsets.seed == seed]
        previous = set()
        for fraction in (0.01, 0.1, 1.0):
            rows = seed_rows[seed_rows.fraction == fraction]
            chosen = set(rows.image_id)
            if rows.image_id.duplicated().any() or not previous <= chosen:
                raise ValueError("Subsets are duplicated or not nested")
            if set(rows.label) != {0, 1} or min(rows.label.value_counts()) < 4:
                raise ValueError("Subset class floor violated")
            counts.append({"seed": seed, "nominal_fraction": fraction, "n": len(rows),
                           "benign": int((rows.label == 0).sum()),
                           "malignant": int((rows.label == 1).sum()),
                           "actual_fraction": len(rows) / len(train)})
            previous = chosen
        if previous != train:
            raise ValueError("100% subset does not equal the full training set")
    return {"status": "PASS", "split_seed": 1234, "near_duplicate_crossings": 0,
            "cross_cohort_near_duplicates": 0, "cross_cohort_exact_duplicates": 0,
            "nested_subsets": True,
            "split_counts": splits.groupby(["split", "label"]).size().unstack(fill_value=0).rename(
                columns={0: "benign", 1: "malignant"}).to_dict("index"),
            "subsets": counts,
            "patient_independence": "UNVERIFIED: BUSI patient IDs are not available"}
