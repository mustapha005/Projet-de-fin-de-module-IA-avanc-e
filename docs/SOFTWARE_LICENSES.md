# Software and source attribution

Versions are frozen in requirements.lock. `scripts/audit_licenses.py` reads the
installed wheel metadata and license texts, saving exact evidence and SHA-256
checksums in software_license_evidence.json. The experiment release contains
project code and installation instructions, not bundled third-party binaries.

| Component | Version | License evidence |
|---|---|---|
| PyTorch | 2.6.0+cpu | BSD-3-Clause and included component notices |
| torchvision | 0.21.0+cpu | BSD-3-Clause |
| Transformers | 4.49.0 | Apache-2.0 |
| PEFT | 0.14.0 | Apache-2.0 |
| scikit-learn | 1.6.1 | BSD-3-Clause |
| NumPy | 2.2.6 | BSD-3-Clause plus bundled dependency notices |
| SciPy | 1.15.3 | BSD-3-Clause plus bundled dependency notices |
| pandas | 2.2.3 | BSD-3-Clause |
| Pillow | 11.2.1 | MIT-CMU |
| ImageHash | 4.3.2 | BSD-2-Clause |
| Matplotlib | 3.10.1 | Matplotlib license based on PSF license; included notices |

DINOv2 weights: Apache-2.0; exact revision/source in configs/backbone.json. Dataset
attribution and distribution qualifications are in DATA_CARD.md. BrEaST requires
both the descriptor and TCIA dataset DOI 10.7937/9WKK-Q141; preserve them in the
final article. BUSI mirror license metadata does not replace original attribution.

Opened implementation sources on 2026-11-20:

- [PEFT 0.14.0 LoRA API](https://huggingface.co/docs/peft/v0.14.0/en/package_reference/lora): exact module targeting, rank, alpha, dropout and bias semantics.
- [SciPy 1.15.3 bootstrap API](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.stats.bootstrap.html): paired resampling and interval definitions. SAN-1 uses an explicit class-stratified index sampler, not SciPy's default BCa routine; the code and assumptions must be reported.
- [Original ResNet technical report](https://arxiv.org/abs/1512.03385): He, Zhang, Ren, Sun, 2015; title and authors checked. This entry uses the verified preprint year rather than unverified conference metadata.

These citations identify implementation sources. They do not validate SAN-1's
medical performance, statistical coverage under missing patient IDs, or fairness.
