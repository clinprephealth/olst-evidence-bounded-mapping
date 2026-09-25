# OLST / NC replay benchmark — public research release

Deterministic, content-addressed mapping of the public PhysioNet One-Legged
Stand Test dataset onto clinical-framework criteria with explicit
non-evaluable reasons and protocol censoring instead of imputation.

Start at `experiments/olst_nc_replay/README.md` (operational guide) and
`experiments/olst_nc_replay/protocol/AMENDMENT_2026-09-09_D1_RESOLUTION.md`
(the dated laboratory record). The executed manuscript draft is
`experiments/olst_nc_replay/paper/OLST_MANUSCRIPT_EXECUTED_v3.md`.

Verify the artifact without the dataset:

    python -m pytest -q

Nothing here predicts falls or is intended for clinical use. The PhysioNet
dataset is not redistributed; see the operational guide for what to obtain
and how it is verified.
