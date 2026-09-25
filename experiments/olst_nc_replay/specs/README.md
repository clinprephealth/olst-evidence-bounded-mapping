# Specs

| File | Description |
|------|-------------|
| `OLST_CANONICALIZATION_SPEC_v1.md` | O-CI-0: `DATA_VERSION`, attempts, capture/participant exclusions, radar time, cohort notes (+ parsing TBD after profile) |
| `olst_emu_schema_v1.yaml` | EMU types + provenance (`attempt_number`, `total_attempts_in_session`, …). Documentation only — not parsed by the harness. |
| `NC_CRITERION_EMU_MAP_v1.json` | Morse criterion ↔ EMU derivability, v1 (frozen; bytes unchanged since the pilot). JSON (not YAML) so the harness stays stdlib-only. |
| `NC_CRITERION_EMU_MAP_<version>.json` | Further map versions are selected by `run(..., mapping_spec_version=<version>)`; an unknown version raises. A map may carry per-criterion `rule` blocks and an `aggregation` block (see `olst_capture_aggregate.py`). |
| `PARTICIPANT_01_PROFILE.md` | Phase 1 profile of participant `01` (vendor field names, units, sampling rates) — add after the partial PhysioNet download. |

Extend §6 of the canonicalization spec with concrete field names after single-participant directory profiling.
