# Defense Q&A preparation (8-minute Q&A)

Every member must be able to answer every question. Answers point to evidence in the
repository. Result numbers are quoted from `paper/numbers.json` / `tables/` only;
entries marked **[after results]** are completed once `make analysis` has run.

## Question, positioning and design

1. **What exactly is your research question, and how could it be answered "no"?**
   On CPU at an equal per-run cap, does the LP/PFT/LoRA ranking depend on the label
   fraction, and is it preserved on an unseen center? Each of H1–H3 has explicit
   support/reject/inconclusive rules (docs/PROTOCOL.md, "Metrics, uncertainty and
   hypothesis decisions"), so any clause can be rejected by a detectable opposite result.

2. **Why DINOv2 and not a medical or ultrasound foundation model?**
   The question concerns adaptation strategies, so the encoder is held fixed. DINOv2
   ViT-S/14 is small enough for CPU fine-tuning, has a permissive license (Apache-2.0)
   and a pinned revision. Ultrasound models exist (USFM, TinyUSFM, USF-MAE). USF-MAE's
   pretraining corpus includes BrEaST, so it could not give an unseen external test.
   A single general-purpose backbone is listed as a limitation.

3. **Why is your 1% fraction not exactly 1%?**
   1% of 341 training images would give 3 images, which can leave one class empty. The
   pre-authorized floor (D005) is 4 images per class, so nominal 1% = 8 images = 2.35%
   of training (`data/split_report.json`). Tables and figures show actual counts.

4. **Is the validation set not also labels? Then 1% is not 1% of labels.**
   Correct: validation stays the full validation split (73 images) at every fraction,
   as specified, so this is not a total-label-budget comparison. It is stated in the
   methods and limitations (docs/REQUIREMENTS.md item 7).

5. **Why benign versus malignant only?**
   BrEaST's binary task is the shared one across both cohorts. BrEaST has only four
   normal cases (excluded, D001), and BUSI's normal class has no external counterpart.

6. **Why is a ResNet-18 from scratch a fair baseline?**
   It gets the same augmentation, epoch limit, wall-clock cap, tuning budget (6
   configurations) and stopping rule as the adapted methods (docs/PROTOCOL.md). If it
   wins, we report that.

## Protocol rigor and integrity

7. **How do you know the test set was used only once?**
   For every reported result it was: one evaluation per final run. (a)
   `src/datasets.development_rows` refuses held-out rows, so tuning only sees
   train/validation. (b) `src/evaluate.final_evaluation` produces the predictions, only for
   purpose main/ablation, and within a run's output folder a different checkpoint or an
   interrupted evaluation fails closed. (c) Prediction files are hashed into each result JSON.
   Two post-hoc exceptions, neither used for selection: the reproducibility check retrained
   and re-evaluated LP 10% seed 1 twice in scratch folders, and the failure gallery ran
   saliency passes on 10 external images.

8. **When was the protocol frozen, and how can we check?**
   Git tag `protocol-frozen` → befa5ba (2026-11-21T02:23:12Z). The first commit adding
   anything to `results/` is f0df013, after it. `verify_frozen()` checks 21 protected
   file hashes, package versions and hardware before every run.

9. **Did near-duplicates leak between train and test?**
   A pHash-only split passed its own check but left 20 published duplicate pairs
   crossing splits. It was rejected (archived in docs/reviews/phash_only/), and the
   pipeline was rebuilt with the union of pHash and the published duplicate list (D007).
   An independent traversal now finds 0 crossings (`data/published_duplicate_audit.json`).
   Patient-level independence remains unverifiable because BUSI has no patient IDs.

10. **How was the decision threshold for F1 chosen?**
    It maximizes validation macro-F1 per final run, with fixed tie rules, and is applied
    unchanged to both test sets. No threshold was ever chosen on a test set.

11. **How did you tune hyperparameters, and was it fair?**
    Seed 0, nominal 10%, validation AUC only. Same grid size per method (5 for LP's C,
    6 for the others) and the same cap per candidate. Selections are in
    `configs/frozen/*.json` with their full ledgers, applied unchanged everywhere.

12. **Is your result reproducible?**
    Training is deterministic on the reference machine. Two attempts of the same tuning
    run produced identical validation AUCs for all 35 shared epochs
    (docs/reviews/AUDIT_2026-11-21_phase3_claude_resume.md). Seeds, config hashes, Git
    commit, hardware, package lock and timings are in every result JSON.
    **[after results]** Fresh-clone rerun of LP, 10%, seed 1 within ±0.005 AUC.

## Compute budget

13. **What does "fixed compute budget" mean concretely?**
    Same epoch limit (50) and the same wall-clock cap T_MAX = 1,440 s per run on one
    laptop CPU with 4 threads. Loading, preprocessing, LP feature extraction (charged
    even on cache hits), training, validation and checkpointing all count. A parent
    supervisor enforces the cap.

14. **Why should a CPU-only budget generalize to GPU practice?**
    It need not, and we do not claim it does. On GPU, LoRA's backward pass through the
    frozen network is relatively cheaper, so a budget-bound ranking could change. The
    finding is conditional on frugal CPU settings, which is the use case studied.

15. **LoRA trains few parameters. Why is it slow?**
    Gradients still flow back through all 12 frozen blocks to reach the adapters, so
    its backward cost is close to full fine-tuning even though it updates few weights.
    PFT stops back-propagation after the last two blocks. **[after results]** cost table.

16. **Did machine load affect your runs?**
    Yes, and we measured it. On battery or under concurrent load, epochs were up to
    ~70% slower, so a capped run completes fewer epochs. Results stay deterministic
    given the epoch count. Each run logs its epochs, and `logs/power_log.csv` records the
    power state. This is reported as a threat to validity.

## Results and statistics [after results]

17. **Is your gap above the noise?** Quote the decision rule (|Δ| > larger seed SD and
    paired 95% CI excludes 0) and the specific contrasts from `tables/contrasts.csv`.
18. **What are your H1–H3 verdicts and why?** `tables/hypotheses.md`.
19. **Which method would you recommend at 1%, at 100%, and for a new site?**
20. **Why is the external AUC lower or higher than internal?** Case mix, reference
    standard (biopsy/follow-up), scanners. The gap is not a pure center effect.
21. **What do the ablations tell you about where the effect comes from?**
22. **What kinds of errors do the models make on BrEaST?** Error strata and overlap
    tables, gallery figure.
23. **Are the models calibrated?** ECE table and reliability figure. No post-hoc
    calibration was applied.
24. **What would you do with more time or compute?** Patient-level split with patient
    IDs, more external centers, an ultrasound-pretrained backbone without BrEaST in
    its corpus, GPU replication, noninferiority with a justified margin.
25. **What did the AI assistants do, and how did you verify their work?** Use of AI
    Assistants section, audits in docs/reviews/, frozen-tag checks, number audit
    (`scripts/audit_numbers.py`) and reference verification ledger.
