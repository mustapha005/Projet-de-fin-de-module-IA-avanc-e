---
title: "Frugal Adaptation of a Self-Supervised Vision Transformer for Breast-Ultrasound Lesion Classification under a Fixed CPU Budget and Center Shift"
author:
  - Mustapha AARAB, Aya AGRIGAH, Badr Eddine TOUBANI — ENSET Mohammedia, Master SDIA
keywords: "foundation models, DINOv2, LoRA, linear probing, partial fine-tuning, breast ultrasound, domain shift, label efficiency, compute budget"
abstract: |
  DRAFT-ABSTRACT. The final abstract (150–250 words) states the question, method, main numeric result and scope. It is written only after the main grid and is filled from generated numbers.
---

::: {custom-style="Keywords"}
*Index Terms*—foundation models, DINOv2, LoRA, linear probing, partial fine-tuning, breast ultrasound, domain shift, label efficiency, compute budget
:::

::: {custom-style="SectionMarker"}
TITLE-END
:::

# Introduction

Foundation models pretrained without labels promise transferable image
representations, but three practical constraints shape whether a medical team
can actually benefit from them: little labeled data, limited compute, and a
deployment site whose images differ from the development data. Recent reviews
of medical imaging foundation models list exactly these issues (compute cost,
data scarcity and domain adaptation) as open problems [@niu2026review]. Which
*adaptation strategy* to use under these constraints is a concrete, answerable
question. A frozen encoder with a linear probe is cheap and hard to overfit.
Partial fine-tuning updates a few top layers. Low-rank adaptation (LoRA)
inserts small trainable matrices throughout the network [@hu2021lora]. Each
spends a different amount of computation and capacity to change the
representation.

Most comparisons of these strategies assume GPU training and report a single
in-distribution test set. Here we fix a CPU-only per-run budget, vary the number
of training labels, and test every model on an unseen acquisition center. We
ask:

> **Research question.** On CPU, at an equal per-run compute cap, does the
> ranking of linear probing, partial fine-tuning, and LoRA for a self-supervised
> ViT on breast-ultrasound lesion classification depend on the label fraction
> (1 / 10 / 100%), and is that ranking preserved on an unseen acquisition center?

We pre-registered three hypotheses before any training. **H1**: linear probing is
not worse than LoRA at 1% labels (internal AUC), and LoRA beats linear probing at
100%. **H2**: the internal strategy ranking is preserved on the external center,
and the internal-to-external AUC gap does not grow with the number of trainable
parameters. **H3**: all three foundation-model strategies beat a ResNet-18
trained from scratch at 1% and 10% labels.

Our contributions are: (i) a frozen, reproducible protocol that equalizes a
wall-clock cap, epoch limit, augmentation and tuning budget across four methods
on a commodity laptop CPU; (ii) a leakage-repaired BUSI split that combines
perceptual hashing with a published duplicate list, and an external BrEaST
evaluation never used for any selection; (iii) a 36-run main grid (four methods,
three label fractions, three seeds) with paired bootstrap contrasts and verdicts
under a decision rule fixed in advance; and (iv) ablations, a cost
analysis and an external error typology that locate where the measured
differences come from.

# Related Work

**Adapting general-purpose self-supervised encoders.** DINOv2 learns visual
features without labels that transfer well through frozen representations
[@oquab2024dinov2]. In radiology, DINOv2 has been evaluated under several
adaptation settings, including linear probing and parameter-efficient
fine-tuning, with results that depend on the task and setting
[@baharoon2023radiology]. Fine-tuning is not uniformly better than probing:
updating the whole network can distort pretrained features and lose
out-of-distribution accuracy even when in-distribution accuracy improves
[@kumar2022distortion]. Updating only selected layers is a competitive middle
ground for vision transformers [@ye2023partial]. These results motivate
comparing *how much* and *where* to adapt, but none fixes a CPU budget or tests
on a separate ultrasound center.

**Parameter-efficient fine-tuning (PEFT) in medical imaging.** LoRA freezes the
pretrained weights and learns low-rank updates [@hu2021lora]. For chest
radiograph foundation models, LoRA has been reported to match or outperform
full fine-tuning across label fractions with a small fraction of tunable
parameters [@lian2024less]. A broad benchmark of PEFT algorithms on medical
image datasets reported that PEFT is especially useful in low-data regimes
[@dutt2024missed]. These studies measure label efficiency, but they use GPU
compute and do not equalize wall-clock cost between strategies. LoRA's small
trainable-parameter count does not imply a small backward-pass cost, because
gradients must still flow through the frozen layers.

**Breast ultrasound and center shift.** BUSI is a widely used public
breast-ultrasound dataset from Egypt [@aldhabyani2020busi]. A published critique
documented duplicated and near-duplicated images and conflicting labels in it
[@pawlowska2023critique]. Splitting BUSI naively can therefore leak test images
into training. BrEaST-Lesions_USG is a curated Polish dataset with biopsy- or
follow-up-verified benign and malignant lesions and BI-RADS metadata
[@pawlowska2024breast; @pawlowska2024tciadata]. Recent work evaluates breast
ultrasound classifiers under cross-dataset shift with multiple seeds, including
a self-supervised transformer [@ramollari2026shift], and a patient-leakage-aware
benchmark uses BUSI and BrEaST for external testing [@wang2026datasetshift].
Ultrasound-specific foundation models (USFM [@jiao2024usfm], the generative
BUSGen [@yu2026busgen], compact TinyUSFM [@ma2026tinyusfm] and USF-MAE
[@megahed2025usfmae]) are an alternative to a general-purpose encoder. USF-MAE's
pretraining corpus includes BrEaST, however, so it could not provide an unseen
external test here. Foundation models also lose accuracy under domain shift in
mammography [@nguyen2026shift], and calibration of frozen foundation models can
differ from their discrimination [@poyrazer2026calibration; @guo2017calibration].

**Where this study sits.** Closest to us are the DINOv2 adaptation comparison in
radiology [@baharoon2023radiology], PEFT label-fraction studies
[@lian2024less; @dutt2024missed], and the ultrasound shift benchmarks
[@ramollari2026shift; @wang2026datasetshift]. We do not claim a better
classifier. We contribute a controlled measurement: the same encoder, a common
CPU wall-clock cap, a repaired data split, pre-registered hypotheses with a
noise-aware decision rule, and a sealed external center. Because no
noninferiority margin is justified for H1, a non-significant difference is
reported as inconclusive rather than as "not worse" [@lakens2017equivalence].
Reporting follows the CLAIM checklist where applicable [@tejani2024claim].

# Materials and Methods

## Data

**Internal cohort (BUSI).** BUSI contains {{data.busi.benign_raw}} benign,
{{data.busi.malignant_raw}} malignant and {{data.busi.normal_excluded}} normal
images [@aldhabyani2020busi]. We kept only benign versus malignant, because the
external set has no normal class, and we ignored the lesion masks. The original
host returned a browser challenge, so we used the public Kaggle mirror of the
same release (CC0) and retained the original attribution. Of the
{{data.busi.binary_raw}} binary images, we removed near-duplicates *before*
splitting. Each image is a node in a graph. Two images are linked if their 8×8
perceptual hashes differ by at most {{data.busi.hamming}} bits, or if they form
a duplicate pair in the published list of {{data.busi.published_pairs}} pairs
[@pawlowska2023critique]. We keep one image per single-label connected
component and quarantine every component whose images carry conflicting labels,
including links to excluded normal images. A first pHash-only pass passed its
own check but left {{data.phash_only.crossing_pairs}} published duplicate pairs crossing splits. We rejected
that split and archived it. The repaired pipeline removed
{{data.busi.removed}} images ({{data.busi.conflict_images}} of them from
{{data.busi.conflict_components}} label-conflict components) and retained
{{data.busi.retained}} ({{data.busi.retained_benign}} benign /
{{data.busi.retained_malignant}} malignant). An independent traversal of the
published duplicate groups confirms that none crosses splits. BUSI has no
patient identifiers, so the split is *image-level*. Patient independence cannot
be verified, and we treat it as a threat to validity [@ucar2026leakage].

**Splits and label fractions.** The retained images were split once, stratified
70/15/15 with seed {{protocol.split_seed}}, into
{{data.busi.train}} training, {{data.busi.val}} validation and
{{data.busi.test}} internal-test images. For each seed we shuffle each training
class and take nested prefixes (1% ⊂ 10% ⊂ 100%). A floor of four images per
class applies at 1%, so the nominal 1% subset has {{data.subset.1.n}} images
({{data.subset.1.actual_pct}}% of training) and the nominal 10% subset has
{{data.subset.10.n}} ({{data.subset.10.actual_pct}}%). Each seed draws its own
subsets, so seed variance includes sampling variance. Validation is always the
full validation split. Total labeled data therefore exceeds the nominal training
fraction, and we do not call this a total-label-budget comparison.

**External cohort (BrEaST).** BrEaST-Lesions_USG contributes
{{data.breast.total}} binary cases ({{data.breast.benign}} benign,
{{data.breast.malignant}} malignant; {{data.breast.normal_excluded}} normal
cases excluded), labeled with the published *Classification* field
[@pawlowska2024breast; @pawlowska2024tciadata]. It is used only for the final
evaluation: never for tuning, early stopping or threshold choice. We found no
cross-cohort exact or pHash near-duplicates. Its reference standard (biopsy or
follow-up), scanners and case mix all differ from BUSI's. The internal–external
gap therefore mixes acquisition, population and verification differences, and
we make no causal claim about the center alone.

## Backbone, preprocessing and augmentation

All three foundation-model methods use DINOv2 ViT-S/14
(`facebook/dinov2-small`, revision {{backbone.revision_short}}, Apache-2.0)
[@oquab2024dinov2] at {{protocol.image_size}}×{{protocol.image_size}} in FP32.
The image representation concatenates the final-normalized CLS token and the
mean patch token. Each image is converted to luminance, replicated to three
channels, resized on its shorter side to 224 and center-cropped, then normalized
with the ImageNet mean and standard deviation. Training uses one augmentation
distribution for every method: RandomResizedCrop (scale 0.8–1.0), horizontal
flip, rotation within ±10° and brightness/contrast jitter of 0.1, seeded per
(run seed, image, view). We use no test-time augmentation.

## Methods compared

**LP:** an L2-regularized logistic regression (balanced class weights) on frozen
features. Features for {{protocol.lp_views}} augmented views per training image
are extracted once and cached, and the cold extraction cost is charged to the
run's budget even when the cache is reused. **PFT:** the last two transformer
blocks, the final layer norm and a linear head are trained, and earlier blocks
run without gradients. **LoRA:** rank-8 adapters (α=16, dropout 0.1) on the
query, key and value projections of all 12 blocks, plus a linear head. The
installed implementation has separate q/k/v projections, not a fused qkv matrix.
**CNN:** ResNet-18 [@he2015resnet] trained from random initialization, the
simple supervised baseline. PFT, LoRA and CNN share AdamW, weighted
cross-entropy, batch size min(32, N), one warm-up epoch followed by cosine
decay, at most {{protocol.max_epochs}} epochs, and early stopping on validation
AUC with patience {{protocol.patience}}.

## Compute budget and hardware

"Fixed compute budget" means that every run gets the same epoch limit and the
same wall-clock cap, T_MAX = {{protocol.cap_seconds}} s
({{protocol.cap_minutes}} min), on one reference machine: an
{{hw.cpu}} laptop ({{hw.physical_cores}} physical / {{hw.logical_cores}} logical
cores, {{hw.ram_gib}} GiB RAM, Python {{hw.python}}), with
{{protocol.threads}} intra-op threads and no accelerator. T_MAX was set before
freezing the protocol from a benchmark of every method and fraction: the larger
of ten full-data epochs of the slowest neural method and 1.25× the cold LP cost.
The budget covers model loading, preprocessing, feature extraction, optimization,
validation and checkpointing. A parent process enforces the deadline. A run that
hits the cap keeps its best complete checkpoint, and updates after the cutoff
are discarded. For every run we log trainable parameters, charged and actual
wall-clock time, time to the best checkpoint, process CPU time, peak resident
memory, inference time per image, and whether the cap was hit.

## Hyperparameter search, thresholds and the frozen protocol

Each method has an equal search budget at seed 0 and the nominal 10% fraction,
selected by validation AUC: LP C ∈ {0.01, 0.1, 1, 10, 100}
({{protocol.search.LP}} configurations); PFT and LoRA learning rate ∈
{1e-4, 3e-4, 1e-3} × weight decay ∈ {0.01, 0.05}; CNN learning rate ∈
{3e-4, 1e-3, 3e-3} × weight decay ∈ {1e-4, 1e-2} ({{protocol.search.CNN}} each).
Ties go to the earlier configuration. The selected configuration is applied
unchanged to every fraction and seed, and every final run starts from
initialization. The F1 threshold maximizes macro-F1 on validation and is applied
unchanged to both test sets. Splits, seeds, search, stopping rule, threshold
policy, statistics, T_MAX and the reference machine were committed under a
`protocol-frozen` Git tag before any tuning or final run. Each test cohort is
evaluated once per final run, on the selected checkpoint.

## Metrics and statistics

The primary metric is ROC-AUC on each test set. Secondary metrics are macro-F1,
the gap AUC~in~ − AUC~out~, 15-bin expected calibration error (ECE), trainable
parameters, CPU time and peak RAM. We report mean ± sample SD over seeds 0, 1
and 2. Uncertainty comes from {{protocol.bootstrap_resamples}} class-stratified
bootstrap resamples of the test images (seed {{protocol.bootstrap_seed}}).
Within each resample the same images pair methods and seeds, and the statistic
is the mean of the three per-seed values. **Decision rule:** a difference counts
only if |Δ mean| exceeds the larger of the two methods' seed SDs *and* the 95%
paired-bootstrap interval of Δ excludes 0 in the same direction. Otherwise we
report "no detectable difference". A hypothesis is *rejected* if any clause is
contradicted by a detectable difference, *supported* only if every clause is
supported by detectable differences, and *inconclusive* otherwise. These
intervals are conditional on the trained seeds and on image-level independence.
There is no multiplicity correction, so all planned contrasts are shown.

## Ablations and error analysis

Using the selected hyperparameters without retuning, we vary one component at a
time. **Where to adapt:** LoRA on the last two blocks only, at all three
fractions, which is directly comparable to PFT. **LoRA rank:** r ∈ {4, 16}, with
α fixed at 16, so rank and scaling change together. **PFT depth:** last four
blocks. **Augmentation:** LoRA without augmentation. All ablations except where
to adapt run at 10%, each with three seeds. On the external set, errors (at the
frozen threshold) are stratified by BI-RADS, verification method, diagnosis,
image size, luminance and contrast. We compare errors shared by all methods with
method-specific ones, and inspect ten deterministically chosen failures with
DINOv2 attention rollout and ResNet-18 Grad-CAM. These visualizations are
exploratory and cannot establish causal shortcut use.

# Results

DRAFT-RESULTS. Written only after the complete main grid. Planned content: main table, cost
table, learning-curve figure, H1–H3 verdict table, ablation table and figure.
Every number comes from `paper/numbers.json` and `tables/`.

# Discussion

DRAFT-DISCUSSION. Interpretation, error typology and comparison with prior work are written
after results.

## Limitations and threats to validity

The external set is small ({{data.breast.total}} cases) and the internal test
set smaller still ({{data.busi.test}} images), so intervals are wide and small
differences are undetectable by design. The split is image-level: BUSI has no
patient identifiers, so related frames of one patient may still fall in
different splits despite deduplication, which would make internal estimates
optimistic. The center comparison is confounded by scanner, population and
reference standard. The nominal 1% fraction is really
{{data.subset.1.actual_pct}}% of the training data because of the
four-per-class floor, and validation always uses the full validation split. We
use a single general-purpose backbone and a binary task without normal images.
BUSI images can carry calipers and text overlays, a known shortcut risk. The
budget is a wall-clock cap on one shared laptop: concurrent load changed epoch
durations, so a capped run's epoch count depends on machine state. Training
itself was deterministic (a restarted tuning run reproduced its validation AUCs
exactly for every shared epoch). A CPU ranking need not transfer to GPU
practice, where LoRA's backward cost is relatively cheaper. Hypothesis verdicts
are exploratory, without multiplicity control.

# Conclusion

DRAFT-CONCLUSION. Direct answer to the research question, written after results.

# Use of AI Assistants {-}

The authors used AI coding assistants, OpenAI Codex and Anthropic Claude Code,
to implement the data pipeline, training and evaluation code, statistical
analysis, figure generation and document build, and to draft and revise text.
Every reference was opened and checked against its source, and every reported
number is generated by code from logged result files. The authors reviewed the
protocol, code and manuscript and remain responsible for the work.

# Data and Code Availability {-}

Code, frozen protocol, configurations, logs and result records are provided as
`SDIA2026_SAN-1_GROUP_13_code.zip`. Images and model weights are not
redistributed. Download and preparation scripts fetch BUSI (CC0 mirror of
[@aldhabyani2020busi]), BrEaST-Lesions_USG from TCIA
[@pawlowska2024tciadata] under its stated license, and DINOv2 (Apache-2.0).

# References {-}
