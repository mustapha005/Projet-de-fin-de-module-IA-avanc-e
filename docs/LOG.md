# Project log

## 2026-11-20 — Codex — Phase 0 plan

The workspace was empty. Read the complete supplied master prompt and extracted
both course DOCX files. The course requirements and SAN-1 scope agree; the master
prompt adds implementation choices. Local input copies and source hashes will
be retained for traceability. The active request is to read these sources and
start the project, not to claim completed final deliverables.

Steps: establish an isolated data environment and Git repository; verify primary
data sources and licenses; download with provenance/checksums; build inventories;
exclude masks/normal images; deduplicate before stratified splitting; generate
nested subsets; audit all overlaps and record a data card. Then proceed to the
literature/protocol phase if the data gate is met.

Risks: dead BUSI host, ambiguous distribution terms, class-label discrepancies,
cross-label duplicate images, missing BUSI patient identifiers, limited laptop
CPU/RAM. A split that leaks near-duplicates invalidates all subsequent metrics.
No main runs or performance-based data changes are allowed during setup.

Initial hardware: Intel Core i5-8265U, 4 physical / 8 logical cores, approximately
15.75 GiB RAM. Reference-machine choice and thread count are provisional until
benchmarking. GNU Make is not on PATH, so equivalent Python commands are provided.

J5 (24 November) status: as of 20 November, no experimental results or ablations.
The complete-results milestone is at risk; no backdated completion is claimed.

### Startup checkpoint

Implemented download/provenance checks, safe ZIP extraction, image inventory,
pHash connected-component deduplication with conflicting-label quarantine,
fixed stratified splits, nested label subsets, and failure-on-leakage checks.
Seven integrity tests pass using the existing Python environment. Syntax
compilation also passes. Full pinned-environment/data validation remains pending;
see `docs/reviews/AUDIT_2026-11-20_phase0_start.md`.

Verified TCIA metadata download: 256 records, of which 154 benign, 98 malignant,
four normal. The image archives are still downloading. BUSI's original host
returns an HTML challenge; public Kaggle version 1 metadata confirms its stated
CC0 license. Full provenance and original-author attribution are retained.

Network throughput is limiting setup: initial pip download timed out; a longer
retry was replaced with uv's concurrent installer. Neither a completed lockfile
nor an installed experiment stack is claimed yet. No training, predictions,
test-based selection, or hypothesis testing has occurred.

While waiting for downloads, started independent literature preparation using
the deep-research skill: adaptation methods, recent ultrasound studies, and
domain-shift/validity evidence. This overlaps preparation only; the data phase
exit gate remains open, and no experiment can start from this checkpoint.

Exact next step: finish pinned dependency installation and all checksummed
downloads, run `.venv/Scripts/python.exe scripts/data_pipeline.py --offline`,
inspect duplicate/conflict components and split reports, rerun integrity tests
inside `.venv`, generate the environment lock, and audit Phase 0. Then complete
the evidence-based protocol and benchmark. H1–H3 are untested.
