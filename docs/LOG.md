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

### Phase 1 completed; Phase 2 plan

Saved the completed literature synthesis and 24-entry verified bibliography;
15 entries are dated 2024–2026. Root read the synthesis, verified the ResNet
technical report, and checked versioned PEFT/bootstrap documentation plus
installed library license evidence. `scripts/audit_references.py` passes.

The full protocol now specifies architecture/gradients, preprocessing and LP
views, search ties, validation-only F1 threshold, class-stratified paired
bootstrap, conservative H1–H3 clause decisions, cap accounting, interrupted-run
policy, ablations and error analysis. D008–D011 document clarifications before
results. Phase 1 audit passes; no protocol freeze or main/tuning results exist.

Phase 2 plan: implement shared development-only datasets and four model paths;
check gradient masks and augmentation reproducibility; measure one epoch per
method/fraction and LP cold extraction with actual CPU/RSS tracking; project the
complete workload and set T_MAX; implement/train the two-epoch development smoke
and test the metric/deadline/provenance paths. Risks: laptop thermal slowdown,
LoRA backward cost despite few trainable weights, incomplete-cap checkpoints,
cache costs, and accidental test access. Test images remain inaccessible to
benchmark/training interfaces. Do not tag until all Phase 2 gates pass.

## 2026-11-21 — Codex — Phase 2 benchmark and integration

All 12 development-only timing cells completed on the i5-8265U with four intra-op
threads, one interop thread, FP32 and no accelerator. Full-data epoch time
(training plus full validation): PFT 83.07 s, LoRA 139.38 s, CNN 53.78 s. LP
full-data cold extraction/fit/validation is about 265 s. No benchmark AUC or test
prediction was computed. The largest measured RSS is approximately 3.37 GiB.

`scripts/project_compute.py` proposes T_MAX=1,440 s (24 min), using the written
ten-slowest-epochs / 1.25×cold-LP rule. The 23 tuning fits, 36 main runs and 21
ablations project to 21.64 elapsed CPU hours, or 25.96 h with 20% headroom. These
are estimates, not consumed compute; no budget fallbacks are currently needed.
Per-cell measurements and assumptions are in `docs/benchmark/`.

Implemented development-only image loading, exact PFT/LoRA trainability, seeded
augmentation, metrics/paired bootstrap, atomic checkpoint selection and a parent
deadline supervisor. Model, statistical and training-policy tests pass (15 new
tests in addition to 16 data/download tests). The two-epoch smoke is now running,
including checkpoint replay, LP cache debit and intentional deadline failure.
No main/tuning run has started and results/ is empty. Do not freeze until smoke,
provenance and portable-line-ending checks are complete.

The first smoke completed in 283.27 s with checkpoint replay, cache debit and
synthetic statistics passing. Inspection exposed a false resource measurement:
the supervisor saw the Windows virtualenv launcher (~4 MiB) instead of its real
Python child. Treat its overall PASS as superseded; archived evidence is in
`docs/reviews/smoke_before_process_tree_fix.json`. The benchmark measured memory
inside each worker and is unaffected. The supervisor now samples and terminates
the entire process tree, and smoke rejects implausible RSS/CPU measurements.

D012 fixes another pre-freeze defect: explicit LF serialization prevents Git
checkout from changing recorded byte hashes. All parsed CSV/JSON content stayed
identical, then the actual pipeline regenerated current hashes and development
views. Historic Phase 0 CRLF hashes remain only as superseded audit evidence.
The revised integration run is in progress; 31 full-suite tests passed in 1.65 s.

### Phase 2 integration passed; checkout/freeze checkpoint

The corrected smoke passed in 255.88 s (under ten minutes). All four checkpoints
reproduce their selected validation probabilities; LP cache reuse is charged,
real-test access is rejected, manifests remain unchanged and synthetic paired
bootstrap behaves correctly. Resource measurement now includes the actual worker
tree. The intentional impossible deadline kills the process tree and cannot
publish an untrained result. A separate 11-second CNN cap retained a valid
completed checkpoint and recovered parameter/count/timing metadata after parent
termination; see `docs/benchmark/capped_checkpoint_recovery.json`.

Implemented the serial tuning/main/ablation controller and immutable-input
validation. The prepared experiment contract pins source/data/model/environment
hashes, exact reference hardware, 24-minute cap, 50 epochs and all three seeds.
No tag or scientific result exists yet. Next: commit the implementation, verify
all protected bytes from a clean Git checkout, record the Phase 2 audit, then
create protocol-frozen and begin the registered tuning grid.

### Phase 2 exit gate and Phase 3 plan

Final pre-freeze suite: 31 tests PASS. The clean clone of commit 917c094 matches
all 21 protected SHA-256s and regenerates the same 414-row development view.
Phase 2 verdict is PASS WITH FIXES; see `docs/reviews/AUDIT_2026-11-21_phase2.md`.
Results/ is empty before tagging. No test prediction has been made.

Phase 3 plan: create the protocol-frozen tag on the audited commit; run exactly
the registered seed-0 10% candidates, save selection ledgers, then execute the
36 final method/fraction/seed cells with one selected-checkpoint evaluation each.
Start with LP tuning to exercise the frozen contract and cache accounting. All
jobs remain serial, bounded and supervised. Failures retain their attempt logs;
do not silently add candidates or extend caps. Keep tests sealed during tuning.
Milestone J5 still has no main results or ablations; completion is not claimed.
