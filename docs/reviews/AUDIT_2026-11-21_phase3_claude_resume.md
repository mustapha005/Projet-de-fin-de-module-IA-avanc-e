# Audit — 2026-11-21 — Claude Code (Opus 5.5) — phase 2 gate re-check + phase 3 progress — commit 0c90118

## Verdict

PASS WITH FIXES — the Phase 2 exit gate re-verifies with real commands, and Phase 3
tuning is valid but incomplete (LoRA 1/6, CNN 0/6). The fixes are operational: commit the pending
Codex bookkeeping changes and record a measured concurrent-load timing threat. No design change is
requested.

## Blocking issues

None. No integrity fault or rubric-point risk was found that requires stopping.

## Non-blocking issues

| # | Issue | Evidence | Fix |
|---|---|---|---|
| 1 | Concurrent machine load changes epochs reached under the wall-clock cap. | LoRA tuning candidate 0, identical config: attempt 1 median epoch 26.17 s (42 epochs in 1084.4 s); attempt 2 median 34.92 s, max 91.01 s, capped at 35 epochs. A 5 s process sample showed OneDrive.Sync.Service ≈ 0.5 core while training used ≈ 4 cores. | Record as a threat to validity; report `epochs_completed` and per-epoch seconds for every run; keep agent work light during runs; recommend pausing OneDrive sync while runs execute. No protocol change. |
| 2 | Running tuning controller (PID 22228 tree) is owned by the Codex app's shell (codex.exe PID 18568). Attempt 1 of the same cell died at 03:14 when the Codex app's session ended (Codex processes restarted at 03:23). | `Get-CimInstance Win32_Process` parent chain: 12484 → 2680 → 21068 → 22228 → pwsh 21612 → codex.exe 18568. | Do not close the Codex app until the tuning controller exits, or let the user approve a hand-over at a candidate boundary. Interruptions remain archived, never resumed with extra budget. |
| 3 | Uncommitted Codex changes (`scripts/status.py`, `scripts/doctor.py`, `docs/machine.json`, `docs/reviews/lora_restart_prefix.json`). | `git status` / `git diff` at session start. None of the four is in `protected_sha256`. | Reviewed and committed with this audit. |

| 4 | The reference laptop is running on battery (Win32_Battery status 1 = discharging, 44% at 11:19) with the Balanced power plan; CPU clock sampled at 1500 MHz under 85% load. Battery operation plausibly explains the slower epochs, and a depleted battery would kill the run in progress. | `Get-CimInstance Win32_Battery`, `powercfg /getactivescheme`, `Win32_Processor.CurrentClockSpeed`. LoRA candidate 2 median epoch 44.0 s vs 26.2 s overnight. | User action: keep the laptop on AC power with a fixed power plan for every remaining run. Record per-run epoch timings; no protocol change. |

## Checks passed

- Frozen contract — `verify_frozen()` → PASS: 21 protected SHA-256s, pinned package versions,
  reference hardware; cap 1440 s, 4 threads, seeds [0, 1, 2], fractions [0.01, 0.1, 1.0].
- Tag ordering — `protocol-frozen` → befa5ba (2026-11-21T02:23:12Z). The first commit adding
  `results/` is f0df013 (02:30:14Z). The worker processes the controller launched validate the tag again.
- Test suite — `python -m unittest discover -s tests` → 31 tests OK (2.84 s).
- Held-out access — grep for `busi_splits` / `breast_external` / `split == 'test'` in `src/` and
  `scripts/`: model-evaluation access only in `src/evaluate.py:77-79` (`final_evaluation`, which refuses
  purpose `tune`); the other hits are data preparation and leakage audits, the protocol's stated exception.
- No real test predictions exist — `find` for `*_predictions.csv`, `evaluation_started.json`,
  `evaluation.json` returns nothing; `results/predictions/` does not exist.
- Tuning ledgers — LP 5/5, selected C=100 (val AUC 0.8969); PFT 6/6, selected lr=1e-3,
  wd=0.01 (0.8372). Weight-decay pairs give distinct validation probabilities but equal AUC ranks;
  the first-listed tie rule was applied as frozen.
- LoRA candidate 0 — attempt 2 status PASS, supervisor-killed at cap with 0.06 s detection
  overshoot, 35 epochs, best epoch 35, val AUC 0.5507, 222,722 trainable / 22,279,298 total params,
  peak RSS 3.63 GB.
- Determinism — attempt 1 and attempt 2 of LoRA candidate 0 have identical validation AUCs
  (|Δ| < 1e-12) for all 35 shared epochs. Only wall-clock timing differed.
- Code review (no change needed) — `Dinov2Layer.forward` in transformers 4.49.0 returns a tuple,
  so PFT's `layer(hidden)[0]` selects the hidden state, not the first batch item. ECE, stratified
  paired bootstrap (mean over seeds per draw), validation-only threshold, and development-only
  loaders match `docs/PROTOCOL.md`.

## Tooling gap noted for later phases

`pandoc` and LibreOffice are not installed on the reference laptop (`which pandoc soffice` →
not found). The Phase 5 build needs a decision on how to obtain them; Phase 3/4 do not.
