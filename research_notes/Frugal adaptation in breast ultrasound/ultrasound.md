# Recent breast ultrasound foundation models and external evaluation

## Which recent studies are closest to SAN-1

### Takeaway
Cross-dataset breast-ultrasound classification and DINOv2 evaluation already have close precedents. SAN-1 should position its contribution around the interaction of adaptation strategy, label fraction, and measured CPU budget, not claim the first external breast-ultrasound benchmark. This is an inference from the studies below; it is not a claim of exhaustive novelty search.

### Cited Findings
- Ramollari and colleagues published a three-seed BUS-BRA-to-BUSI comparison including DINOv2-B/14 on 18 November 2026. Full-frame DINOv2 failed to fit under their configuration, while a single-seed lesion-crop exploration improved discrimination. They explicitly do not establish the best performance attainable with architecture-specific tuning. SAN-1 uses a smaller backbone and a different adaptation comparison. — [Publisher](https://www.mdpi.com/1999-4893/19/11/1011)
- Wang's 2026 benchmark includes BUSI, BrEaST, BUS-BRA and BUS-UCLM, compares whole frames with ROI inputs, and reports external discrimination and calibration. It uses EfficientNet-B0 and ViT-B/16 with different input resolutions and five seeds. Its patient-ID granularity is a limitation: it reports 780 identifiers for 780 BUSI images and performs no dedicated duplicate screening. This does not independently establish true BUSI patient independence. — [Publisher](https://www.mdpi.com/2075-4418/16/10/1537)
- BUSGen uses generative pretraining on millions of breast-ultrasound images and few-shot adaptation to create downstream training data. This is distinct from adapting one discriminative encoder under a CPU wall-clock cap. The published 2026 article and earlier 2025 preprint represent one work, not two independent references. — [Published article](https://www.nature.com/articles/s41551-026-01639-1?error=cookies_not_supported&code=1); [PubMed identity](https://pubmed.ncbi.nlm.nih.gov/41946926/)

### Inferences
- A valid positioning statement is: prior studies motivate external reliability and modality-specific pretraining; SAN-1 measures which adaptation strategy is useful under explicitly limited local compute and labels. Do not generalize the prior DINOv2 failure to all self-supervised features or to SAN-1's future outcomes.

### Gaps
- No opened source establishes the identical CPU-capped LP/PFT/LoRA, three-fraction BUSI-to-BrEaST experiment. This search cannot establish that no such publication exists.
- Methods/results in the newest Ramollari article were accessible through publisher-indexed excerpts; direct PDF retrieval failed. Its abstract and bibliographic identity were opened successfully. Do not claim an independent reproduction.

## What ultrasound foundation models change the comparison

### Takeaway
Several modality-specific alternatives are now available, but their pretraining corpora and resource assumptions matter. A model pretrained on the external cohort cannot be substituted into a clean unseen-cohort comparison without qualifying that exposure.

### Cited Findings
- USFM targets label-efficient transfer across organs and tasks using ultrasound-specific pretraining. The journal identity is verified as Medical Image Analysis 96, 103202 (2024), DOI 10.1016/j.media.2024.103202. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/38788326/); [Author manuscript](https://arxiv.org/abs/2401.00153)
- USF-MAE applies masked autoencoding and evaluates downstream breast, ovarian, and gastrointestinal classification. Crucially, its OpenUS-46 table lists BrEaST and BUS-BRA among the pretraining datasets. The full text therefore raises a direct pretraining-exposure issue for the proposed BrEaST holdout. — [Full text, Table 1](https://arxiv.org/html/2510.22990v2)
- TinyUSFM addresses model compression by distillation and introduces UniUS-Bench; its benchmark includes BUSI as a three-class task. Model compression and cross-organ averages do not answer a matched adaptation-budget binary external-test question. — [Full text](https://arxiv.org/html/2510.19239v2)
- Ultrasound-CLIP uses ultrasound image-text pretraining and evaluates zero-shot transfer, linear probing, and fine-tuning. It is a recent modality-specific representation reference, but its extra text supervision and pretraining differ from DINOv2. — [Author manuscript](https://arxiv.org/abs/2604.01749); [CVPR proceedings record](https://openaccess.thecvf.com/CVPR2026?day=2026-06-05)

### Inferences
- The choice of DINOv2 can be defended as a controlled general-purpose backbone, while modality-specific models belong in related work and future work. Before adding any alternative, audit whether BUSI or BrEaST entered its pretraining, tuning, or model selection.

### Gaps
- No weights, training code, or data were downloaded or executed in this literature task. Public availability and reported performance do not establish reproducibility on this laptop.
- USF-MAE's venue beyond arXiv remains unverified; label it a preprint. TinyUSFM's published identity was subsequently confirmed in IEEE Journal of Biomedical and Health Informatics (2026), DOI 10.1109/JBHI.2026.3678309. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/41894218/)

## What the external dataset actually measures

### Takeaway
BrEaST supports an independent-cohort binary evaluation after excluding normal images. It should not be described as entirely biopsy-confirmed or as one identifiable acquisition center.

### Cited Findings
- The descriptor reports 256 scans from 256 women, including 154 benign cases, 98 cancers and four normal examples. It reports 197 biopsies and includes follow-up verification. The workbook has one case row per scan; segmented lesion counts should not replace the case count. The dataset explicitly uses CC BY 4.0. — [BrEaST descriptor](https://www.nature.com/articles/s41597-024-02984-z?error=cookies_not_supported&code=1)
- The descriptor explains that the radiologist–medical-center–patient linkage was removed during de-identification. This limits center-stratified interpretation of the public release. — [BrEaST descriptor, de-identification section](https://www.nature.com/articles/s41597-024-02984-z?error=cookies_not_supported&code=1)

### Inferences
- Describe the planned test as an external acquisition cohort/domain, with center shift as the motivating setting. Differences may combine case mix, scanner, imaging practice and verification; they cannot identify a causal center effect.
- Retain the workbook's Classification label. Do not derive malignancy from BI-RADS or mistake absent histology for a missing target label.

### Gaps
- The literature task does not verify local archive contents. The root agent's actual file inventory and split audit remain authoritative for experimental counts.
- Source identities, evidence-access level, verification date and publication-version caveats are recorded in `ultrasound_refs.json`. All numbers above describe cited literature or datasets, not SAN-1 experiments.
