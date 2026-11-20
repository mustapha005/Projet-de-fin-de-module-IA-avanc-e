# Validity of breast ultrasound adaptation experiments

## What does deduplication establish about independence?

### Takeaway
Passing a perceptual-hash crossing check supports a narrowly defined image-similarity claim. It does not establish that different partitions contain different patients; CLAIM explicitly recommends patient-level or higher disjointness. [CLAIM 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031/)

### Cited Findings
- The BUSI critique used geometric transformations followed by visual verification, identified transformed duplicates and similar frames of the same lesion, and supplies a duplicate list and supplementary file-to-group information. It also documents conflicting benign/malignant assignments. [Pawlowska et al. 2023](https://www.ippt.pan.pl/repository/open/o8361.pdf)
- A recent kidney-CT study distinguishes perceptual-hash recovery of acquisition groups from recovery of patient identities: its groups can still split a patient's images. This is evidence from CT, not a validated BUSI grouping algorithm. [Ucar 2026](https://pubmed.ncbi.nlm.nih.gov/42955168/)
- CLAIM asks authors to state partition disjointness, data provenance and differences in annotation or data structure between development and external testing. [CLAIM 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031/)

### Inferences
- For SAN-1, audit pHash components against the published BUSI duplicate list before protocol freeze. If known same-lesion groups still cross partitions, either revise the pre-freeze split rule with a documented deviation or explicitly qualify the internal-test result. This is a proposed project action, not a finding about files not yet downloaded.
- Preserve the wording "image-level split after pHash filtering; patient independence unverified" unless patient IDs or validated groups become available. A zero crossing count should always name the hash/threshold used.

### Gaps
- No source reviewed establishes that pHash Hamming distance <=4 detects all BUSI duplicates or reconstructs patient identity.
- The supplied project documents do not provide a patient-ID mapping. Actual retained counts and known-group overlap await the completed data audit.

## What can external testing and calibration tell us?

### Takeaway
External testing can reveal representation failures that an internal score conceals. It does not isolate a causal center effect or establish clinical readiness; calibration requires separate assessment. [Nguyen et al. 2026](https://arxiv.org/abs/2607.10358); [Guo et al. 2017](https://proceedings.mlr.press/v70/guo17a.html)

### Cited Findings
- A mammography benchmark reports heterogeneous external performance across datasets under a common frozen-backbone linear-probe protocol. It is a different modality and not an LP/PFT/LoRA comparison, but directly motivates domain-wise reporting rather than a single aggregate transfer score. [Nguyen et al. 2026](https://arxiv.org/abs/2607.10358)
- The foundational calibration study separates prediction confidence from empirical correctness and evaluates post-processing calibration, including temperature scaling. Its results do not establish that a model trained on BUSI is calibrated on BrEaST. [Guo et al. 2017](https://proceedings.mlr.press/v70/guo17a.html)
- The catalogue TMI review is a verified review of medical-imaging foundation-model components, applications and challenges, not empirical evidence that any SAN-1 adaptation strategy will win. [Niu et al. 2026](https://pubmed.ncbi.nlm.nih.gov/42616634/)
- A retinal transfer study evaluates discrimination, ECE and Brier score separately; external ECE and Brier can rank frozen encoders differently. It uses a learned MLP head and source-fold temperature scaling, with patient-cluster bootstrap for correlated bilateral images. It illustrates an evaluation concern, not a breast-ultrasound result. [Poyrazer et al. 2026](https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2026.1815982/full)

### Inferences
- Describe BUSI-to-BrEaST as cross-cohort/domain testing. Differences in acquisition, patient case mix and reference-standard procedure can contribute to the observed gap; the experiment does not identify their separate causal effects.
- Report internal and external AUC, F1, ECE and reliability plots separately. AUC-based model selection alone does not select a calibrated model. If temperature scaling is added, fit it only on the source validation set and preregister it as a protocol change before experiments.

### Gaps
- The parent project has no test predictions, so no actual calibration or domain-shift claim can yet be made.
- The retinal and mammography studies differ from SAN-1 in modality, models, adaptation, split design and compute budget; their score magnitudes must not be treated as directly comparable baselines.

## What statistical and compute claims are defensible?

### Takeaway
A nonsignificant superiority comparison is not evidence of equivalence or noninferiority. The supplied H1 wording needs an explicit margin/test or a more limited interpretation before freeze. [Lakens 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5502906/)

### Cited Findings
- Lakens explains that failing to reject a zero effect cannot establish that a meaningful effect is absent, and that equivalence testing requires defined equivalence bounds. [Lakens 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5502906/)
- CLAIM calls for named software versions, detailed training and model-selection procedures, clarity about frozen parameters, and hardware detail where computational performance is studied. [CLAIM 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031/)

### Inferences
- Under the supplied two-part detectability rule, "no detectable difference" should make the "not worse" component inconclusive, unless a justified noninferiority margin and test are added before freeze. Do not relabel a confidence interval containing zero as support for H1.
- Keep seed variability and test-sampling uncertainty distinct. Three models evaluated on the same test images do not provide three independent test cohorts. For paired comparisons, bootstrap the same test indices for both methods, and explicitly state how the seed-specific differences are aggregated. Do not pool repeated predictions as independent patients.
- An equal wall-clock cap is a resource ceiling, not equal consumed compute. Log feature extraction and tuning as well as final training. LP cache reuse should expose both one-time extraction cost and amortized cost. These are proposed operational choices; no reviewed source settles the precise accounting convention for SAN-1.
- The full validation set contributes labels even in a nominal 1% training experiment. Call the fractions training-label fractions and report validation-label counts separately.

### Gaps
- A formal paired-bootstrap implementation reference has not yet been added; the project must freeze the resampling unit and degenerate-resample policy.
- No validated noninferiority margin or clinical utility threshold for SAN-1 AUC differences was identified.
- No benchmark or experiment supports the project's CPU cap yet.

### Verification ledger and handoff limits

Eight bibliography candidates are in `validity_refs.json`, five dated 2024–2026. Every record has an opened primary, author-institution or publication-index page and checked title/authors/year/identifier. The exact JSON status distinguishes full text from abstract/metadata only. The highest-priority sources for this project are the BUSI critique, CLAIM 2024, and the noninferiority/equivalence clarification. The Niu review is included because the catalogue specifically requests it; it should not be used for a detailed claim beyond its inspected abstract. Ghosh et al.'s volumetric review is already recorded by the parent and was not added to this candidate set because its 3D emphasis is peripheral.

The published BUSI critique's supplementary source is [Mendeley Data, DOI 10.17632/k8t3gnx9h6.1](https://doi.org/10.17632/k8t3gnx9h6.1), as identified by the opened letter; the supplementary data themselves were not downloaded in this research task. Counts of images participating in duplicate groups must not be mistaken for the number to remove.

No final experimental result, complete phase gate, or exhaustive novelty claim is supported by these notes. No code, shared protocol, or data split was changed.
