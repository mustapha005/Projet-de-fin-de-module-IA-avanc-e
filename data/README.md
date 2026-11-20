# Data preparation

Run `python scripts/data_pipeline.py` in the isolated environment. Downloaded
archives live in `data/downloads/`, extracted data in `data/raw/`, and both are
Git-ignored. Scripts never upload source data.

Download sources, SHA-256 checksums, byte sizes, and acquisition timestamps are
written to `data/provenance.json`. Existing downloads are verified before reuse.
Interrupted downloads retain source-matched partial files and resume with validated
HTTP Range/If-Range responses where supported. A server returning a full response
restarts the file instead of appending it. Failed downloads are not treated as
completed files. ZIP extraction rejects
absolute paths, traversal, and symlinks.

Prepared manifests identify benign=0 and malignant=1. Masks/normal images are
excluded. The dedup and split reports document removed images, conflicting-label
clusters, stratification, actual label fractions, and overlap checks. Deduplication
also uses the attributed published duplicate-pair facts in
`configs/busi_published_pairs.json`; zero pHash matches alone is insufficient.
Run `python scripts/audit_published_duplicates.py` for the independent author-list
check. The archived pHash-only provisional reports in `docs/reviews/phash_only/`
document an intentionally superseded, failing split and must not be used to train.

Primary sources and licensing status are in `docs/DATA_CARD.md`. Attribute both
the datasets and their descriptors in the final article. No classifier training
or test evaluation is part of data preparation.
