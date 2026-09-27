# Evidence-bounded mapping of the PhysioNet OLST corpus

Replay-stable, criterion-level evaluation of clinical assessment frameworks
from the public One-Legged Stand Test dataset, with explicit non-evaluable
reasons and protocol censoring instead of imputation.

Manuscript: `experiments/olst_nc_replay/paper/OLST_MANUSCRIPT_EXECUTED_v3.md`
(and the arXiv LaTeX in `arxiv/`). Operational guide:
`experiments/olst_nc_replay/README.md`. Laboratory record:
`experiments/olst_nc_replay/protocol/AMENDMENT_2026-09-09_D1_RESOLUTION.md`.

```bash
python -m pytest -q
```

Nothing here predicts falls or is intended for clinical use. The PhysioNet
waveforms are not redistributed. The frozen pre-submission plan in
`protocol/` retains a few historical lines that name internal projects
and a local filesystem path. Those lines are kept on purpose: they are
the preregistration record, and sanitizing them after the fact would
make that record less authentic. They are not kernel code, and they are
not the public scientific claim.

## Licence

- Code and tests: Apache-2.0
- Manuscript and original figures: CC BY 4.0
- Dataset-derived fixtures, store snapshot, and result files: CC BY 4.0,
  with attribution to the PhysioNet OLST dataset (Copeland et al.;
  DOI 10.13026/46hn-6b25)
