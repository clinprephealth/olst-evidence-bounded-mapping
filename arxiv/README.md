# arXiv upload — OLST paper

**Title.** Evidence Availability Is Not Evidence Entitlement: Replayable, Evidence-Bounded Mapping of Multimodal Biomechanical Data to Clinical Assessment Criteria

**Authors.** Michael P. Ryder, DO (Independent researcher) <michaelryder.do@gmail.com>

**Primary category.** cs.SE
**Cross-lists.** q-bio.QM, cs.CY

**License on arXiv.** Submitter's choice. Recommended: Creative Commons Attribution (CC BY 4.0). arXiv also offers CC BY-SA, CC BY-NC-SA, CC BY-NC-ND, CC0, and its own perpetual non-exclusive license; the selected license is irrevocable.

**Citations (fixed 2026-09-26).** `arxiv/main.tex` uses `\citep{...}` (Morse 1989 is `\citep{morse1989}`). Compiled from `arxiv-source/` the PDF has a References section beginning with Morse, Morse & Tylko 1989. No leftover Markdown `[key]` citation keys remain.

**Comments line.** 20 pages, 4 figures. Methods artifact on the public PhysioNet OLST corpus. Nothing here predicts falls or is intended for clinical use. Code and store snapshot: [GitHub URL]. Archival DOI: [Zenodo, after v0.1.1].

**Abstract.** Paste the abstract from the executed manuscript (first paragraph after `## Abstract`). Plain text for the metadata form.

## Upload

Upload `arxiv-source.tar.gz`. Top-level file: `main.tex`. Figures are PDF. Bibliography is `refs.bib`.

Do not include the lakehouse JSONL snapshot or the 1,233 real fixtures in the arXiv source (too large; they belong on GitHub/Zenodo). The paper source plus PDF figures is enough for the abstract page; the repo is the artifact.

## After announcement

Same as the tabular paper: write the arXiv id into `CITATION.cff`, mint Zenodo from the GitHub Release, replace as version 2. Journal submission is **not** required for public existence.
