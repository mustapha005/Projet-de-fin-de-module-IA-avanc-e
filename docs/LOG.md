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

## 2026-11-20 — Codex — continuation and acquisition recovery

Resumed after interruption. Rechecked Git status, source files, environment imports,
and completed process logs: uv installation and BrEaST image transfer had both
failed on network timeouts. No hidden successful data or environment gate exists.
The source-identification checks and metadata download remain valid.

Plan: reuse uv caches with a longer timeout; retain partial downloads across
retries using source-matched HTTP Range/If-Range and validate response offsets;
rerun data integrity tests, then execute the actual image pipeline. Resume the
literature notes that were interrupted by tool usage limits, saving work early.
No main runs will begin until data, literature, protocol and benchmark gates pass.

Download retry code is being strengthened because the previous implementation
restarted files after each timeout. This is an acquisition-only change, not an
experimental protocol change. A new test initially hit a Windows sandbox access
error on replacing its temporary state file; rerunning outside the sandbox is
required to distinguish that permission issue from a code failure.

### Data acquired and independent duplicate audit

Both complete archives now validate: BUSI 647 binary images (437 benign, 210
malignant; 133 normals excluded); BrEaST 252 binary images (154 benign, 98
malignant; four normals excluded). The first pHash-only pass retained 527 BUSI
images. It had zero pHash crossings, but this was not sufficient evidence.

An independent check against the 237 pairs in the published 2023 critique's
Table B1 found **20 direct duplicate pairs crossing the provisional splits** and
two remaining binary/normal label conflicts. This is a blocking data issue.
Saved the original reports under `docs/reviews/phash_only/`; no model was trained
and no test metric was computed. Added D007 before rebuilding the data.

The combined graph now uses both pHash and the published links; conflicting-label
components, including links to excluded normals, are quarantined. An independent
graph traversal tests components even if an intermediate image was removed.
Plan: rerun all integrity tests, regenerate manifests, require both audits to
pass, and record the corrected counts. Patient independence still cannot be
proved without original BUSI patient IDs.

### Phase 0 completed; Phase 1 plan

The repaired pipeline passes both similarity audits. BUSI retains 488 images:
311 benign / 177 malignant; train/validation/test = 341/73/74. Removal count is
159, including 17 ambiguous-label images. BrEaST has 252 binary cases. Each seed
has 8/33/341 training images; nominal 1% is actually 2.346%, and 10% is 9.677%.
A fresh pipeline execution reproduced all five manifest hashes unchanged; see
`docs/reviews/phase0_manifest_reproduction.json`. Sixteen integrity/download tests
pass. The complete 51-package environment is locked and checked. DINOv2 loads
locally from its pinned revision, with 22,056,576 backbone parameters.

The historical pHash-only failure is preserved and superseded. Phase 0 verdict:
PASS WITH FIXES, detailed in `docs/reviews/AUDIT_2026-11-20_phase0.md`.
No model has been trained and `results/` remains empty.

Phase 1 plan: review the completed 23-reference synthesis (15 from 2024–2026),
finish the protocol's metric/threshold/compound-hypothesis rules, augmentation and
cost accounting, and exact architecture targets; verify missing implementation
citations and licenses. Commit before Phase 2. Risks: treating a non-significant
difference as noninferiority; unfair cache accounting; separate HF query/key/value
layers versus fused qkv; very small internal test and unverified patient groups.
T_MAX and the hardware thread count remain pending real CPU benchmarking.
