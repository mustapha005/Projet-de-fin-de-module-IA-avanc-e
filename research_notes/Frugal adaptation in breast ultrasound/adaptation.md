# Adaptation methods and evidence

## What supports linear probing partial fine tuning and LoRA

### Takeaway
Existing evidence supports all three as credible comparators, but does not establish a universal winner. DINOv2 was designed for useful frozen representations, and feature-distortion research explains why improved internal performance need not imply improved external performance. [DINOv2](https://arxiv.org/pdf/2304.07193v2), [feature distortion](https://arxiv.org/abs/2202.10054)

### Cited Findings
- **Oquab et al., TMLR 2024:** the author PDF explicitly carries a January 2024 publication header. Sections 7.1–7.2 evaluate frozen representations and supervised adaptation; the transfer-benchmark protocol includes logistic regression on precomputed features. These are natural-image benchmarks, not evidence that LP will win on ultrasound. [Author PDF](https://arxiv.org/pdf/2304.07193v2)
- **Hu et al., 2021:** LoRA freezes pretrained weights and learns low-rank updates. The original experiments concern language models, so their throughput, memory and accuracy gains cannot be transferred numerically to a CPU vision pipeline. [Original paper](https://arxiv.org/abs/2106.09685)
- **Kumar et al., 2022:** fine-tuning can perform worse than linear probing out of distribution when pretrained representations are strong and the distribution change is large. The paper proposes feature distortion as an explanation and examines LP followed by fine-tuning. This motivates measuring internal and external rankings separately. [Original paper](https://arxiv.org/abs/2202.10054)
- **Ye et al., 2023:** the abstract reports comparisons of partial-tuning strategies and emphasizes layer selection. This supports a location/depth ablation; it does not establish the last two DINOv2 blocks as the best choice for BUSI. [Original preprint](https://arxiv.org/abs/2312.15681)

### Inferences
- Parameter count and elapsed training cost require separate measurements. The LoRA language-model results do not prove a proportional CPU saving for this architecture. [Basis](https://arxiv.org/abs/2106.09685)
- LP should be a substantive baseline: preserving a representation could help under external shift. [Basis](https://arxiv.org/abs/2202.10054)
- Last-two-block versus all-block LoRA, alongside PFT, could distinguish adaptation location from adaptation mechanism. This is a proposed interpretation of the project ablation, motivated by layer-selection evidence. [Basis](https://arxiv.org/abs/2312.15681)

### Gaps
- These sources do not validate the project's exact two-block depth, rank 8, or shared CPU cap. Those remain protocol choices to test.
- No source examined establishes noninferiority of LP under the project's proposed statistical rule. Nonsignificance should not be described as established equivalence.

## How directly medical adaptation studies apply to SAN 1

### Takeaway
Medical PEFT comparisons and low-label DINOv2 evaluations already exist. SAN-1 should position itself as a controlled study of specific compute and acquisition-domain constraints, with a small backbone and strict data auditing, rather than as the first medical application of LoRA or DINOv2. [Baharoon et al.](https://arxiv.org/html/2312.02366v4), [Lian et al.](https://arxiv.org/html/2401.12215v1)

### Cited Findings
- **Baharoon et al., preprint 2023, revision 2024:** Table 9 compares LP, full fine-tuning, LoRA and BitFit on DINOv2 ViT-g/14 using NIH Chest X-ray and CheXpert. Appendix B.3 specifies LoRA rank 48, alpha 16 and dropout 0.1. This is close prior art, but not the proposed small-backbone ultrasound fixed-CPU study. [Full text](https://arxiv.org/html/2312.02366v4)
- **Lian et al., 2024:** the main study compares LoRA with full tuning on MRM/MAE chest-radiograph models at 1%, 10% and 100% labels. It includes rank ablations and an additional DINOv2 B/14 and L/14 comparison. Results vary across tasks; this does not justify claiming universal LoRA superiority. [Sections 2.1–2.4](https://arxiv.org/html/2401.12215v1)
- **Dutt et al., MIDL 2024:** the proceedings verify a broad benchmark spanning PEFT algorithms, CNN/transformer backbones and medical datasets. The publisher abstract supports systematic benchmarking; full implementation details were not inspected here. [Publisher record](https://proceedings.mlr.press/v250/dutt24a.html)
- **Zoellin et al., 2024 preprint:** DINORET and block-expanded DINORET adapt DINOv2 through additional self-supervision for retinal tasks and investigate forgetting. This contextualizes domain adaptation but changes both modality and procedure relative to SAN-1. [Original preprint](https://arxiv.org/abs/2409.17332)

### Inferences
- A defensible contribution is to evaluate whether established strategy rankings change with label availability under a declared CPU cap, then test their ordering externally on ultrasound. This is a scoped positioning proposal, not proof that no identical prior study exists. [Nearest comparison](https://arxiv.org/html/2312.02366v4), [medical low-label study](https://arxiv.org/html/2401.12215v1)
- The evidence permits either PEFT gains or a strong frozen-feature baseline. It should motivate hypotheses without precommitting findings. [Medical benchmark](https://proceedings.mlr.press/v250/dutt24a.html), [LP under shift](https://arxiv.org/abs/2202.10054)

### Gaps
- No matched BUSI-to-BrEaST comparison with the same model, preprocessing, duplicate policy and CPU cap was verified in this bounded search. This is a search limitation, not proof of novelty.
- These studies do not supply transferable expected AUCs for SAN-1. Their metrics must not replace local measurements or enter this project's results table.
- Source-level variability and hardware fairness were not comprehensively audited. No external paper is certified as a direct numerical baseline.

## What is verified and what remains before writing

### Takeaway
Eight references have verified identities in opened primary sources; four have verified 2024 publication/preprint dates. Complete bibliographic records are in `adaptation_refs.json`. This is research preparation, not a passed phase gate or a scientific result.

### Cited Findings

| Candidate | Date treatment | Opened source and depth | Use |
|---|---|---|---|
| Oquab et al. | TMLR 2024; original preprint 2023 | [Author PDF](https://arxiv.org/pdf/2304.07193v2), publication header, authors, selected evaluation sections | Backbone and frozen-feature rationale |
| Hu et al. | 2021 preprint cited here | [arXiv identity and abstract](https://arxiv.org/abs/2106.09685) | Original LoRA mechanism |
| Kumar et al. | 2022 | [arXiv identity and abstract](https://arxiv.org/abs/2202.10054) | Internal/external ranking rationale |
| Ye et al. | 2023 preprint; later venue unverified | [arXiv identity and abstract](https://arxiv.org/abs/2312.15681) | Layer/depth ablation motivation |
| Lian et al. | 2024 preprint | [Full-text HTML](https://arxiv.org/html/2401.12215v1), settings and ablations | Direct medical PEFT/label-fraction prior art |
| Baharoon et al. | 2023 preprint; v4 revised September 2024 | [Full-text HTML](https://arxiv.org/html/2312.02366v4), Table 9 and appendix B.3 | Closest DINOv2 comparator |
| Dutt et al. | MIDL/PMLR 2024; original preprint 2023 | [Publisher](https://proceedings.mlr.press/v250/dutt24a.html), full metadata and abstract; PDF fetch failed | Medical PEFT benchmark |
| Zoellin et al. | 2024 preprint | [arXiv identity and abstract](https://arxiv.org/abs/2409.17332) | DINOv2 domain adaptation context |

### Inferences
- Use published dates where verified, but do not relabel Baharoon's 2023 preprint as a 2024 publication merely because it was revised. The final combined bibliography still needs a recent majority; this subset has four of eight. [DINOv2 header](https://arxiv.org/pdf/2304.07193v2), [Baharoon history](https://arxiv.org/abs/2312.02366), [Dutt publication](https://proceedings.mlr.press/v250/dutt24a.html)
- If space is tight, prioritize Oquab, Hu, Kumar, Lian, Baharoon and Dutt. Ye and Zoellin support narrower arguments.

### Gaps
- Veasey and Amini's 2024 ISBI lung-nodule DINOv2/LoRA paper is relevant (DOI 10.1109/ISBI56570.2024.10635887), but direct IEEE access returned a challenge. It is excluded from the eight eligible candidates because primary author metadata could not be fully checked on an opened paper page. [Publisher](https://ieeexplore.ieee.org/document/10635887)
- A 2026 CVPR scalable-3D-adaptation paper surfaced in official search results, but direct opening was blocked. It remains a follow-up. [Official lead](https://openaccess.thecvf.com/content/CVPR2026/html/Liu_Revisiting_2D_Foundation_Models_for_Scalable_3D_Medical_Image_Classification_CVPR_2026_paper.html)
- Abstract-only sources support limited contextual claims. Their identity verification is not a full methodological review.
