# Final quality gate (Phase 7) — DRAFT, 2026-11-22

Status of the 17 items of the master prompt, section 9, checked with commands on
2026-11-22. **Not final:** the article and slides are on hold at the user's request, so
the items that depend on them stay open. Rubric score estimates are added once the
article and slides are final.

## Open items (❌ / pending)

* 1, 9, 13, 14, 16 — depend on the final article/slides/package (on hold).
* 5 — `tables/error_strata_100.md` shows means without SD (the SDs are in
  `error_strata_all.csv`). To fix before article writing uses that table.
* 3 — literal exceptions, to disclose in the article and slides (see the row).
* 11 — the article does not yet cite the BUSI and BrEaST licenses or the main library
  licenses (only DINOv2's Apache-2.0 appears). To fix during article writing.

## Items

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Falsifiable question in one sentence in abstract and intro | pending | Intro states the RQ and H1–H3 (`paper/article.md`); abstract is still a draft placeholder |
| 2 | `protocol-frozen` predates every main-run result | ✅ | Tag commit befa5ba 2026-11-21T02:23:12Z is an ancestor of the first results commit 3a52c61 (2026-11-22T10:36:55Z); `audit_experiments.py` asserts every `completed_utc` > tag time. These times come from the local clock: the repository was first pushed after the results, so GitHub does not independently attest the order |
| 3 | Test sets touched only by `evaluate.py` at the end of final runs | ⚠ exceptions | Each logged result comes from one `final_evaluation` transaction. After all final runs, with no selection: (a) the gallery code ran forward/gradient passes on 10 BrEaST images (`src/analysis/error_analysis.py`); (b) `scripts/rerun_cell.py` retrained and test-evaluated `main_LP_010_s1` twice in scratch folders. Data preparation and post-hoc strata also read held-out metadata/pixels without a model |
| 4 | No near-duplicate crosses splits | ✅ | `data/published_duplicate_audit.json`: 237 published pairs, 0 crossing; `data/dedup_report.json`; regenerated in the fresh clone with no Git-visible change |
| 5 | 3 seeds per reported cell; mean ± std in every table | ❌ | Seeds complete; `main_results`, `cost` and `ablations` show mean ± SD, `error_strata_100` does not (see open items) |
| 6 | H1–H3 answered with the pre-registered rule | ✅ | `tables/hypotheses.md`: H1 inconclusive, H2 inconclusive, H3 supported, H3-external inconclusive |
| 7 | ≥ 3 ablations | ✅ | 5 ablations, 21 runs, all complete (`tables/ablations.md`, `docs/reviews/ablation_audit.json`) |
| 8 | Error typology + figure | ✅ (article pending) | `tables/error_strata_*.{csv,md}`, `error_overlap.*`, `figures/fig_error_overlap.png`; the failure gallery is generated locally and not published |
| 9 | `audit_numbers.py` 0 orphans + 10 numbers hand-checked | pending | Run after the final article build |
| 10 | All references resolve; 15–25, majority 2024–2026 | ✅ | `docs/reference_verification.json`: 25 verified, 16 from 2024–2026; all 25 cited in `paper/article.md` |
| 11 | Licenses for BUSI, BrEaST, DINOv2, main libraries | ❌ | See open items |
| 12 | "Use of AI assistants" section | ✅ (draft) | `paper/article.md` section present |
| 13 | 8–12 pages excl. refs, two columns, abstract 150–250 words | pending | `paper/build.py` reports pages and abstract words |
| 14 | Slides 12–15, editable, notes, member split, numbers = article | pending | `slides/build_slides.py --final` |
| 15 | Fresh clone → smoke passes; one main cell within ±0.005 | ✅ with caveats | `docs/reviews/fresh_clone_2026-11-22.md` (data rebuild with no Git-visible change, 39 tests OK, smoke PASS; no `make`, existing environment reused); `docs/reviews/rerun_main_LP_010_s1_cold.json` (features bit-identical, AUC difference 0.0) |
| 16 | Exact file names; zip has no data/weights/secrets | pending | `scripts/package.py` (after article and slides) |
| 17 | `git log` has no AI-attribution lines | ✅ | `git log` grep for co-authored/generated-with/assistant names: 0 hits; every author and committer is mustapha005 |
