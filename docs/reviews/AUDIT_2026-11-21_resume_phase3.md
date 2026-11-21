# Audit — 2026-11-21 continuation — Codex — latest completed phase 2

## Verdict

PASS for the completed Phase 2 gates; Phase 3 remains INCOMPLETE. Preserve and
restart one interrupted tuning attempt using the existing frozen rule.

## Blocking issues

No design-change request is required. The incomplete LoRA attempt cannot be
accepted as a completed tuning candidate or resumed with accumulated optimizer
steps. It will restart from initialization as attempt 2 under the same cap.

## Checks performed

- Read README, LOG, PROTOCOL, DEVIATIONS and Git history; protocol-frozen resolves
  to befa5ba, before all scientific records.
- `verify_frozen()` checks all 21 protected file hashes, installed versions and
  reference hardware: PASS. No protected source or design input changed.
- Current Phase 2 evidence retains 12 timing cells, corrected smoke PASS at
  255.88 seconds and successful capped-checkpoint recovery. No rerun of unchanged
  CPU measurements was needed.
- Completed tuning ledgers: LP 5/5, PFT 6/6. Selection recomputation confirms
  LP C=100 and PFT lr=0.001, weight_decay=0.01, using the stated tie rule.
- No matching Python experiment process is live. LoRA attempt 1 stopped after
  42 logged epochs, without fit.json or supervised.json. The cause is unknown.
  Its completed-epoch timing supplies only a lower bound of 1084.43 seconds;
  total CPU/RAM/termination time cannot be reconstructed and is not fabricated.
- Archived 11 complete worker records with histories/logs and a separate
  interrupted-attempt record. No model weights or source images are included.
- Main grid 0/36; ablations 0/21; no real test predictions. H1–H3 are untested.

Continue LoRA and CNN tuning under supervision. Inspect failures and preserve
attempts; do not change frozen hyperparameters, stopping or statistical rules.
