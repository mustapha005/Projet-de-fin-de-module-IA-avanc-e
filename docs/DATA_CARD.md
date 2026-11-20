# Data card

Checked on 20 November 2026. Both archives are downloaded, hashed and inventoried.
The corrected manifests pass pHash and published-duplicate audits. No model
predictions or experimental performance metrics exist yet.

## Measured cohorts

| Cohort / split | Benign | Malignant | Total |
|---|---:|---:|---:|
| BUSI binary source | 437 | 210 | 647 |
| BUSI after cleaning | 311 | 177 | 488 |
| BUSI training | 217 | 124 | 341 |
| BUSI validation | 47 | 26 | 73 |
| BUSI internal test | 47 | 27 | 74 |
| BrEaST external test | 154 | 98 | 252 |

Evidence: data/inventory_report.json, data/split_report.json and data/manifests/.
Excluded normals: BUSI 133; BrEaST four. Masks never enter the classifier.
BrEaST labels use Classification, not a BI-RADS-derived substitute. The external
cohort has not been used for tuning.

## BUSI provenance and terms

Baheya Hospital, Cairo, Egypt. Al-Dhabyani, Gomaa, Khaled and Fahmy, Dataset of
breast ultrasound images, Data in Brief 28, 104863 (2020 issue; online 2019),
https://pmc.ncbi.nlm.nih.gov/articles/PMC6906728/ (DOI 10.1016/j.dib.2019.104863).
Local counts resolve the article's inconsistent benign-count table.

The university host returned an HTML challenge. Acquisition used the public
Kaggle mirror, version 1 (2021-03-14), whose API states CC0: Public Domain:
https://www.kaggle.com/datasets/aryashah2k/breast-ultrasound-images-dataset.
docs/source_probe.json records the response. The original article is CC BY 4.0
and describes research uses. The mirror label does not establish that its uploader
can change the original authors' terms. We retain attribution and redistribute
no images. No additional text/license files were found in the archives.

Archive SHA-256: 7fffc86a517934da55021f66641d81383058d26a30adb0ffab3780ca7e52d57d.
Binary source dimensions range from 190 to 1048 pixels wide and 324 to 719 high.

## Deduplication and independence

The first pHash-only split was rejected after the published duplicate list exposed
20 direct pairs crossing its splits. Those superseded reports are retained under
docs/reviews/phash_only/ and are not valid experimental inputs.

The corrected graph combines pHash Hamming distance <=4 with Pawlowska, Karwat
and Zolek (2023), Table B1:
https://pmc.ncbi.nlm.nih.gov/articles/PMC10293973/table/tbl0004/.
The attributed facts (CC BY 4.0) are versioned in configs/busi_published_pairs.json.
Continuous IDs 1-437 are benign, 438-647 malignant, and 648-780 normal. IDs are
validated against source filenames. A single-label component keeps its first
lexicographic image ID; ambiguous components are entirely quarantined, including
binary images linked to normal cases. Total removed: 159 binary images, comprising
17 ambiguous-label images and 142 redundant consistent-label images.

A local contact sheet confirmed visible similarity of the quarantined binary
class duplicates. This is an image-similarity inspection, not clinical relabeling.
The independent graph audit also follows connections through removed images.
There are no remaining published duplicate groups, no pHash crossings between
splits or cohorts, and no within-external pHash pairs. Evidence:
data/published_duplicate_audit.json and data/cohort_overlap_report.json.

These checks do not prove patient independence: original BUSI patient identifiers
remain unavailable. Axilla cases, annotations and other source-quality issues
remain limitations. No extra ROI/annotation-based selection has been performed.

## Fractions

Stratified 70/15/15 split, seed 1234, yields 341/73/74 after integer rounding.
Each seed 0/1/2 independently shuffles each training class and selects nested
prefixes. All 73 validation labels are retained for every training fraction.

| Nominal fraction | Benign | Malignant | Training labels | Actual fraction |
|---|---:|---:|---:|---:|
| 1% | 4 | 4 | 8 | 2.346% |
| 10% | 21 | 12 | 33 | 9.677% |
| 100% | 217 | 124 | 341 | 100% |

The low-label setting uses the declared four-per-class floor. Full validation
labels contribute to annotation cost, so this is not a total-label-budget study.

## BrEaST provenance and terms

Official collection: https://www.cancerimagingarchive.net/collection/breast-lesions-usg/.
Version 1 dataset: https://doi.org/10.7937/9WKK-Q141.
Pawlowska et al. descriptor: https://doi.org/10.1038/s41597-024-02984-z (2024).
Explicit dataset license: CC BY 4.0, with required dataset/descriptor citation and
TCIA use-policy attribution.

This is a Polish external acquisition cohort; original center linkage was removed
from the public release. Verification uses biopsy or follow-up, not histology in
every case. Dataset shift combines acquisition, case mix and verification; it
cannot identify an isolated causal center effect or yield per-center estimates.

The workbook has 256 rows and includes CaseID, Image_filename, BIRADS, Verification
and Diagnosis. Its 252 binary records form the external cohort.
Image archive SHA-256: c32e49cdfa54042e065582d0cb35978b5fc5e5b5e461b33bf773fb50cfdad355.
Workbook SHA-256: 89a8874496a6f1f93960390b963f7369b90f7e72ee08a738f2d17e37f5eff8bf.

## Release policy

Raw data, clinical workbook, caches, weights and QA image sheets are Git-ignored.
Release only scripts, necessary non-identifying manifest fields, source attribution
and audit reports. Download sizes, URLs and checksums are in data/provenance.json.
