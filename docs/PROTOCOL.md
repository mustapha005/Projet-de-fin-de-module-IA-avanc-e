# SAN-1 experimental protocol — draft, not frozen

Status: setup/data phase. No main-run result exists. No protocol-frozen tag.
The complete protocol will be committed in Phase 1 and the CPU cap added in
Phase 2 before the frozen tag. Unresolved fields must not be guessed.

## Research question

On CPU, at an equal per-run compute cap, does the ranking of linear probing,
partial fine-tuning, and LoRA for a self-supervised ViT on breast-ultrasound
lesion classification depend on the label fraction (1 / 10 / 100%), and is
that ranking preserved on an unseen acquisition center?

## Hypotheses supplied before results

- H1: LP is not worse than LoRA at 1% internal AUC; LoRA beats LP at 100%.
- H2: Internal strategy ranking is preserved externally, and the internal minus
  external AUC gap does not grow with trainable parameter count.
- H3: All three foundation-model strategies beat the scratch CNN at 1% and 10%.

A detectable difference requires absolute mean difference greater than the
larger sample standard deviation over three seeds AND a 95% paired-bootstrap
confidence interval excluding zero. Otherwise report no detectable difference.
Hypothesis verdicts will be supported/rejected/inconclusive with explicit clause
logic. Noninferiority and compound-H2 ambiguities are open before freeze.

## Phase 0 data rules

- Benign=0, malignant=1; drop normal and mask files in both cohorts.
- Audit all image files and record SHA-256, pHash (8x8), dimensions, source.
- BUSI pHash Hamming distance <=4 defines an undirected near-duplicate graph.
  Connected components are formed before splitting; keep the lexicographically
  first path in each single-label component. Quarantine entire conflicting-label
  components. No outcome/model metric influences this rule.
- Split retained BUSI images stratified 70/15/15 with seed 1234. First reserve
  30%; split it equally into validation/test, both with seed 1234.
- For each seed 0/1/2, shuffle each training class once; take prefixes for nested
  1%, 10%, 100% subsets. Per-class count is max(4, floor(n_class*fraction)) for
  1%, max(4, floor(n_class*fraction)) for 10%, and all images for 100%. The same
  minimum at 10% preserves nesting if the training set is extremely small.
  Record actual fractions; validation remains full at all fractions.
- External records are inventoried for eligibility/leakage only; no predictions
  or outcome-guided selection. Cross-cohort near-duplicates must be flagged and
  resolved before freezing rather than silently removed from the test set.
- Image-level independence only: missing BUSI patient IDs mean pHash cannot
  establish patient independence. This remains a threat to validity.

## Pending Phase 1/2 fields

Full preprocessing/augmentation and LP view policy; architecture/module targets;
model revision; hyperparameter-selection/tie rules; metric/CI implementation;
threshold selection; cap accounting and abort/resume behavior; reference-machine
fingerprint/thread count; T_MAX; ablation budgets; test-access audit; results schema.
