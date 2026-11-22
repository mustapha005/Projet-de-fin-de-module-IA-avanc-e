# Article sources (IEEE two-column, LaTeX / Overleaf)

This folder is a self-contained Overleaf project. Nothing here refers to a file
outside it.

## Opening it in Overleaf

1. Zip **the contents of this folder** (so that `main.tex` is at the top level of
   the zip, not inside another folder).
2. Overleaf: *New Project* -> *Upload Project* -> choose the zip.
3. *Menu* -> **Compiler: pdfLaTeX**, **Main document: main.tex**.
4. Press *Recompile*. Overleaf runs BibTeX and the needed passes itself. If the
   citations show as `[?]` on the first run, press *Recompile* once more.

`IEEEtran.cls` and `IEEEtran.bst` ship with Overleaf, so nothing has to be
installed.

## What is hand-written and what is generated

| Path | Written by | Content |
|---|---|---|
| `main.tex` | the authors | all prose, section structure, captions |
| `numbers.tex` | `scripts/make_latex.py` | one `\val...` macro per measured value |
| `tables/*.tex` | `scripts/make_latex.py` | the six tables, from `tables/*.csv` |
| `figures/*.png` | `src/analysis/figures.py` | the five figures, 300 dpi |
| `refs.bib` | the authors | 25 verified references |

**Do not type a result number into `main.tex`.** Every measured value is a macro,
for example `\valMainLoRAHundredAucIn`, whose body comes from
`paper/numbers.json`, which in turn is generated from `results/`. The comment at
the end of each line in `numbers.tex` names the key it came from.
`scripts/audit_latex.py` fails if a numeric literal appears in the prose without
a generated source, so a hand-typed number is caught rather than shipped.

## Regenerating after a change to the results

From the project root, with the experiment environment:

```powershell
.\.venv\Scripts\python.exe scripts/make_latex.py              # numbers, tables, figures, refs
.\.venv\Scripts\python.exe scripts/audit_latex.py --final     # structure + number provenance
.\.venv\Scripts\python.exe scripts/handcheck_article_numbers.py
```

`make_latex.py` overwrites `numbers.tex`, `tables/`, `figures/` and `refs.bib`.
It never touches `main.tex`.

## Checks that run here, and the one that does not

`audit_latex.py` verifies that the sources are ASCII and brace-balanced, that
every `\cite` resolves to `refs.bib` and every entry is cited, that every `\ref`
has a label, that every figure and `\input` target exists, that every `\val`
macro used is defined, that the abstract is 150-250 words, and that no prose
number lacks a generated source.

It **cannot** tell you the document compiles or how many pages it is. Overleaf
is the only check for those. The course requires 8-12 pages excluding
references; read the page count off the compiled PDF and tell the group if it
falls outside that range.

## Deliverable formats

The course asks for the article as **both PDF and DOCX**
(`SDIA2026_SAN-1_GROUP_13_article.pdf` and `.docx`). Overleaf produces the PDF
directly. LaTeX does not produce a faithful DOCX, so the Word version needs a
separate decision; see `docs/DEVIATIONS.md` entry D015.
