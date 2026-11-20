# Audit — 2026-11-20 — Codex — phase 0 — base ac55334

## Verdict

PASS WITH FIXES — acquired both datasets, repaired leakage missed by pHash,
and reproduced the final manifests byte for byte before any training.

## Blocking issues

| Issue | Evidence | Rubric criterion | Fix applied |
|---|---|---|---|
| pHash alone missed published duplicate relationships | Archived `phash_only/published_duplicate_audit.json`: 20 direct pairs crossed the provisional splits | Protocol / rigor | D007: union published links with pHash, quarantine normal/binary conflicts; current independent audit PASS |
| Interrupted package and image transfers | Historical acquisition failures; successful checksums now in `data/provenance.json` | Reproducibility | Resume-safe downloads, complete pinned local environment, archive CRC and original-image checks |

No unresolved blocking data issue remains. This gate does not authorize freezing
the experiment without the literature, protocol, benchmark and smoke gates.

## Non-blocking issues

| Issue | Evidence | Treatment |
|---|---|---|
| Patient independence cannot be established | BUSI public files lack patient IDs | Report image-level inference and residual leakage risk |
| BUSI original host blocked by HTML challenge | `docs/source_probe.json`, D006 | Verified public mirror; retain attribution and do not redistribute images |
| BrEaST is a pooled cohort with mixed verification | Descriptor and actual metadata; `docs/DATA_CARD.md` | Do not claim a causal single-center effect or universal histology confirmation |
| Nominal 1% is larger after the class floor | `data/split_report.json`: 8/341 | Report actual 2.346% alongside nominal label |

## Checks passed

- Full acquisition from initially absent archives succeeded; source URLs, archive
  hashes and errors are retained in `data/provenance.json`.
- Repeated offline `scripts/data_pipeline.py` rechecked original image SHA-256s,
  reran inventories, deduplication, splits and nesting, and reproduced all five
  manifest SHA-256s. Evidence: `phase0_manifest_reproduction.json`.
- Final BUSI: 647 binary images before cleaning; 488 retained; 159 removed,
  including 17 quarantined for ambiguous labels. Splits 341/73/74.
- BrEaST: 252 binary cases, 154 benign / 98 malignant; four normals excluded.
- Zero pHash split crossings, exact/near cross-cohort matches, retained published
  duplicate groups or known normal/binary conflicts.
- Seeds 0/1/2 each have nested 8/33/341 training subsets; full validation retained.
- Sixteen unittest cases pass in the pinned `.venv`; package dependency check passes.
- `requirements.lock` contains 51 distributions. DINOv2 local revision and
  safetensors checksum are pinned in `configs/backbone.json`; no remote code used.
- AGENTS.md and CLAUDE.md are byte-identical. `results/` is empty, with no frozen
  tag and no test predictions. `git diff --check` passes.

Scientific performance and hypotheses remain untested.
