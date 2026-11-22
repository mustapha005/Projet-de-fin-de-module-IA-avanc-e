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

### Phase 3 started — frozen protocol and LP selection

Created lightweight `protocol-frozen` at befa5ba (commit dated 2026-11-21 02:23:12 UTC),
before the first results file. `verify_frozen()` validates all 21 protected
files, exact package versions and reference hardware. Saved design/data
provenance under results/ only after tagging.

All five LP candidates completed at seed 0 / nominal 10%; the predeclared
validation-AUC rule selected C=100. The ledger is `configs/frozen/LP.json`;
candidate evidence is under `results/tuning/`. This is selection evidence, not
test performance or a hypothesis verdict. PFT/LoRA/CNN tuning is running serially
with the frozen epoch/clock caps. Both real test cohorts remain sealed.

Fetched the required TCIA data citation directly over verified HTTPS (HTTP 200),
after the web reader returned 500. Saved the citation and response hash. The
bibliography now has 25 verified entries, 16 from 2024–2026; consistency audit
passes. This attribution-only addition does not change the frozen experiment.

### 2026-11-21 continuation — completed PFT and interrupted LoRA

Re-read the project instructions/current records and checked real process state.
The previous tool session no longer exists, and no matching experiment Python
process is live. LP's five and PFT's six tuning candidates are complete, with
saved selections. LoRA candidate 0 has 42 logged epochs but no fit/supervisor
completion record; its termination cause is unknown. No CNN tuning or real test
evaluation has occurred. The incomplete LoRA checkpoint is not a selected fit.

Frozen-contract verification still passes all 21 hashes, package versions and
hardware checks. PFT's six-entry selection ledger was recomputed against its
validation criterion. Archived completed worker evidence and the incomplete
LoRA history separately. Plan: restart LoRA candidate 0 from initialization as
attempt 2, using the unchanged cap and settings, then continue its remaining
candidates and CNN. This follows the frozen restart rule; no extra optimizer
steps are carried forward from attempt 1. Remain present while costly work runs.

## 2026-11-21 — Claude Code (Opus 5.5) — resume audit and Phase 4 tooling plan

Took over from Codex after its session ran out of tokens. Read README, LOG,
PROTOCOL, DEVIATIONS, REQUIREMENTS and the last 30 commits. Found the Codex-launched
tuning controller (`--phase tune --methods LoRA CNN`) still live under the Codex
app's shell; LoRA candidate 0 attempt 2 completed at the cap (35 epochs, val AUC
0.5507) and candidate 1 started. Attempt 2 reproduced attempt 1's validation AUCs
for all 35 shared epochs, but its median epoch was 33% slower (concurrent load).
Audit: `docs/reviews/AUDIT_2026-11-21_phase3_claude_resume.md` (PASS WITH FIXES).
A request to stop the Codex-owned controller at a candidate boundary was blocked by
tool permissions; it keeps running and must not be closed with the Codex app.

Phase 4 plan (implemented now, while tuning runs; exercised only on synthetic
fixtures outside `results/`, never on real test predictions): `src/analysis/`
modules to collect run records with hash checks, generate the main/cost/ablation
tables with mean ± SD and class-stratified paired bootstrap CIs, compute every
planned contrast and the H1–H3 clause verdicts exactly as frozen, draw the learning
curve, cost–performance, reliability and ablation figures, run the external error
typology (BIRADS, Verification, Diagnosis, resolution, luminance, contrast), error
overlap, deterministic failure selection, attention rollout/Grad-CAM, and emit
`paper/numbers.json`. Risks: a verdict-code bug silently flipping a hypothesis
(mitigate with unit tests built from hand-computable contrasts); analysis choices
the protocol leaves open being made after seeing results (mitigate by recording
them as a pre-result clarification now); my own CPU use slowing capped runs (keep
tests short and infrequent).

### 2026-11-21 11:20 — Claude Code checkpoint

Done this session (all exercised only on synthetic fixtures or development data;
no real test prediction exists): `src/analysis/` (tables, contrasts, H1–H3 verdicts,
figures, error typology, gallery, rollout/Grad-CAM), `scripts/run_analysis.py`
(`make analysis`), `scripts/spot_check_tables.py` (Phase 4 gate), 8 new tests (39
total pass); article draft (intro, related work, methods, limitations) with every
number a generated placeholder; `paper/build.py` (pandoc + IEEE CSL + generated
two-column template → DOCX → Word PDF → page PNGs, D014); `scripts/audit_numbers.py`
(0 orphans apart from the draft abstract placeholder); `slides/build_slides.py`
(15 editable slides, notes, presenter split). D013 fixes analysis-presentation
choices before results.

Tuning status: LP 5/5, PFT 6/6, LoRA 2/6 (candidate 2 running), CNN 0/6. Validation
AUC so far: LoRA lr=1e-4 wd=.01 0.5507, wd=.05 0.5565 (both capped while still rising).

Open problems: (1) the laptop runs on battery (44%, Balanced plan, ~1.5 GHz), which slows
capped runs and risks killing them; it needs AC power and a fixed plan. (2) The tuning
controller is still owned by the Codex app, which must stay open until it exits.
(3) My own builds slowed epochs; avoid heavy work while a capped run is active.

Exact next step: when `scripts/status.py` shows LoRA 6/6 and CNN 6/6 with selections saved,
run `scripts/archive_run_evidence.py`, commit configs/frozen + results/tuning + run_evidence,
then launch `.venv/Scripts/python.exe scripts/run_experiments.py --phase main` (supervised,
estimated 7–8 h), then `--phase ablation` (~6–7 h), then `make analysis`, the spot check,
Results/Discussion writing, `paper/build.py --final`, `audit_numbers.py`, and slides.

### 2026-11-21 19:36 — Claude Code — tuning closed, main grid launched (user-authorized unattended)

Tuning finished at 13:01 (Codex-owned controller exited normally): 23/23 candidates PASS,
no interrupted attempts. Independent recomputation reproduces every saved selection:
LP C=100 (val AUC 0.897); PFT, LoRA and CNN all lr=1e-3, wd=0.01 (0.837 / 0.874 / 0.719).
LoRA candidates 4 and 5 tie within 1e-12; the first listed is kept. LoRA candidate 4 was
capped at 43 epochs on battery power, whereas candidate 5 completed 50 epochs on AC.
Selections, ledgers and worker evidence committed (85ea849).

The user explicitly authorized running the remaining work unattended. Detached launcher
`scripts/run_grid.py` (PID 7244) runs `--phase main` then `--phase ablation` with bounded
retries; logs in `logs/grid_controller.log`, `logs/main_controller.log`,
`logs/ablation_controller.log`, power samples in `logs/power_log.csv` (AC throughout so
far; AC sleep/hibernate = never). At 20:08 UTC: 10/36 main results (all 9 LP, PFT 1% s0),
with hashes, thresholds and image counts (74 internal / 252 external) checked; the
checkpoint-based PFT evaluation path works. No result has been interpreted yet.

Exact next step: when `logs/grid_controller.log` shows `DONE` (estimated main ~03:30 UTC,
ablations ~10:00 UTC on 22 November), run `scripts/audit_experiments.py`, commit results/,
then `scripts/run_analysis.py`, `scripts/spot_check_tables.py --seed <recorded>`, inspect
sanity flags, and write Results/Discussion. If it shows `STOP`, read the phase controller
log; an interrupted evaluation (evaluation_started.json without evaluation.json) fails
closed and needs a logged manual decision, never a silent re-evaluation.

### 2026-11-21 22:00 — Claude Code — status check of the unattended main grid

At 21:55 UTC: 20/36 main results, all status PASS (LP 9/9, PFT 9/9, LoRA 1% s0–s1);
LoRA 1% s2 training; launcher processes 12464/7244 alive; AC power throughout.
One cap hit so far: `main_PFT_100_s2` stopped at the 1,440 s cap after 18 epochs with
its best validation AUC at the last epoch (still improving). Its median epoch took 79.7 s
versus 70.5 s (s0) and 68.8 s (s1). System CPU in its window (median 57.3%, max 66.5%)
matches s0/s1 (56.8% / 56.4%), so the recorded load does not explain the slowdown. The
`cpu_mhz` column of `logs/power_log.csv` reads a constant 1600 (the nominal clock Windows
reports), so it cannot detect thermal or turbo throttling. This is a timing-variance
observation for the threats-to-validity text, not a deviation: the run is final as logged
and will not be rerun (rerunning because of an outcome would be selection).

Exact next step: unchanged from the 19:36 entry.

### 2026-11-22 (committed by 10:47 UTC) — Claude Code — grid complete, Phase 4 audit and analysis

Grid `DONE` at 04:54 UTC (main 36/36, ablation 21/21, all first attempts, AC throughout).
Main and new ablation audits PASS; 10 sanity flags investigated (low-label CNN below
chance is genuine: checkpoint fidelity 9/9 exact on validation). Results committed
(3a52c61, 790aa8c). `scripts/run_analysis.py` produced tables, figures and verdicts:
H1 inconclusive, H2 inconclusive, H3 supported, H3-external inconclusive. Spot check
(seed 20261122) 3/3. Figure layout fixes only. Full record:
docs/reviews/AUDIT_2026-11-22_phase4_results.md.

User instructions (2026-11-22): (1) do not start the final paper until the user approves;
(2) the user will provide a GitHub repository URL; commits must be attributed to the team's
GitHub accounts (mustapha005, toubani12, Aya Agrigah's account to be confirmed) and never
list an AI assistant as collaborator or co-author. Existing history is not rewritten.

Exact next step: Phase 7 checks that do not touch the article — `scripts/rerun_cell.py`
(main_LP_010_s1, ±0.005), fresh-clone `make smoke`, draft FINAL_CHECKLIST.md; then wait for
the user's go-ahead on the article (Results/Discussion/abstract, `paper/build.py --final`,
`audit_numbers.py`) and slides; push once the repository URL and identities are confirmed.

### 2026-11-22 (committed by 10:59 UTC) — Claude Code — Phase 7 checks that do not depend on the article

`scripts/rerun_cell.py --cell main_LP_010_s1` PASS (difference 0.0); new `--cold` mode
re-extracts LP features from the images: bit-identical arrays, test AUC difference 0.0.
Fresh local clone (b8d64c1) with only the archives and weights copied in: data rebuild
byte-identical to the committed manifests and reports, 39 tests OK, smoke PASS
(docs/reviews/fresh_clone_2026-11-22.md). Draft docs/FINAL_CHECKLIST.md: items 2–8, 10,
12, 15, 17 pass; 1, 9, 13, 14, 16 wait for the article/slides; 11 (dataset and library
licenses in the article) is open.

Exact next step: wait for the user's approval to start the article. Then write Results,
Discussion, Conclusion and the abstract from `paper/numbers.json` and `tables/` (state
the observations in the Phase 4 audit: H3 driven by the scratch CNN failing at <=33
images, LoRA 100% capped 3/3, ablation tuning advantage, rollout not informative), add
the license sentences (item 11), run `paper/build.py --final` and `audit_numbers.py`,
finish slides and QA_PREP answers 17–25, run `scripts/package.py`, and complete
FINAL_CHECKLIST.md with rubric estimates. Push when the user sends the repository URL and
confirms each member's GitHub identity. D013 still awaits user review.

### 2026-11-22 15:20 — Claude Code — public release preparation and record corrections

The user supplied https://github.com/mustapha005/Projet-de-fin-de-module-IA-avanc-e
(public, empty) and Aya's account (Agrigah) and asked for a push. The history scan found
no secrets, personal email, weights or archives, but two files from b2b8332 fall outside
the DATA_CARD release policy: the failure gallery (patient image pixels) and the per-image
clinical-property table. Branch `main` therefore starts at the unchanged 790aa8c and adds
the later work without them. Local `master` (058deaa) is unchanged and is not pushed.
Commits b2b8332, b8d64c1, 73c8862 and 058deaa cited in these records are local only;
their content is in the first `main` commit after 790aa8c.

Corrections to earlier records:
* The two preceding headings carried estimated times (10:20–11:40, 11:55); they now give
  the Git commit times.
* "Byte-identical" data rebuild: Git showed no change after line-ending normalisation;
  only busi_splits.csv was hash-compared directly. Network use was not monitored.
* "Low-label CNN failure is genuine": the checks found no fault, but exclude only
  save/reload and validation-inference faults.
* LoRA 100%: capped 3/3, but the best epochs precede the last one.
* Test access: two reproducibility re-evaluations and the gallery saliency are exceptions.
* Checklist: item 3 has exceptions and item 5 fails (strata table without SD). Passing:
  2, 4, 6, 7, 8, 10, 12, 15, 17. Failing: 5, 11.
* The frozen tag does not independently prove timing: commit times are local and the
  first push came after the results.

No teammate authorship was assigned: who contributed which work has not been stated.
The article was not edited.

Exact next step: wait for the user's approval to start the article, their review of D013,
their decision on the two withheld files, and a statement of each member's contribution.

### 2026-11-22 15:27 — Claude Code — first push verified

Pushed main (0f30b5d, 23 commits) and protocol-frozen (befa5ba) without force. A fresh
unauthenticated clone from GitHub has the same hashes, 36 main and 21 ablation results,
21/21 protected hashes matching and 39 tests OK. The withheld files have no history there.

Future work happens on main. Local master must not be pushed while the two files are withheld.
Exact next step: unchanged from the previous entry.
