# Audit — 2026-11-20 — Codex — phase 1 — base 63c94a6

## Verdict

PASS WITH CLARIFICATIONS — positioning and the full pre-experiment specification
are written; the only experiment-freeze fields pending are measured Phase 2
compute/hardware settings and any prescribed budget fallbacks.

## Blocking issues

None remaining for Phase 1. No protocol-frozen tag is authorized yet.

## Non-blocking issues

| Issue | Evidence | Treatment |
|---|---|---|
| H1 noninferiority and H2 clause ambiguity | Supplied master prompt; verified Lakens reference | D010: explicit conservative decisions; nondetection is inconclusive |
| Cached LP cannot have unlimited fresh augmentation | LP definition versus neural training | D009: four deterministic views, common distribution, disclosed exposure difference and cold-cost debit |
| DINOv2 implementation has split projections | Installed Transformers model inspection, PEFT 0.14 documentation | D008: exact query/key/value targets and logged trainable counts |
| Some references only have abstract access | `reference_verification.json` | Limit claims to accessible evidence; no invented full-text appraisal |
| Formal TCIA dataset citation still needed in final bibliography | Descriptor and dataset DOI recorded in DATA_CARD | Add the dataset entry at article assembly; preserve verified source identity and required attribution |

## Checks passed

- `scripts/audit_references.py`: 24 unique bibliography entries match 24 verified
  ledger keys; 15 publication years in 2024–2026. Source identities/access limits
  were checked in the three research ledgers; root additionally opened ResNet.
- Research question and positioning cover LP/PFT/LoRA, label scarcity, medical
  FM context, ultrasound, external shift, calibration and existing closest work.
- Protocol specifies data, all methods, search, thresholds, metrics, bootstrap,
  hypothesis clause logic, costs, failures, ablations and error analysis.
- `configs/search.json` contains the supplied five/six/six/six candidates.
- Eleven primary libraries have installed-version license files and hashes.
- Root read the full synthesis and reconciled its project status with Phase 0.
- `results/` remains empty; neither main nor tuning test predictions exist.

Phase 2 must test implementation against these rules, measure runtime and RAM,
and pass smoke before filling T_MAX and creating the frozen tag.
