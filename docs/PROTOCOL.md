# SAN-1 experimental protocol — draft, not frozen

Status: Phase 1 specification; no main-run result or protocol-frozen tag exists.
Data preparation passed. The measured CPU cap and reference thread count must
be added in Phase 2 before the frozen tag. All rules below precede model results.

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
Hypothesis verdicts follow the conservative clause rules below. An absence of
detectable difference never establishes equivalence or noninferiority.

## Phase 0 data rules

- Benign=0, malignant=1; drop normal and mask files in both cohorts.
- Audit all image files and record SHA-256, pHash (8x8), dimensions, source.
- BUSI pHash Hamming distance <=4 and the duplicate pairs in Pawlowska et al.
  (2023), Table B1, define the union of two undirected near-duplicate graphs.
  Source facts and the continuous-ID mapping are versioned in
  `configs/busi_published_pairs.json`. Connected components are formed before
  splitting; keep the lexicographically first ID in each single-label component.
  Quarantine entire conflicting-label components, including binary images linked
  to a normal-class image in the published list. No model metric influences this.
  An independent graph traversal checks the published groups after cleaning,
  including connections through removed intermediate images. See deviation D007.
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

## Preprocessing and views

Read with PIL, convert to luminance then three identical RGB channels. Evaluation
uses bilinear antialiased resize of the shorter side to 224, followed by a 224
center crop; normalize by mean [0.485, 0.456, 0.406], SD [0.229, 0.224, 0.225].
This explicitly overrides the downloaded processor's default resize of 256.
Do not crop using lesion masks, erase overlays or use test-time augmentation.

Training replaces the center crop with RandomResizedCrop(224, scale=[0.8,1.0],
ratio=[0.75,4/3], bilinear antialias), horizontal flip p=0.5, rotation uniformly
within ±10 degrees (bilinear, zero fill), and ColorJitter brightness/contrast=0.1.
Apply in that order before normalization. The same transformation distribution
is used for LP, PFT, LoRA and CNN. Derive a stable seed from (run seed, original
image ID, view index); save/restore the torch RNG around the image transform so
adapter/head randomness and augmentation do not perturb one another.

LP caches four independently drawn training views per original image, indices
0–3, with repeated labels. Neural epoch e uses view index e (zero-based), so its
first four views match LP for the same image and seed. Later neural epochs draw
additional views; this difference is disclosed, not described as identical
augmentation exposure. Validation/test use one deterministic view. Cache keys
include source SHA, transform config, model revision and seed/view. Validation
features are cached separately; never extract test features during training.
The no-augmentation ablation uses evaluation preprocessing for training.

## Models and optimization

Use the local `facebook/dinov2-small` revision in `configs/backbone.json`, FP32,
no remote code, eager attention, no compilation/quantization or mixed precision.
Concatenate final-normalized CLS and mean patch tokens (768 features) for all
three DINOv2 methods. All neural classifiers have two logits and softmax malignant
probability; LP uses its single binary logistic decision and `predict_proba`.

| Method | Trainable components |
|---|---|
| LP | sklearn LogisticRegression, balanced class weights, L2 penalty, lbfgs, tol=1e-4, max_iter=1000, intercept; raw 768 features, no fitted feature scaling |
| PFT | final two transformer blocks, final layer norm, 768→2 head; frozen embeddings and earlier blocks run under no_grad and eval mode |
| LoRA | independent rank-8 adapters on query/key/value in all 12 blocks, alpha=16, dropout=0.1, bias=none, standard initialization; 768→2 head |
| CNN | torchvision ResNet-18 weights=None, all layers trainable, 512→2 head |

The HF implementation has separate query/key/value projections, not one fused
qkv matrix. Apply PEFT to their exact module paths; count actual trainable tensors.
The separate-projection parameterization is recorded in D008. PFT frozen-prefix
outputs are detached each batch; LoRA keeps the gradient path through frozen
layers where required. Do not mistake requires_grad=False for computational cost.

Neural models use AdamW (betas=.9/.999, eps=1e-8), weighted cross-entropy with
weight N/(2*n_class) from the selected training subset, batch=min(32,N), no dropped
last batch, no gradient clipping/accumulation. Shuffle reproducibly each epoch.
One linear warm-up epoch reaches the configured learning rate, then cosine decay
to zero at the epoch limit. Apply weight decay to all trainable parameters.
The maximum is 50 epochs; only the ordered budget fallbacks below can change it
before freeze. Validate after each complete epoch. Strictly higher validation
AUC by more than 1e-12 replaces the checkpoint; ties keep the earlier checkpoint.
Stop after eight consecutive non-improving complete epochs. A batch or validation
pass interrupted by the cap cannot select a new checkpoint. Record such truncation.
LP optimizer iterations are not neural epochs and will not be reported as such.

## Search and threshold selection

Run the entire search only at nominal 10%, seed 0, on training and validation.
Order configurations ascending as listed in `configs/search.json`.
LP: C=[.01,.1,1,10,100]. PFT/LoRA: lr=[1e-4,3e-4,1e-3] × wd=[.01,.05].
CNN: lr=[3e-4,1e-3,3e-3] × wd=[1e-4,1e-2]. Each candidate has the same cap.
Pick greatest best-validation AUC; ties within 1e-12 choose the earlier listed
configuration. No additional candidates, fraction-specific tuning or ablation
retuning. Failed candidates remain logged, never silently replaced. Store selected
configurations and the search ledger in `configs/frozen/` after tuning.

Every final run starts afresh, including seed 0 at 10%; do not reuse a tuning
checkpoint as a main run. Seeds 0/1/2 control initialization, order and subsets.
Set Python, NumPy, torch seeds and deterministic_algorithms(True, warn_only=True);
retain warnings. No claim of universal cross-platform bitwise reproducibility.

For each selected final checkpoint choose the threshold maximizing validation
macro-F1. Candidates are unique validation probabilities, 0, and nextafter(1,+inf);
predict malignant for p>=threshold. Ties choose closest to 0.5, then the smaller
threshold. Freeze it for both tests. Report uncalibrated probabilities; no post-hoc
temperature scaling or externally selected threshold is permitted.

## Compute, deadlines and access controls

One run at a time on the reference laptop; torch intra-op threads provisional 4,
interop 1, loader workers 0; constrain BLAS to the same intra-op thread count.
Hardware/software fingerprint is in `docs/machine.json`; finalize in Phase 2.
Primary budget units are elapsed wall-clock hours on this CPU. Also log process
CPU seconds (summed across threads); never call elapsed hours core-hours.

T_MAX is **unset**. Benchmark seed-0 training and validation only, one full epoch
per method/fraction, with a warm-up step separated from measured steady-state
work. LP additionally measures cold four-view extraction plus one C=1 fit; report
that total instead of inventing LP epochs. Proposed cap is the larger of ten
slowest full-data neural epochs and 1.25× full-data cold LP cost, rounded upward
to a minute. Project tuning (23 fits), main (36), ablations (21), and final
inference using actual method/fraction costs, with 20% runtime headroom.

If projection exceeds 60 elapsed CPU hours, apply in order: 100% neural cap of
30 epochs for all methods; omit no-augmentation then PFT-depth ablations; use
160×160 for CNN everywhere including tuning. Log each change and rebenchmark
affected cells. Keep three seeds and all fractions. Above 100 hours after these
fallbacks, stop for user review. The final cap must fit at least one complete
training/validation pass for each neural method and complete LP feature setup.

Charge model loading, preprocessing, training features, optimizer work,
validation and checkpoint writing to the run's budget. Downloads, Python imports
and final test inference are outside it and separately timed. Reusing LP features
does not create free compute: debit measured cold extraction/loading cost for
that exact cache from T_MAX, even on cache hits; report both charged isolated-run
cost and actual/amortized work. Never debit features outside the selected subset.
Evaluate LP validation once after the fit. A nonconverged LP fit is flagged.

A parent supervisor enforces the deadline and samples process RSS/CPU; workers
check before expensive work and save best checkpoints atomically. Record actual
deadline overshoot (OS scheduling/termination is not instantaneous). Do not keep
updates after the cutoff. If no valid completed checkpoint exists, log failure;
do not substitute an untrained baseline or extend the cap. Successful results
are skipped only after validating configuration, data, weights and prediction
hashes. Incomplete runs restart under the same cap and preserve attempt logs;
they cannot accumulate extra training time across restarts.

Only final evaluation code may open test images or labels after selection. Data
preparation is an explicit prior exception for inventories/eligibility/leakage.
Training interfaces expose only train/validation. Benchmark/smoke use development
data and synthetic held-out fixtures, never real test predictions. Smoke uses
one seed, two epochs and ~2% of training with the four/class floor. Its artifacts
live under `data/cache/smoke/`; benchmark evidence under `docs/benchmark/`.
Keep `results/` empty until `protocol-frozen`. For each final run, lock a test
evaluation transaction, persist predictions once, and derive all later analyses
from those files. Technical interruption recovery is logged and cannot select
models/thresholds based on a partially observed test result.

## Metrics, uncertainty and hypothesis decisions

Primary endpoint: ROC-AUC using malignant probability. Secondary: macro-F1 of
both classes at the fixed threshold, AUC_in−AUC_out, and 15 equal-width-bin binary
top-label ECE: confidence=max(p,1−p), correctness of argmax at 0.5, weighted
absolute bin accuracy/confidence difference. Include endpoints, empty bins
contribute zero. Reliability plots also show malignant probability calibration
against positive frequency, clearly distinguished from top-label ECE.

Report mean and sample SD (ddof=1) across exactly three seeds. No ensemble score
substitutes for the mean per-seed score. Use 2000 class-stratified bootstrap
resamples of original test images/cases, seed 20261120, percentile 2.5/97.5 bounds.
Within each draw, the same sampled IDs pair methods and all seeds; compute the
mean of the three per-seed metrics or differences. Also retain per-seed paired
intervals. Do not pool three predictions per image as independent observations.
This is conditional test-sampling uncertainty for these trained seeds, not a
population interval over training runs. Class stratification fixes observed
prevalence and avoids one-class AUC draws. BUSI independence is unverified;
intervals may be optimistic and are not patient-level clinical intervals.

For gap comparisons, draw internal and external indices independently, while
preserving method/seed pairing within each cohort. For comparing gaps, the SD
term is the larger sample SD of the two methods' per-seed gaps. Otherwise it is
the larger SD of their per-seed AUCs. A direction is detectable only if its
absolute mean difference exceeds that SD and its paired interval excludes zero
in the same direction. Report all other contrasts as no detectable difference.
There is no familywise multiplicity adjustment; all planned pairwise contrasts
and intervals are shown. Verdicts are exploratory under this supplied rule,
not multiplicity-controlled clinical confirmatory tests.

- H1 first clause: LP detectably better than LoRA at 1% is sufficient support
  for “not worse”; LoRA detectably better rejects; otherwise inconclusive. There
  is no justified noninferiority margin, so a tie cannot support the clause.
  Second clause requires LoRA detectably better at 100%; the opposite rejects.
- H2 ranking clause considers the three FM pairs at each fraction. Detectable
  opposite directions internally/externally reject. All nine pairs detectable
  with matching direction support; otherwise inconclusive. Descriptive rankings
  with uncertain ties are still shown. Gap clause orders the three methods by
  actual trainable count. A detectable positive higher-minus-lower gap for any
  pair/fraction rejects; every pair/fraction detectably negative supports the
  non-growth claim by sufficient evidence; otherwise inconclusive. No causal
  parameter-count conclusion is possible from these three different methods.
- H3 requires each FM method detectably better than CNN at both 1% and 10% on
  the internal primary endpoint (six contrasts). Any detectable opposite result
  rejects; all six positive support; otherwise inconclusive. External analogues
  are separately reported as secondary contrasts.
- Each compound hypothesis is rejected if any clause rejects, supported only
  if all clauses support, otherwise inconclusive. Exact equality does not meet
  strict superiority criteria. Do not change these rules after results.

## Ablations and error analysis

Use selected main-method hyperparameters without retuning. LoRA last-two-block
adapters: all fractions × three seeds (9). LoRA ranks 4 and 16, fixed alpha=16
and dropout=.1: 10% × three seeds (6). Rank therefore changes alpha/r; disclose
that the rank ablation does not isolate rank from scaling. PFT last-four blocks:
10% × three seeds (3). LoRA without augmentation: 10% × three seeds (3).
All other settings and budgets match the corresponding main cell.

After all final predictions, stratify external errors by available BI-RADS and
verification/diagnosis, plus image resolution, mean luminance and contrast.
Do not invent absent lesion-size metadata. Describe small groups with counts;
do not tune on their outcomes. Show shared and method-specific errors, reliability
plots, and 8–12 deterministically selected representative failures (highest
confidence errors, then ID order, balanced across error types where possible).
Use attention rollout/Grad-CAM on saved checkpoints to explore overlays and
calipers. These visualizations cannot establish causal shortcut use or provide
medical diagnosis. No post-error-analysis retraining is part of this protocol.

## Result provenance and remaining gate

Each result records method/fraction/actual counts/seed, configuration and hash,
Git commit and frozen-tag commit, UTC timestamps, source/manifest/backbone hashes,
environment/hardware/threads, target module names, total/trainable parameters,
attempt status, optimization/checkpoint/threshold history, timings (charged and
actual, time-to-best, test inference per image), CPU seconds, peak RSS, deadline
status, test-prediction hashes and metrics. Preserve failed/capped runs. Figures,
tables and manuscript numbers must be generated from these records.

Only Phase 2 may fill T_MAX, final thread count and benchmark-driven fallbacks.
Require model-gradient tests, metric/CI tests, development-only smoke, projected
budget and fair-accounting audit before tagging. No main or tuning result yet.
