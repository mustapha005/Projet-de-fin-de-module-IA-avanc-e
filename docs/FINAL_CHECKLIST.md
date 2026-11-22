# Final quality gate (Phase 7) — DRAFT, 2026-11-22 (article added)

Status of the 17 items of the master prompt, section 9, checked with commands on
2026-11-22. **Not final:** the article is written but its page count needs an Overleaf
compile, and the slides and the code package are still to do. Rubric score estimates are
added once the article and slides are final.

## Open items (❌ / pending)

* 13 — page count needs an Overleaf compile; no LaTeX toolchain exists on the
  reference machine (D015). Two columns and the abstract length are verified offline.
* 14, 16 — slides and package still to do.
* **DOCX deliverable** — the LaTeX source yields the PDF only; see D015.
* 3 — the two literal exceptions are now disclosed in the article (Limitations);
  the row is kept as a warning, not a pass.

## Items

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Falsifiable question in one sentence in abstract and intro | ✅ | The abstract and Section I each state the research question in one sentence; Section I states H1-H3 (`paper/latex/main.tex`) |
| 2 | `protocol-frozen` predates every main-run result | ✅ | Tag commit befa5ba 2026-11-21T02:23:12Z is an ancestor of the first results commit 3a52c61 (2026-11-22T10:36:55Z); `audit_experiments.py` asserts every `completed_utc` > tag time. These times come from the local clock: the repository was first pushed after the results, so GitHub does not independently attest the order |
| 3 | Test sets touched only by `evaluate.py` at the end of final runs | ⚠ exceptions | Each logged result comes from one `final_evaluation` transaction. After all final runs, with no selection: (a) the gallery code ran forward/gradient passes on 10 BrEaST images (`src/analysis/error_analysis.py`); (b) `scripts/rerun_cell.py` retrained and test-evaluated `main_LP_010_s1` twice in scratch folders. Data preparation and post-hoc strata also read held-out metadata/pixels without a model |
| 4 | No near-duplicate crosses splits | ✅ | `data/published_duplicate_audit.json`: 237 published pairs, 0 crossing; `data/dedup_report.json`; regenerated in the fresh clone with no Git-visible change |
| 5 | 3 seeds per reported cell; mean +- std in every table | ✅ | 36 main + 21 ablation runs, seeds {0,1,2}; all six article tables show mean +- SD. The article's strata table is generated from `tables/error_strata_all.csv`, which carries the SDs that the display-only `tables/error_strata_100.md` omits |
| 6 | H1–H3 answered with the pre-registered rule | ✅ | `tables/hypotheses.md`: H1 inconclusive, H2 inconclusive, H3 supported, H3-external inconclusive |
| 7 | ≥ 3 ablations | ✅ | 5 ablations, 21 runs, all complete (`tables/ablations.md`, `docs/reviews/ablation_audit.json`) |
| 8 | Error typology + figure | ✅ | Article Section IV-G with `figures/fig_error_overlap.png` and the BI-RADS/verification strata table; `tables/error_strata_*.{csv,md}`, `error_overlap.*`. The failure gallery is generated locally and not published |
| 9 | Number audit with 0 orphans + 10 numbers hand-checked | ✅ | `scripts/audit_latex.py --final`: 142 prose numbers checked, 0 without a generated source (`docs/reviews/latex_audit.json`). `scripts/handcheck_article_numbers.py`: 12 printed values recomputed independently, AUCs with scikit-learn from the raw prediction CSVs, 0 mismatches (`docs/reviews/article_handcheck.json`) |
| 10 | All references resolve; 15-25, majority 2024-2026 | ✅ | `docs/reference_verification.json`: 25 verified, 16 from 2024-2026; `audit_latex.py` confirms all 25 are cited in `paper/latex/main.tex` and none is missing from `refs.bib` |
| 11 | Licenses for BUSI, BrEaST, DINOv2, main libraries | ✅ | Article section "Data, Code and License Availability" cites BUSI (CC0 mirror, CC BY 4.0 original retained), BrEaST (CC BY 4.0 via TCIA, dataset DOI and descriptor), DINOv2 (Apache-2.0) and the main libraries; evidence in `docs/SOFTWARE_LICENSES.md` |
| 12 | "Use of AI assistants" section | ✅ | `paper/latex/main.tex`, unnumbered section before the availability statement |
| 13 | 8-12 pages excl. refs, two columns, abstract 150-250 words | ⚠ partial | Two columns via IEEEtran `conference`; abstract 241 words (`docs/reviews/latex_audit.json`). Page count unverified: no LaTeX on the reference machine, so it must be read off the Overleaf PDF (D015) |
| 14 | Slides 12–15, editable, notes, member split, numbers = article | pending | `slides/build_slides.py --final` |
| 15 | Fresh clone → smoke passes; one main cell within ±0.005 | ✅ with caveats | `docs/reviews/fresh_clone_2026-11-22.md` (data rebuild with no Git-visible change, 39 tests OK, smoke PASS; no `make`, existing environment reused); `docs/reviews/rerun_main_LP_010_s1_cold.json` (features bit-identical, AUC difference 0.0) |
| 16 | Exact file names; zip has no data/weights/secrets | pending | `scripts/package.py` (after article and slides) |
| 17 | `git log` has no AI-attribution lines | ✅ | `git log` grep for co-authored/generated-with/assistant names: 0 hits; every author and committer is mustapha005 |
