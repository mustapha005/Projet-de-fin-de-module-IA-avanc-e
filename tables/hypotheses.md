| Hypothesis | Clause | Verdict |
|---|---|---|
| H1 | LP_not_worse_than_LoRA_at_1pct | inconclusive |
| H1 | LoRA_beats_LP_at_100pct | supported |
| H1 | **compound** | **inconclusive** |
| H2 | ranking_preserved_externally | inconclusive |
| H2 | gap_does_not_grow_with_trainable_parameters | inconclusive |
| H2 | **compound** | **inconclusive** |
| H3 | six internal FM-vs-CNN contrasts | **supported** |
| H3 (secondary) | six external FM-vs-CNN contrasts | inconclusive |

Detectable only if |mean difference| exceeds the larger per-seed SD and the 95% class-stratified paired bootstrap CI excludes 0 in the same direction. Compound: any rejected clause rejects; all supported supports; else inconclusive.
