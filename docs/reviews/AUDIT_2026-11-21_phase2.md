# Audit — 2026-11-21 — Codex — phase 2 — implementation 917c094

## Verdict

PASS WITH FIXES — measured the workload, verified all four model paths, fixed
Windows process supervision and portable hashes, and passed development smoke.
The protocol may now be tagged before any tuning or main result is generated.

## Blocking issues resolved

| Issue | Evidence | Rubric criterion | Fix |
|---|---|---|---|
| Parent monitored Windows venv launcher, underreporting RAM and risking incomplete termination | Superseded smoke reported ~4 MiB; benchmark's in-worker measurements were plausible | Compute rigor / reproducibility | Track full process tree, aggregate CPU and RSS; terminate descendants; revised smoke and actual deadline interruption pass |
| CRLF working files differed from Git's LF blobs | Line-ending migration audit and old manifest hashes | Reproducibility | D012: explicit LF writers, equal parsed content, regenerated hashes; clean clone matches all protected bytes |
| Hard termination could omit run metadata | Deadline-path code review | Reporting / rigor | Persist static metadata and recover it with the last valid checkpoint; real 11-second capped CNN test passes |

## Non-blocking issues

| Issue | Evidence | Treatment |
|---|---|---|
| Runtime projection depends on sustained laptop throughput | One measured pass per cell, not a 26-hour thermal stress test | Include 20% headroom; log actual cap hits and consumed work |
| LP has finite cached view exposure and different solver iterations | D009 and protocol | Same transformation distribution, first four views matched; cold-cost debit and explicit disclosure |
| Small image-level internal test and no reliable patient IDs | Phase 0 data card | Preserve limitations and conservative hypothesis logic |
| Full fresh-environment scientific reproduction not yet done | No main result exists | Phase 7 gate remains open; clean-checkout audit here verifies bytes/preparation only |

## Checks passed

- `scripts/benchmark_cpu.py`: 12 timing-only train/validation cells, no test scores.
  PFT/LoRA/CNN full-data epoch time 83.07/139.38/53.78 seconds; LP cold full-data
  setup/fit/validation approximately 265 seconds. Peak measured RAM 3.37 GiB.
- Parameter counts: LP 769; PFT 3,552,770; LoRA 222,722; CNN 11,177,538 trainable.
  Partial-forward equivalence, frozen-prefix gradients, exact LoRA target layers
  and zero-initialized adapter equivalence pass meaningful architecture tests.
- Projection: T_MAX 1,440 seconds, four CPU threads, 50 epochs, all 80 specified
  fits (23 tuning + 36 main + 21 ablations), 25.96 elapsed CPU hours with headroom.
  No prescribed fallback needed. Detailed assumptions are in compute_projection.json.
- Final pre-freeze suite: 31 tests pass (0.642 s test execution, excluding imports).
- Corrected full development smoke: 255.88 seconds; all checkpoints replay,
  cache reuse is debited, impossible deadline rejected, real-test access blocked,
  synthetic paired bootstrap checked, manifests unchanged, actual worker monitored.
- Separate capped CNN: selected epoch 1 at 8.18 seconds, deadline 11 seconds,
  supervisor detection overshoot 0.078 seconds; checkpoint and metadata retained.
- Clean local Git clone of 917c094: all 21 protected SHA-256s match, and its
  development preparation reproduces the same 414-row manifest byte for byte.
- Both data overlap audits still pass; bibliography ledger still has 24 verified
  identities, 15 from 2024–2026. `git diff --check` passes.
- Results directory is empty at this audit; no scientific test prediction exists.

Benchmark timing code predates LF serialization and supervision fixes. Numerical
model and transform code is unchanged; the fixes affect bookkeeping/termination,
not the measured forward/backward paths. Benchmark resource measurements were
taken inside workers and were never the defective parent-launcher measurements.
