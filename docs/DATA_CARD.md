# Data card — acquisition in progress

The BrEaST clinical workbook has been downloaded and inspected. Image archive
downloads and the split audit are still in progress; no split PASS is claimed.

## BUSI

Origin: Baheya Hospital, Cairo, Egypt. Primary publication: Al-Dhabyani, Gomaa,
Khaled, Fahmy, *Dataset of breast ultrasound images*, Data in Brief 28, 104863
(2020 issue; online 2019), DOI 10.1016/j.dib.2019.104863.
Source checked 2026-11-20: https://pmc.ncbi.nlm.nih.gov/articles/PMC6906728/
The paper explicitly describes research uses of the dataset, is CC BY 4.0, and
links the university distribution. The official host returns a challenge page.
The public Kaggle mirror's API was fetched on 2026-11-20 and identifies version
1 (2021-03-14) as CC0: Public Domain. That is the mirror's stated license, not
proof that the mirror uploader can change the original authors' terms. The
project retains attribution to the original authors and redistributes no images.
The archive's notices still need inspection; no claim of a separate original
dataset-specific license grant is made from the article license alone.
Mirror evidence: `docs/source_probe.json`, source
https://www.kaggle.com/api/v1/datasets/view/aryashah2k/breast-ultrasound-images-dataset

University page: https://scholar.cu.edu.eg/?q=afahmy/pages/dataset
Archive candidate: https://scholar.cu.edu.eg/Dataset_BUSI.zip
The paper's class table is internally inconsistent (benign count vs total).
Only a measured local inventory will establish the experimental sample sizes.
Patient IDs are not established; image-level splitting may leak patient identity
even after near-duplicate removal. No masks are used as classifier inputs.

## BrEaST-Lesions_USG

Official collection: https://www.cancerimagingarchive.net/collection/breast-lesions-usg/
Dataset DOI: https://doi.org/10.7937/9WKK-Q141 (version 1).
Descriptor: https://doi.org/10.1038/s41597-024-02984-z (2024).
Explicit dataset license: CC BY 4.0 with required citation/TCIA use policy.
The primary descriptor reports 256 patients/scans, including 154 benign,
98 malignant, and four normal. These are source-reported counts, not yet local
measurements. Confirmation is by biopsy or follow-up, not histology in every case.
The downloaded workbook independently confirms 256 rows: 154 benign, 98 malignant,
four normal, using the `Classification` column, not a BI-RADS-derived label.
Workbook SHA-256: `89a8874496a6f1f93960390b963f7369b90f7e72ee08a738f2d17e37f5eff8bf`.
It provides CaseID, Image_filename, BIRADS, Verification, Diagnosis and other
fields. This cohort is external test only, not a second validation set.

## Release policy

Do not redistribute either cohort in this project's repository/code ZIP. Provide
download/preparation scripts, source URLs, hashes, and aggregate audit reports.
Keep raw metadata local; publish only necessary non-identifying manifest fields.
