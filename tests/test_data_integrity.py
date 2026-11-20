"""Tests focus on scientific leakage and acquisition failure modes."""
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

import pandas as pd

from scripts.download_data import safe_extract
from src.data import article_image_id, audit_known_groups, audit_splits, deduplicate, label_subsets, split_busi


def fixture(n=100):
    import random
    generator = random.Random(42)
    return pd.DataFrame([{"image_id": f"image_{i:03}", "label": i % 2,
                          "phash": f"{generator.getrandbits(64):016x}", "sha256": f"sha_{i}"}
                         for i in range(n)])


class DataIntegrityTests(unittest.TestCase):
    def test_published_links_cover_dissimilar_hashes_and_normal_conflicts(self):
        frame = pd.DataFrame([{"image_id": "a", "label": 0, "phash": "0000000000000000"},
                              {"image_id": "b", "label": 0, "phash": "ffffffffffffffff"},
                              {"image_id": "c", "label": 1, "phash": "aaaaaaaaaaaaaaaa"}])
        clean, report = deduplicate(frame, known_pairs=[("a", "b")], forbidden_ids={"c"})
        self.assertEqual(clean.image_id.tolist(), ["a"])
        self.assertEqual(report["conflict_images"], 1)

    def test_published_graph_audit_traverses_removed_intermediate(self):
        retained = pd.DataFrame({"image_id": ["a", "c"]})
        with self.assertRaisesRegex(ValueError, "component survives"):
            audit_known_groups(retained, [("a", "b"), ("b", "c")])

    def test_published_id_mapping_respects_class_boundaries(self):
        self.assertEqual(article_image_id(437), "busi/benign (437)")
        self.assertEqual(article_image_id(438), "busi/malignant (1)")
        self.assertEqual(article_image_id(647), "busi/malignant (210)")
        self.assertEqual(article_image_id(648), "busi/normal (1)")
        self.assertEqual(article_image_id(780), "busi/normal (133)")

    def test_transitive_duplicates_cannot_survive_as_separate_samples(self):
        # A~B and B~C, while A and C have distance 8: collapse the whole component.
        frame = pd.DataFrame([{"image_id": c, "label": 0, "phash": h}
                              for c, h in [("a", "0000"), ("b", "000f"), ("c", "00ff")]])
        clean, report = deduplicate(frame)
        self.assertEqual(clean.image_id.tolist(), ["a"])
        self.assertEqual(report["removed_images"], 2)

    def test_conflicting_labels_are_all_quarantined(self):
        frame = pd.DataFrame([{"image_id": "a", "label": 0, "phash": "0000"},
                              {"image_id": "b", "label": 1, "phash": "000f"}])
        clean, report = deduplicate(frame)
        self.assertEqual(len(clean), 0)
        self.assertEqual(report["conflict_images"], 2)

    def test_nested_reproducible_subsets_and_fixed_holdout(self):
        clean = fixture()
        split = split_busi(clean)
        pd.testing.assert_frame_equal(split, split_busi(clean.sample(frac=1, random_state=7)))
        subsets = label_subsets(split)
        pd.testing.assert_frame_equal(subsets, label_subsets(split))
        external = pd.DataFrame([{"image_id": "ext", "phash": "0000000000000000", "label": 1, "sha256": "ext"}])
        report = audit_splits(split, subsets, external)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["subsets"][0]["n"], 8)
        a = set(subsets.query("seed == 0 and fraction == 0.01").image_id)
        b = set(subsets.query("seed == 1 and fraction == 0.01").image_id)
        self.assertNotEqual(a, b)

    def test_external_duplicate_is_a_hard_failure(self):
        split = split_busi(fixture())
        external = split.iloc[[0]].assign(image_id="external_duplicate")
        with self.assertRaisesRegex(ValueError, "Leakage"):
            audit_splits(split, label_subsets(split), external)

    def test_test_record_in_training_subset_is_a_hard_failure(self):
        split = split_busi(fixture())
        subsets = label_subsets(split)
        subsets.loc[0, "image_id"] = split[split.split == "test"].iloc[0].image_id
        external = pd.DataFrame(columns=["image_id", "phash", "label", "sha256"])
        with self.assertRaisesRegex(ValueError, "Validation/test"):
            audit_splits(split, subsets, external)

    def test_changed_subset_label_is_a_hard_failure(self):
        split = split_busi(fixture())
        subsets = label_subsets(split)
        subsets.loc[0, "label"] = 1 - subsets.loc[0, "label"]
        external = pd.DataFrame(columns=["image_id", "phash", "label", "sha256"])
        with self.assertRaisesRegex(ValueError, "labels disagree"):
            audit_splits(split, subsets, external)

    def test_zip_path_traversal_is_rejected_before_any_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "bad.zip"
            with ZipFile(archive, "w") as bundle:
                bundle.writestr("fine.txt", "fine")
                bundle.writestr("../outside.txt", "unsafe")
            with self.assertRaisesRegex(ValueError, "Unsafe ZIP"):
                safe_extract(archive, root / "extract")
            self.assertFalse((root / "outside.txt").exists())
            self.assertFalse((root / "extract" / "fine.txt").exists())


if __name__ == "__main__":
    unittest.main()
