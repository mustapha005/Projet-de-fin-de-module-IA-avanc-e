# Positioning SAN-1 before experiments

Evidence cutoff: 20 November 2026. This review supports protocol decisions; it does not report experimental results or mark the data/protocol gates complete. Bibliographic identities and the depth of source inspection are recorded in `reference_verification.json`.

## The contribution is a constrained adaptation comparison

SAN-1 asks which adaptation strategy is useful when a small DINOv2 encoder, limited training labels and a declared CPU ceiling are fixed, and whether the measured ordering survives external breast-ultrasound testing. Existing work already compares DINOv2 adaptation strategies in radiology, evaluates medical LoRA at limited label fractions, and benchmarks medical PEFT more broadly. The contribution must therefore be stated through the controlled resource and evaluation conditions. The present bounded search does not establish that no identical study exists. ([Baharoon et al.](https://arxiv.org/html/2312.02366v4), [Lian et al.](https://arxiv.org/html/2401.12215v1), [Dutt et al.](https://proceedings.mlr.press/v250/dutt24a.html))

A strong frozen-feature baseline is scientifically motivated. DINOv2 supports transfer through precomputed representations, and feature-distortion research shows that an internal fine-tuning gain need not survive distribution shift. LoRA and partial tuning offer different mechanisms for restricting adaptation, while layer choice remains a variable worth testing. These sources justify the comparison and its location/depth ablations; they do not establish an expected winner for BUSI. ([Oquab et al.](https://arxiv.org/pdf/2304.07193v2), [Kumar et al.](https://arxiv.org/abs/2202.10054), [Hu et al.](https://arxiv.org/abs/2106.09685), [Ye et al.](https://arxiv.org/abs/2312.15681))

## Recent ultrasound work narrows the novelty claim

Recent studies already include DINOv2 in multi-seed cross-dataset ultrasound evaluation and use BUSI and BrEaST within broader external-testing benchmarks. These are close contextual comparisons, but their backbones, framing, adaptation procedures and resource assumptions differ. Their numerical scores should not be presented as directly matched baselines. ([Ramollari et al.](https://www.mdpi.com/1999-4893/19/11/1011), [Wang](https://www.mdpi.com/2075-4418/16/10/1537))

USFM, BUSGen and TinyUSFM illustrate modality-specific representation learning, generative training-data use and model compression. These alternatives motivate a clear rationale for the fixed general-purpose backbone rather than resolving its adaptation ranking. Adding an ultrasound model also requires checking its training corpus: USF-MAE's pretraining table includes BrEaST, so it cannot be assumed to provide an unseen-BrEaST comparison. ([Jiao et al.](https://pubmed.ncbi.nlm.nih.gov/38788326/), [Yu et al.](https://www.nature.com/articles/s41551-026-01639-1), [Ma et al.](https://arxiv.org/html/2510.19239v2), [Megahed et al.](https://arxiv.org/html/2510.22990v2))

## Provenance determines what external performance means

The BUSI descriptor establishes the intended source cohort; its later critique documents transformed duplicates, related lesion frames and conflicting labels. The project's pHash rule must be compared with the published grouping evidence before freeze. A passed pHash crossing check should remain an image-similarity statement, not proof of patient independence. This qualification accords with CLAIM and with work distinguishing recovered acquisition groups from patient identities. ([Al-Dhabyani et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC6906728/), [Pawłowska et al.](https://www.ippt.pan.pl/repository/open/o8361.pdf), [CLAIM 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031/), [Uçar](https://pubmed.ncbi.nlm.nih.gov/42955168/))

BrEaST includes normal cases, uses biopsy or follow-up verification, and omits the original medical-center linkage. Its public release supports external-cohort testing, with acquisition shift as motivation. The observed gap will combine acquisition, case mix and reference-standard differences; it cannot identify an isolated causal center effect. Use the provided Classification field and reconcile eligibility counts with the local inventory. ([BrEaST descriptor](https://www.nature.com/articles/s41597-024-02984-z))

## Inconclusive differences remain scientifically meaningful

H1's “not worse” wording cannot be supported solely by a confidence interval containing zero. Either an appropriate noninferiority margin/procedure must be justified before results, or nondetection must remain inconclusive for that clause. Seed variation, paired test-sampling uncertainty and H2's two clauses need separate definitions. These issues should be resolved in the protocol rather than after inspecting a ranking. ([Lakens](https://pmc.ncbi.nlm.nih.gov/articles/PMC5502906/))

Calibration must be assessed alongside discrimination, not inferred from validation AUC. External findings in mammography and retinal imaging support domain-specific assessment while remaining different-modality evidence. Their published effect sizes are not SAN-1 expectations. ([Guo et al.](https://proceedings.mlr.press/v70/guo17a.html), [Nguyen et al.](https://arxiv.org/abs/2607.10358), [Poyrazer et al.](https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2026.1815982/full))

The study should report actual compute consumption as well as its common ceiling. Feature extraction, cache amortization, tuning and training need explicit accounting, and LP's feature-view policy must be settled before claiming augmentation comparability. The full validation cohort also contributes labels at every nominal training fraction. These are implications of this design; the literature does not prescribe their exact implementation. A documented conditional result, including a negative or inconclusive finding, would address the stated research question more credibly than an unqualified claim of general superiority. ([CLAIM 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031/), [Niu et al.](https://pubmed.ncbi.nlm.nih.gov/42616634/))

The bibliography now has 24 verified identities, including 15 from 2024–2026,
after adding the original ResNet technical report. Identity verification is not
full methodological appraisal: abstract-only records and blocked full texts are
identified in the ledger. Versioned implementation documentation and installed
library licenses are recorded in SOFTWARE_LICENSES.md. The final article must
also include TCIA's dataset citation, alongside its descriptor.

Project follow-through: the combined pHash/published-duplicate audit has now
passed (DATA_CARD.md), and the view, cost and hypothesis rules are specified in
PROTOCOL.md. CPU benchmark and smoke gates remain open; no performance claim
or main-run hypothesis verdict is available.
