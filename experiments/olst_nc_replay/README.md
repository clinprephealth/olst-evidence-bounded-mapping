# OLST / NC replay benchmark

Deterministic, content-addressed mapping of the public PhysioNet One-Legged
Stand Test dataset (motion capture + force plate + radar, release 1.0,
DOI 10.13026/46hn-6b25) onto clinical-framework criteria, with explicit
non-evaluable reasons instead of imputation. The contribution is the methods
artifact. Nothing here predicts falls or is intended for clinical use.

The complete experimental record, including every post-freeze decision with
its date and the commit that executed it, is
[`protocol/AMENDMENT_2026-09-09_D1_RESOLUTION.md`](protocol/AMENDMENT_2026-09-09_D1_RESOLUTION.md)
(sections A1–A15). The frozen pre-registration is
[`protocol/STEP_0.5_FREEZE.md`](protocol/STEP_0.5_FREEZE.md) and the two
frozen drafts beside it. This README is the operational guide; the amendment
is the laboratory record.

## Layout

| Path | Purpose |
|---|---|
| `olst_replay_harness.py` | `run(fixture_path, mapping_spec_version) -> ReplayReport`. Canonicalization, EMU derivation, criterion-map evaluation, `run_id` / `output_hash`. Its own SHA-256 is `HARNESS_VERSION`. |
| `olst_real_loader.py` | Builds one fixture per attempt from the PhysioNet CSVs; pins source-file digests from `SHA256SUMS.txt`. |
| `olst_capture_aggregate.py` | Capture-level best-of-attempts aggregate as declared in a map's `aggregation` block. |
| `lakehouse.py` | Content-addressed store: six JSONL streams, `ingest` / `recall` / `verify_replay`. |
| `olst_naive_baseline.py` | Threshold-only comparator, no evidence pointers. |
| `_run_full_corpus.py` | Step 1 / Step 2 driver: verifies every source file against the manifest, builds fixtures, runs N times, ingests, aggregates, writes a summary artifact. |
| `specs/OLST_CANONICALIZATION_SPEC_v1.md` | Canonicalization spec; its SHA-256 is `spec_id`. Versions v1.3 and v1.4 are the executed ones. |
| `specs/NC_CRITERION_EMU_MAP_*.json` | Criterion maps: `v1`, `v2`, `v2.1` (Morse Fall Scale), `berg_v1` (Berg Balance Scale). Each file's SHA-256 is its `criterion_map_id`. Maps are never edited after execution; a change is a new file. |
| `fixtures/*.json` | 19 synthetic fixtures + golden `fixture_id` / `output_hash` per map version. |
| `fixtures/real/` | The 10 pilot fixtures (May 2026, Python 3.9, pre-v1.3 shape). |
| `fixtures/real_full/` | 1233 real fixtures, spec v1.3 (MNTR ceiling unpublished → `null`). |
| `fixtures/real_full_spec1.4/` | 1233 real fixtures, spec v1.4 (MNTR ceiling 4000 ms, sourced). |
| `../../artifacts/olst_lakehouse/` | Committed store snapshot: 9892 runs, 1328 capture aggregates, 2037 distinct fixture texts. |
| `../../artifacts/olst_full_corpus_*.json` | One summary artifact per execution context (below). |
| `../../tests/test_olst_*.py` | 165 tests. The store tests replay stored fixtures and need no PhysioNet data. |

## Execution contexts in the committed store

Every run is identified by `run_id = SHA-256(fixture_id, dataset_version,
mapping_spec_version, spec_id, criterion_map_id, harness_version)`. The store
holds nine contexts; the digests below are the first 8 hex characters.

| Map | `harness_version` | `spec_id` | `criterion_map_id` | Runs | What it is | Artifact |
|---|---|---|---|---|---|---|
| v1 | `a6f80c42` | `04e04b61` | `2267d7c9` | 28 | May 2026 pilot: 19 synthetic + 10 real − 1 excluded | `olst_nc_gold_standard_v1.json` |
| v1 | `193dba29` | `9de0a3da` | `2267d7c9` | 1233 | Step 1, full corpus, spec v1.3 | `olst_full_corpus_v1__harness_193dba29.json` |
| v1 | `f718e4ad` | `9de0a3da` | `2267d7c9` | 1233 | Step 2 rerun under the v2.1-capable harness; reproduces Step 1 output hashes 1233/1233 | `olst_full_corpus_v1.json` |
| v2 | `f718e4ad` | `9de0a3da` | `d4ac623a` | 1233 | Frozen v2: stance construct, protocol censoring, v1 sway gate retained | `olst_full_corpus_v2.json` |
| v2.1 | `f718e4ad` | `9de0a3da` | `b284beb3` | 1233 | Sway loses categorical authority, keeps evidentiary standing | `olst_full_corpus_v2.1.json` |
| v1 / v2 / v2.1 | `f718e4ad` | `4e26b694` | as above | 3 × 1233 | Spec v1.4: MNTR ceiling sourced (4 s). Same labels, new evidence identity | `olst_full_corpus_{v1,v2,v2.1}__spec1.4.json` |
| berg_v1 | `98dc66fb` | `4e26b694` | `b9d2cfbc` | 1233 | Berg Balance Scale; needed a generic ordinal rule type in the harness (+86/−7 lines) | `olst_full_corpus_berg_v1__spec1.4.json` |

The v1 map bytes are unchanged since the pilot. `v1`, `v2`, `v2.1` differ
only in map bytes when compared under one `harness_version`; the Berg run
differs in map and harness, and that harness difference is a reported result
(amendment A15), not an oversight.

## Reproduce

Python 3.9 or later, standard library only for the harness; `pytest` for the
tests. Run from the repository root (the `pytest.ini` sets `pythonpath = .`).

```bash
python -m pytest tests/test_olst_nc_replay.py tests/test_olst_v13_stance_protocol.py tests/test_olst_v2_map.py tests/test_olst_v21_map.py tests/test_olst_v14_ceiling_source.py tests/test_olst_berg_map.py tests/test_olst_full_corpus_store.py -q
```

That verifies the golden hashes for every map on the synthetic suite, the
store-level identity claims across execution contexts, and bit-for-bit
replay of a seeded sample of stored runs. To replay every stored run:

```bash
OLST_FULL_STORE_VERIFY=1 python -m pytest tests/test_olst_full_corpus_store.py::test_stored_runs_replay_bit_for_bit -q
```

To re-execute a full-corpus run you need the PhysioNet data (below). Each
invocation verifies every referenced source file against `SHA256SUMS.txt`
before building anything and refuses to run on an incomplete or mismatched
mirror. Ingest is idempotent, so re-running a context appends nothing.

```bash
PYTHONPATH=. python -m experiments.olst_nc_replay._run_full_corpus --mapping-spec-version v2.1 --determinism-n 100 --fixtures-dir experiments/olst_nc_replay/fixtures/real_full_spec1.4 --artifact-suffix __spec1.4
```

Use `--fixtures-dir experiments/olst_nc_replay/fixtures/real_full` without a
suffix for the spec v1.3 contexts (check out the spec at the v1.3 commit
recorded in the amendment, since the spec file's digest enters `run_id`).

## Data you must obtain independently

The PhysioNet release is not redistributed here. Fixtures contain derived
numbers and the manifest digests of the files they came from, never raw
samples. To rebuild fixtures you need, under
`data/physionet_olst/olst-mocap-forceplate-radar/1.0/` (gitignored):

- `Metadata/OLST_Attempts.csv`, `Metadata/Participant_Demographics.csv`
- `Raw/MOCAP/<NN>/*_pos.csv` and `Raw/ForcePlate/<NN>/*_left.csv`, `*_right.csv` for all 32 participants (about 4.2 GB)
- `SHA256SUMS.txt`, `README.txt`

Radar range-Doppler maps and the QTM project are not used. Capture
`12_MNTRL_V2` is excluded per the dataset's usage notes; capture
`35_MNTRL_V4` has no force-plate files in the release manifest and is
reported as `source_missing_upstream`.

Cite the dataset as PhysioNet requires: Copeland D, Zhang X, Linton E,
Mori B, Lugaro H, Anthony BW. One-Legged Stand Test: Synchronized Motion
Capture, Force Plate, and Radar Dataset for Fall-Risk. *Sci Data* 2026;13.
doi 10.1038/s41597-026-06831-1.

## Notes on the record

Machine-local paths in the frozen preregistration record
(`protocol/STEP_0.5_FREEZE.md`) are retained as historical metadata and are
not required for reproduction. `paper/paper.md` is the May 2026 manuscript
superseded by the frozen draft in `protocol/` and the executed draft in
`paper/`. The literature checkpoint in `paper/literature_review/` is a
structured novelty scan with logged queries, not a systematic review.
