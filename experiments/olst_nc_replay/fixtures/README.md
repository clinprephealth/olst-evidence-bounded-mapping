# Fixtures

Place synthetic OLST-shaped JSON here after `../specs/OLST_CANONICALIZATION_SPEC_v1.md` matches real export fields.

## Required top-level provenance fields

Every fixture **must** include these fields:

- `dataset_version` — string, e.g. `"1.0"`. Matches `DATASET_VERSION` in `olst_replay_harness.py`; mismatch produces a `UserWarning` (not a silent pass).
- `participant_id` — string, e.g. `"01"`. Read directly by the harness; no fallback keys.
- `capture_id` — string of the form `{ParticipantID}_{MovementCode}_V{n}`, e.g. `"01_MNTRR_V2"`. Read directly; no synthesis from filename parts.
- `attempt_number`, `total_attempts_in_session` — integers on each attempt-level record. No silent session-level merges.

Missing any of `participant_id`, `capture_id`, or `dataset_version` raises `FixtureSchemaError`.

## Optional v1.3 fields (real fixtures; amendment 2026-09-09)

- `stance_phase` — `{foot_up_ms, touchdown_ms, event_label_source}`, the `t_foot_up → t_end` window (spec §6.6). Feeds `gait_temporal_control.stance_duration_ms`.
- `acquisition_protocol` — `{protocol_code, observation_ceiling_ms, observation_ceiling_source}` by movement code (spec §6.6). `observation_ceiling_ms` is `null` when the release does not publish the cued duration.
- `stability_phase` / `force_plate` may be `null` with a sibling `<field>__missing_reason` when the attempt has no `t_stable` (spec §6.4).

Synthetic fixtures in this directory do not carry these fields; the harness adds nothing to their EMUs, which is what keeps `golden_output_hashes_v1.json` valid. `real/` holds the 10 pilot fixtures as built in May 2026 (Python 3.9, pre-v1.3 shape); `real_full/` is written by `_run_full_corpus.py`.

## Exclusion rules

- Never use `12_MNTRL_V2` as a `capture_id` outside the negative-control test that asserts `ExcludedCaptureError` — per PhysioNet usage notes that capture is missing.
- Participant `12` with any other `capture_id` is a perfectly valid fixture.

## Cohort rules

- Do **not** model 20-second captures for young-participant profile fixtures unless explicitly an adversarial counterfactual (see canonicalization spec §5).

## Identifiers and golden vectors

Fixtures **do not** carry a `fixture_id` field — that's computed by the harness as SHA-256 of the fixture content at load time. Fixture filenames on disk (e.g. `clean_young_01.json`, `borderline_10s_cutoff_01.json`) are descriptive and have no governance role.

`golden_output_hashes_v1.json` records `{filename: {fixture_id, output_hash}}` for every committed fixture; the test suite asserts both hashes on every run, so a fixture-content drift and an output drift are both detected.
