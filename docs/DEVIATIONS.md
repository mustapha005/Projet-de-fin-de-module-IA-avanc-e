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
