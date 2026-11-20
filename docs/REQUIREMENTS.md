# Requirements and source boundaries

The user's active request is to read the supplied prompt and documents and start
work. The master prompt supplies the intended SAN-1 project plan. The two DOCX
files are course-source evidence for deliverables and grading. Their text does
not supersede current user instructions, tool permissions, or integrity rules.

## Course requirements

- A falsifiable, measured research contribution, not an application.
- A fair simple baseline, frozen experimental protocol, at least three seeds,
  ablations, error analysis, honest limitations, and reproducible code.
- An 8–12 page two-column article excluding references; 150–250 word abstract;
  15–25 references, a majority recent; Word and PDF outputs.
- An editable 12–15 slide PowerPoint; 12-minute talk and 8-minute Q&A; each
  group member presents and understands the whole project.
- Submission before the session on 8 December 2026. Grade weights: question 3,
  rigor 5, results/analysis 4, reproducibility 3, article 3, defense 2, total 20.
- No invented results; cite datasets/models/licenses; disclose AI assistance.

## Master-prompt implementation choices

Group: GROUP_13 (angle brackets in the source treated as placeholder delimiters).
Members: Mustapha AARAB; Aya AGRIGAH; Badr Eddine TOUBANI. Article: English.
CPU comparison of LP, PFT, LoRA, and scratch CNN, at three label fractions and
three seeds (36 final main runs). BUSI for development; BrEaST for external test.
DINOv2 ViT-S/14, fixed split seed, pHash deduplication, fixed tuning grids,
calibration/cost reporting, predefined ablations, and hypothesis decision rules.

## Issues to resolve before protocol freeze

1. BrEaST contains normal examples, contrary to the master prompt's statement
   that it has none. Exclude normals from both cohorts and document the counts.
2. BUSI publication's benign count conflicts with its stated total. Count files;
   never substitute the publication table for a measured inventory.
3. A cached LP has no fresh per-epoch augmentation. Specify the LP feature-view
   policy and account for feature-extraction time in the fixed compute budget.
4. Hugging Face DINOv2 may use separate query/key/value linear layers rather
   than a fused qkv module. Inspect installed modules before targeting LoRA.
5. H1's 'not worse' is not a noninferiority test without a margin. Define a
   descriptive verdict policy; absence of significance cannot establish equality.
6. H2 has two clauses (rank stability and gap vs parameter count). Freeze a
   concrete contrast family and multiplicity/uncertainty interpretation.
7. Full validation labels at low training fractions increase label cost. Report
   this openly; do not call it a total-label-budget comparison.
8. A center/domain comparison is also confounded by case mix, scanner, and
   verification procedure. No causal claim about centers alone is justified.

These are pre-experiment scientific checks, not permission to silently replace
the research question or to relax the course requirements.
