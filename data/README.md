# Data preparation

Run `python scripts/data_pipeline.py` in the isolated environment. Downloaded
archives live in `data/downloads/`, extracted data in `data/raw/`, and both are
Git-ignored. Scripts never upload source data.

Download sources, SHA-256 checksums, byte sizes, and acquisition timestamps are
written to `data/provenance.json`. Existing downloads are verified before reuse.
Failed downloads are not treated as completed files. ZIP extraction rejects
absolute paths, traversal, and symlinks.

Prepared manifests identify benign=0 and malignant=1. Masks/normal images are
excluded. The dedup and split reports document removed images, conflicting-label
clusters, stratification, actual label fractions, and overlap checks.

Primary sources and licensing status are in `docs/DATA_CARD.md`. Attribute both
the datasets and their descriptors in the final article. No classifier training
or test evaluation is part of data preparation.
