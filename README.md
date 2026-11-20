# SAN-1 — Frugal adaptation under breast-ultrasound domain shift

Project identifier: `SDIA2026_SAN-1_GROUP_13`

Authors: Mustapha AARAB, Aya AGRIGAH, Badr Eddine TOUBANI

ENSET Mohammedia, Master SDIA, Advanced Artificial Intelligence, 2026–2027.

Submission: 8 December 2026, before the session begins. Article language: English.

On CPU, at an equal per-run compute cap, does the ranking of linear probing,
partial fine-tuning, and LoRA for a self-supervised ViT on breast-ultrasound
lesion classification depend on the label fraction (1 / 10 / 100%), and is
that ranking preserved on an unseen acquisition center?

## Status

Phase 0 is in progress. No scientific training or test-set evaluation has been
performed. No performance result or hypothesis verdict is available.
See [docs/LOG.md](docs/LOG.md) for the current checkpoint and next action.

## Environment and commands

The project uses its own `.venv`; it does not modify global Python packages.
Python 3.12 is the reference interpreter. PowerShell commands from this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-data.txt
.\.venv\Scripts\python.exe scripts/doctor.py
.\.venv\Scripts\python.exe scripts/data_pipeline.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On systems with GNU Make, `make setup`, `make data` and `make check` wrap these
steps (`PYTHON` can be overridden). Other phase targets will be implemented
and verified in phase order; an unavailable target fails explicitly.
The eventual main reproduction command is `make reproduce`; it is **not ready**.
Its runtime and compute cap remain unset pending the CPU benchmark.

## Data and integrity

BUSI is the development/internal-test cohort. BrEaST-Lesions_USG is the sealed
external-test cohort. Only benign/malignant images are included; no masks enter
the classifier. Data, downloaded weights, caches, and credentials are excluded
from Git and the eventual code archive. Downloads retain checksums and sources.
See [data/README.md](data/README.md) and [docs/DATA_CARD.md](docs/DATA_CARD.md).

The protocol must be committed and tagged `protocol-frozen` before final
experiments. Tuning uses training/validation only. Test predictions are produced
only for final, selected checkpoints. Every reported metric must be generated
from logged predictions/results, with three seeds (0, 1, 2).

## Required outputs

`deliverables/` will contain the article (DOCX and PDF), editable PPTX, and code
archive named with the project identifier. They are produced only after real
experiments, statistical analysis, and visual/document audits pass.

Use of AI assistants is recorded in the project log and will be disclosed in
the article. The student authors remain responsible for the submitted work.
