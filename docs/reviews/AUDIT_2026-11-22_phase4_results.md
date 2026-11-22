# Phase 4 audit — main grid, ablations and analysis (2026-11-22, Claude Code)

**Verdict: PASS.** All 57 pre-registered final cells are complete, audited and analysed
reproducibly. Ten sanity flags were investigated: none is an implementation fault. The
observations below must be carried into the article's results and threats to validity.

## Evidence (commands actually run)

| Check | Command / source | Outcome |
|---|---|---|
| Grid finished | `logs/grid_controller.log` | main exit 0 at 01:06:54 UTC; ablation exit 0; `DONE` 04:54:11 UTC |
| Power state | `logs/power_log.csv` | 0 unplugged samples over the whole grid |
| Main audit | `scripts/audit_experiments.py --phase main` | PASS, 36/36; metrics recomputed from hashed predictions; paired identities; 8 flags |
| Ablation audit | `scripts/audit_experiments.py --phase ablation` (new) | PASS, 21/21; identities equal the main grid; 2 flags |
| Attempts | `data/cache/runs/*/attempt_*` | every final cell finished in attempt 1; no `evaluation_started.json` without `evaluation.json` |
| Evidence archive | `scripts/archive_run_evidence.py` | 80 attempts (23 tuning, unchanged; 57 final, new) |
| Checkpoint fidelity | `scripts/check_checkpoint_fidelity.py` (new) | 9/9 reloaded checkpoints reproduce logged validation probabilities exactly (max diff 0.0) |
| Unit tests | `python -m unittest discover -s tests` | 39 OK |
| Analysis | `scripts/run_analysis.py` | exit 0; tables, figures, `paper/numbers.json`, verdicts |
| Table spot check | `scripts/spot_check_tables.py --seed 20261122 --cells 3` | 3/3 match (CNN 1% internal 0.411 ± 0.067; LoRA 100% internal 0.958 ± 0.014; PFT 1% external 0.550 ± 0.131) |
| Rollout diagnostic | `scripts/check_rollout_similarity.py` (new) | `docs/reviews/rollout_similarity.json` |

Results were committed in 3a52c61; the audit extension and fidelity check in 790aa8c.

## Pre-registered verdicts (tables/hypotheses.md)

H1 inconclusive (LoRA > LP at 100% supported; LP vs LoRA at 1% not detectable).
H2 inconclusive (no gap contrast detectable; ranking clause inconclusive).
H3 supported (internal, all six FM-vs-CNN contrasts at 1% and 10%).
H3 external (secondary) inconclusive.

## Sanity-flag investigation

* **CNN 1%/10% internal AUC below 0.5 and external > internal (6 flags).** Validation
  AUCs at selection were 0.54–0.73. The selected checkpoints, reloaded through the final
  evaluation loader, reproduce the logged validation probabilities exactly; CNN 100% seed 0
  reaches validation AUC 0.876 and the CNN 100% cell internal test 0.897 ± 0.019. Save/reload, eval mode and
  preprocessing are therefore consistent; the low-label CNN failure is a genuine result
  (random-initialised ResNet-18 trained on 8–33 images, selected on a 73-image validation
  set). Two CNN runs produce near-constant probabilities (SD < 0.001). Interpretation of
  H3 must say that it is driven by the scratch CNN not learning at ≤33 images.
* **Near-chance external AUC for LP 1% s2, LoRA 1% s0, LoRA-last2 1% s0, LoRA-rank4 10% s1
  (4 flags).** Fit evidence is normal (non-degenerate probabilities, normal epochs); they
  fall within the seed spread of 1%/10% cells. No action.

No result was deleted, re-run or re-evaluated.

## Observations for the article

1. **Cap hits: 5/36 main, 0/21 ablation.** LoRA 100% 3/3 (12 epochs each), PFT 100% s2
   (best epoch = last epoch, still improving), CNN 100% 1/3. LoRA 100% is therefore
   budget-limited, which matters for any LoRA-vs-PFT conclusion at 100%.
2. **Timing variance.** PFT 100% s2 epochs took a median of 79.7 s versus 70.5/68.8 s for
   s0/s1 with matching recorded load; `cpu_mhz` in the power log is a constant nominal value
   and cannot reveal throttling (LOG 2026-11-21 22:00).
3. **Ablation comparisons favour the main configuration by design.** The LoRA/PFT
   hyperparameters were tuned for the main configuration at 10%, seed 0, and the main
   10% seed-0 run reproduces that tuning run (validation AUC 0.874). Ablations reuse those
   settings untuned. The rank ablation also changes alpha/r (pre-registered disclosure,
   PROTOCOL.md "Ablations and error analysis").
4. **Attention rollout is not informative about adaptation.** On 10 validation images,
   rollout maps of LP/PFT/LoRA correlate at 0.992–0.99998 while last-layer CLS attention
   correlates at −0.08 to 0.82; the gallery's DINOv2 maps are dominated by the shared early
   layers and isolated background tokens. The gallery caption must say so; no claim may
   rest on those maps.
5. Ablation contrasts use the pre-registered rule; some large external differences (e.g.
   LoRA-last2 1%, −0.071) are "not detectable" because they do not exceed the seed SD.

## Figure QA (presentation only; no data or statistic changed)

Inspected all six figures at full resolution. Fixed: colliding "100%" point labels in the
cost plot (replaced by one ordering note), the reliability legend covering data and the
overlapping row labels (figure-level key, shared y-label), and the clipped x-label of the
error-overlap plot.

## Open items

* D013 (analysis presentation) remains flagged for user review.
* Article writing is on hold at the user's request (2026-11-22) until they approve.
* Phase 7: fresh-clone smoke test, `scripts/rerun_cell.py`, packaging, final checklist.
