# Deviations and clarifications

All entries are made before main experiments. No frozen protocol exists yet.

| ID | Date | Change / clarification | Reason and impact |
|---|---|---|---|
| D001 | 2026-11-20 | Exclude BrEaST normal images too | Primary descriptor reports four normals. Preserves the intended benign/malignant task; final counts come from metadata. |
| D002 | 2026-11-20 | Quarantine mixed-label pHash components | A deterministic choice of one conflicting label is not defensible. Log all such components before splitting. |
| D003 | 2026-11-20 | Include native Python command equivalents | GNU Make is absent on the Windows host. Make targets are retained for portable reproduction. |
| D004 | 2026-11-20 | Repository lives directly in AIfinale | This is the user-selected empty workspace. Artifact prefix remains SDIA2026_SAN-1_GROUP_13. |
| D005 | 2026-11-20 | 1% floor is four images per class | Pre-authorized in the master prompt. Record actual rather than nominal percentage. |
| D006 | 2026-11-20 | Public BUSI Kaggle mirror used as acquisition fallback | University page/archive return an HTML challenge. Mirror version and stated CC0 license checked via public API; retain original attribution and do not redistribute images. This changes the source transport, not the planned cohort. |
| D007 | 2026-11-20 | Combine pHash with the published BUSI duplicate graph; quarantine binary/normal conflicts | Independent audit of the pHash-only provisional split found 20 published duplicate pairs crossing splits and two retained images with normal-class duplicates. Correct before freeze and before any training. Preserve the failed provisional audit in docs/reviews/phash_only/. The published table is CC BY 4.0 and attributed in the versioned configuration. |
| D008 | 2026-11-20 | LoRA targets separate query/key/value projections | Installed Transformers DINOv2 uses three linear modules, not fused qkv. Rank applies separately to each; actual parameters are reported. No extra projections or biases are trained. |
| D009 | 2026-11-20 | LP uses four cached augmented views per image | Reconciles the requested cache with the common augmentation distribution. Neural epochs 0–3 match these seeded views; later epochs draw more. Charge cold feature cost even on cache hits; disclose unequal realized view exposure. |
| D010 | 2026-11-20 | Conservative compound-hypothesis decisions | No supplied noninferiority margin permits treating nonsignificance as “not worse.” Support requires sufficient directional evidence, rejection requires detectable contradiction; otherwise inconclusive. H2 clauses and H3 internal primary endpoint are explicit before results. |
| D011 | 2026-11-20 | Use development/synthetic data for smoke evaluation | An end-to-end smoke test must not expose real internal/external test performance before final selection. Store smoke artifacts outside results/. |
| D012 | 2026-11-21 | Canonical LF serialization before freeze | Windows text writers produced CRLF while Git stores LF, invalidating byte hashes after checkout. Explicit LF writers and a one-time normalization preserve parsed rows/JSON values; regenerate current provenance hashes and verify a clean checkout. Historical CRLF manifest hashes remain in the Phase 0 audit as superseded evidence. |
