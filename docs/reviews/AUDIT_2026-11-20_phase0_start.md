# Audit — 2026-11-20 — Codex — phase 0 startup

## Verdict

PASS for the tested scaffold; **Phase 0 exit gate NOT YET MET**. Both image
archives, the pinned environment, and the real-data split audit are outstanding.
This is a startup checkpoint, not a completed experimental phase.

## Blocking issues

| Issue | Evidence | Rubric criterion | Next action |
|---|---|---|---|
| Full data not ready | Image downloads pending; no data/split_report.json yet | Rigor; reproducibility | Complete verified downloads, then run data_pipeline.py |
| Isolated environment not verified | pip transfer timed out; retry/uv installation in progress | Reproducibility | Install pinned dependencies, run pip check, save exact lock, rerun tests |
| Main protocol not frozen | docs/PROTOCOL.md says draft; no protocol-frozen tag | Rigor | Resolve methodological questions and run literature/benchmark phases before tag |
| BUSI patient independence unverified | Source lacks an established patient-ID mapping | Rigor; limitations | Inspect distribution and published duplicate list; report residual limitation |

## Non-blocking issues

| Issue | Evidence | Fix |
|---|---|---|
| GNU Make unavailable | Get-Command make returned no command | Native Python equivalents in README; Makefile retained |
| Original BUSI download challenged | docs/source_probe.json records HTML challenge rather than ZIP | Public mirror selected with license/version metadata logged |
| Source statement about external normals incorrect | BrEaST XLSX Classification: benign 154, malignant 98, normal 4 | Exclusion encoded and D001 recorded |

## Checks passed

- `python -m unittest discover -s tests -v`: **7 tests passed**, 0.510 seconds.
  This check used the existing Python 3.12 environment (NumPy 2.5.4, pandas 3.0.6,
  scikit-learn 1.9.1); it is not validation of the requested pinned virtualenv.
- Tests cover transitive duplicate components, conflicting-label quarantine,
  deterministic/nested subsets, external overlap rejection, test-record leakage,
  subset-label tampering, and ZIP traversal rejection.
- `python -m compileall -q scripts src tests`: successful compilation.
- `git ls-files data .inputs .venv`: staged data files are README and provenance
  only; raw datasets, original inputs, and environment are excluded.
- All three supplied sources copied to ignored `.inputs`; SHA-256 recorded in
  `docs/input_sources.json`. Both DOCX texts extracted, including the SAN-1 section.
- Official TCIA metadata ZIP validated and hashed: `data/provenance.json`.
- Both catalogue FM review citations resolve with matching identities; see
  `docs/REFERENCE_CHECKS.md`. Full literature review is not claimed.
- No model results or predictions exist. H1–H3 remain untested.
