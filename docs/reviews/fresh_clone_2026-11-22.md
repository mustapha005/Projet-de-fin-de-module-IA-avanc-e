# Fresh-clone reproduction check (2026-11-22, Claude Code)

**Verdict: PASS**, with the two environment caveats listed at the end.

## Procedure

1. `git clone` of the local repository at b8d64c1 into an empty scratch folder (tag
   `protocol-frozen` present). The clone had no `data/raw/`, `data/cache/` or `logs/`.
2. Copied in only the Git-ignored inputs a new user would download: the three source
   files in `data/downloads/` (BUSI ZIP, BrEaST ZIP, BrEaST clinical XLSX) and
   `weights/dinov2-small/`. Archives are verified against `data/provenance.json` by
   `scripts/download_data.py`; weights against `configs/backbone.json` by `load_backbone`.
3. In the clone: `scripts/data_pipeline.py` then `scripts/prepare_development.py`
   (the `make data` commands), `python -m unittest discover -s tests` (`make check`) and
   `scripts/smoke.py` (`make smoke`).

## Outcomes

| Step | Outcome |
|---|---|
| Data pipeline | exit 0; 2,103 raw files extracted from the archives; cached archives verified (network traffic was not monitored) |
| Development manifest | exit 0; 414 development records |
| Regenerated vs committed | `git status --porcelain --untracked-files=no` → 0 changed tracked files (all manifests, split/dedup/overlap reports, provenance; Git normalises line endings); byte identity checked directly only for `busi_splits.csv` (SHA-256 1DB2607B…) |
| Unit tests | 39 OK |
| Smoke | PASS: LP, PFT, LoRA, CNN fits PASS with checkpoint replay PASS; cache debit, deadline failure, real-test access guard, manifest immutability, synthetic bootstrap and process-tree resource checks PASS |

The related single-cell rerun (`scripts/rerun_cell.py --cell main_LP_010_s1 --cold`) is
recorded in `docs/reviews/rerun_main_LP_010_s1_cold.json`: re-extracted features are
bit-identical and both test AUCs differ by 0.0 from the logged result.

## Caveats

* GNU `make` is not installed on the reference Windows laptop; the commands behind each
  target were run directly.
* The README commands were not followed literally (downloads were copied in).
* The existing `.venv` interpreter was used, not a reinstall from `requirements.lock`.
  It is the environment whose pinned package versions `verify_frozen()` checked before
  every experiment and in today's audits, but installing from the lock file into a new
  environment was not tested here (`scripts/smoke.py` itself does not call
  `verify_frozen()`).
