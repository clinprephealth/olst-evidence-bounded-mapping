# OLST Canonicalization Spec (O-CI-0) — v1

Normative rules for deterministic canonical JSON and content hashing for PhysioNet OLST-shaped inputs. Same logical trial + same rule version → byte-identical canonical JSON → identical SHA-256.

Companion: [`OLST_NC_DECISION_COMPATIBILITY_PLAN.md`](../../../docs/OLST_NC_DECISION_COMPATIBILITY_PLAN.md) §2.2, §2.2.1 O-CI-0.

---

## 1. Scope

v1 covers trial-level JSON fixtures produced **after** parsing native exports (MoCap, force plate, radar, metadata). Parsing rules for raw vendor files are filled in from single-participant profiling; structure-specific field names TBD until that profile is committed.

### 1.1 Pinned dataset release

`DATA_VERSION = "1.0"` — the PhysioNet OLST dataset release this spec is authored against.

Every fixture and `ReplayReport` carries `dataset_version`. If a fixture's `dataset_version` differs from the spec's `DATA_VERSION`, the harness emits a `UserWarning` and proceeds — never a silent pass. A future release (e.g. `1.1` with corrected captures) requires a spec amendment row in §9 and either a backfill of `DATA_VERSION` or an explicit cross-version compatibility statement.

---

## 2. Multi-attempt sessions (Finding 1)

Attempt count is **performance-dependent**: better balancers tend toward fewer, longer attempts; poorer balancers toward more, shorter attempts. **Trial count must not be used as a subject-level feature** without confounding performance.

**Rules:**

1. Each **attempt** is a separate canonical unit: one attempt → one fixture id → one content hash.
2. **No silent aggregation** across attempts in the canonical layer (no pooled stability duration, no session-level mean without an explicit, versioned aggregation step downstream of canonical bytes).
3. Session-level bundles, if present in source data, are represented as an ordered list of attempt records with stable ordering (e.g. by attempt index ascending); the canonical hash of a session bundle is the hash of that list’s canonical encoding, not a lossy merge.

**Fixture metadata (required for harness / EMU provenance):**

- `attempt_number` — 1-based index of this attempt within the session.
- `total_attempts_in_session` — count of attempts in that session for that trial protocol.

**Interpretation:** The same `stability_duration_ms` on attempt 1 vs attempt 6 is not interchangeable; EMU payloads must carry attempt provenance (see `olst_emu_schema_v1.yaml` for `gait_temporal_control`).

---

## 3. Known exclusions — data layer (Finding 2)

Gap visibility at ingest: excluded captures and participants are **listed explicitly**; implementations **must not** silently skip or emit partial canonical results for them.

### 3.1 KNOWN_CAPTURE_EXCLUSIONS (v1)

Capture ids follow the dataset's filename convention `{ParticipantID}_{MovementCode}_V{n}` (e.g. `12_MNTRL_V2`).

| Capture ID | Reason |
| ----------- | ------ |
| `12_MNTRL_V2` | Data collection error — capture missing. PhysioNet usage notes (Limitations) verbatim: *"one capture (12_MNTRL_V2) is missing due to a data collection error and should be excluded from analysis."* |

### 3.2 KNOWN_PARTICIPANT_EXCLUSIONS (v1)

*Empty in v1.* No whole-participant exclusions are published for the v1.0 release. The slot is kept so a future row addition is one line of code + one row of spec.

**Rules:**

1. If a fixture's `capture_id` matches `KNOWN_CAPTURE_EXCLUSIONS`, the harness **raises** `ExcludedCaptureError` (see `olst_replay_harness.py`) with capture id and reason. No canonical JSON, no EMUs, no partial hashes.
2. If a fixture's `participant_id` matches `KNOWN_PARTICIPANT_EXCLUSIONS`, the harness **raises** `ExcludedParticipantError` analogously.
3. The capture gate runs **before** the participant gate so that the most specific exclusion wins.
4. When new exclusions are published by the dataset maintainers, add a row to §3.1 or §3.2 and bump spec version or document an amendment date in §9.

**Fixture requirement:** Every fixture JSON **must** carry both `participant_id` and `capture_id` as separate, required top-level provenance fields. The harness reads them directly — no fallback key lists, no synthesis from filename parts. A fixture missing either field is a schema error (`FixtureSchemaError`), not a silent default.

---

## 4. Radar time alignment (Finding 3)

**Critical:** Radar alignment uses **row-specific** metadata, not a global nominal frame rate.

**Rules:**

1. Per-row `Seconds_per_Frame` (from dataset metadata) drives conversion between frame index and time.
2. Radar timestamps in canonical form are derived from **cumulative sum** of `Seconds_per_Frame` over rows from trial origin (or from documented trial-relative zero), **not** from `frame_index / nominal_sampling_rate` unless nominal rate is identical for every row and the usage notes explicitly allow it (they do not — use row metadata).
3. Implementations that use a single global rate for radar produce incorrect times and **different** canonical hashes — that is an O-CI-0 failure.

Document in each canonical radar block: the ordered list of `Seconds_per_Frame` or precomputed cumulative times from the same rule set so replay can be verified.

---

## 5. Cohort asymmetry — capture duration (Finding 4)

**20-second** OLST captures appear **only for older-participant cohort** in this dataset. Young-participant profiles do not use that duration symmetrically.

**Rules:**

1. Synthetic fixtures **must not** assign 20-second captures to young-participant profiles unless explicitly labeled as counterfactual test cases (adversarial / negative control), not as representative sampling.
2. Gold-standard mapping (execution Task 7): **stratify by age group**. Morse gait-related thresholds (e.g. 10-second clinical cutoff) have different distributions across cohorts; reports must acknowledge cohort, not treat N=32 as a single homogeneous population.

---

## 6. Parsing and normalization

Concrete rules from the participant 01 profile (`PARTICIPANT_01_PROFILE.md`). Companion to that file: this section is the normative spec; the profile is the source of truth for what the dataset actually contains.

### 6.1 MoCap (`Raw/MOCAP/<NN>/{capture_id}_MC_V{n}_pos.csv`)

- Sampling rate: 100 Hz, deterministic — declare as canonical rate.
- Joint columns are `{Joint}_pos_{X,Y,Z}` triples (Actuator, Wrist_R/L, Elbow_R/L, Shoulder_R/L, Upper_Back, Lower_Back, Chest, Belly, Hip_R/L_Ant, Hip_R/L_Post, Knee_R/L, Ankle_R/L). The marker-name → joint map is `Metadata/MOCAP_Markers_Locations.csv`.
- Position units: input millimeters, canonical millimeters (no conversion).
- Time: input seconds from MoCap clock; canonical milliseconds from trial start. **Trial-start = `MOCAP_Start_Time` from `OLST_Attempts.csv`**, not zero.
- The `participant_id` column on each row is redundant with the file path; the canonical fixture takes the value from the path/metadata, not the row.

### 6.2 Force plate (`Raw/ForcePlate/<NN>/{capture_id}_FP_V{n}_{left,right}.csv`)

- Sampling rate: 1200 Hz.
- Bilateral separation: two CSVs per capture (`_left.csv`, `_right.csv`); the canonical pipeline reads both and emits `force_plate.{left,right}_pct` derived in §6.4.
- Force columns `Force_X, Force_Y, Force_Z` are in **Newtons** (raw, not body-weight normalized). Canonical: Newtons.
- CoP columns `COP_X, COP_Y, COP_Z` are in **millimeters**; `COP_speed` is in **millimeters per second**.
- Time: input seconds from FP clock; canonical milliseconds from trial start, aligned to the same trial-start as MoCap.

### 6.3 Radar (`Processed/Radar_RDMs/<NN>/...`)

- Pre-processed Range-Doppler Maps (`.mat`). Raw radar IQ is not in v1.0 of the dataset.
- Time alignment: per spec §4, use `Seconds_per_Frame` from `OLST_Attempts.csv` for the capture, **not** a nominal rate. The column is per-capture in this dataset (one value per capture); the canonical-time derivation is `time_ms[i] = i * Seconds_per_Frame * 1000` if the dataset ever publishes per-row values, the cumulative-sum form remains correct (sum of equal increments equals product). The harness output records the `Seconds_per_Frame` value used so a different rate is a different canonical hash.

### 6.4 Stability-phase derivation

- `stability_phase.start_ms` = `t_stable * 1000` (rounded to int).
- `stability_phase.end_ms` = `t_break * 1000`, except `is_attempt_final == True` **or `t_break` empty**, where `end_ms = t_end * 1000` (the participant ended the trial rather than transitioning to the next attempt; five non-final rows in release 1.0 have `t_stable` but no `t_break`).
- `stability_phase.event_label_source` = constant `"OLST_Attempts.csv@v1.0"`.
- **Absent stable phase (v1.3).** When `t_stable` is empty the participant never reached stability. The fixture is still built: `stability_phase` is `null` with `stability_phase__missing_reason`, and `force_plate` is `null` with `force_plate__missing_reason` (CoP and load metrics are defined over the stable window only). Nothing is imputed; the gap is declared in the fixture so a capture-level aggregate can name the attempt. 152 kept attempts in release 1.0 are in this state.
- `force_plate.mean_cop_displacement_mm` = mean of `sqrt(COP_X² + COP_Y²)` over the stability phase.
- `force_plate.sway_area_mm2` = 95% confidence-ellipse area of the CoP scatter over the stability phase, rule v1.
- `force_plate.left_pct` = `mean(Force_Z_left) / (mean(Force_Z_left) + mean(Force_Z_right)) * 100` over the stability phase; `right_pct` symmetrically; `asymmetry_index = abs(left_pct - right_pct)` (computed downstream in the EMU layer).

### 6.5 Cohort assignment

- `age_cohort` from `Metadata/Participant_Demographics.csv`: `young` if age ≤ 32, `older` if age ≥ 64.
- 20-second captures appear only for the older cohort (spec §5). Synthetic fixtures must respect this; gold-standard reports must stratify.

### 6.6 Stance-phase derivation and acquisition protocol (v1.3)

Added 2026-09-09 per `protocol/AMENDMENT_2026-09-09_D1_RESOLUTION.md` (D1 resolution, D4a).

- `stance_phase.foot_up_ms` = `t_foot_up * 1000`; `stance_phase.touchdown_ms` = `t_end * 1000`; `stance_phase.event_label_source` = `"OLST_Attempts.csv@v1.0"`. This is the one-legged stance interval (foot-lift to foot-touchdown per the dataset README). It is emitted whenever both events are present (all 1238 kept attempts in release 1.0). The EMU layer derives `gait_temporal_control.stance_duration_ms = touchdown_ms − foot_up_ms` from it.
- The stable phase (§6.4) is a sub-window of the stance phase and feeds the CoP EMUs only. The two windows are never substituted for one another.
- **Movement codes and the observation ceiling.** The capture id's movement code identifies the acquisition protocol. `acquisition_protocol` is carried in the fixture with its source named:

| Movement code | Base leg (`trial_leg`) | Protocol | `observation_ceiling_ms` | `observation_ceiling_source` |
|---|---|---|---|---|
| `MNTRL` | left | Mountain-to-Tree, cued short (4 s) trial | `4000` (v1.4; `null` in v1.3) | Copeland D et al. Gait Posture 2026;126:110108 (doi 10.1016/j.gaitpost.2026.110108): data collected "during short (4 s) and long (20 s) OLST trials". The README does not state the cue. |
| `MNTRR` | right | Mountain-to-Tree, cued short (4 s) trial | `4000` (v1.4; `null` in v1.3) | as above |
| `TRLGL` | left | 20-second sustained-balance trial, older cohort only | `20000` | README: "older adult participants completed longer 20-second trials"; corroborated by Copeland et al. 2026 ("long (20 s)") |
| `TRLGR` | right | 20-second sustained-balance trial, older cohort only | `20000` | as above |

  Base leg for `TRLG*` was verified from force-plate vertical load (amendment A2), not assumed from the letter. A ceiling is carried only with a published source; it is never inferred from the duration distribution and written back into the fixture. Observed maxima exceed the nominal cue under both protocols (`MNTR*` 6.34 s, `TRLG*` 21.31 s): the ceiling is the instructed duration, not a hard cap, and the D4a rule treats it as the longest duration the protocol asked the participant to produce. **v1.4 (amendment A14):** the `MNTR*` ceiling moved from `null` (spec v1.3, executed in A11/A13) to `4000` on the strength of the companion paper. A 4000 ms ceiling lies below every duration threshold (5000, 10000), so the D4a outcome for `MNTR*` is `protocol_censored` in both versions; what changes is that the fixture now carries a sourced number instead of a declared gap. The v1.3 fixtures and runs are preserved in the store as their own execution context.
- **Attempt-window integrity.** Attempts within a capture are ordered by `t_foot_up` for temporal analyses. `attempt_number` remains the dataset's `an`. Overlapping stance windows within a capture (release 1.0: `47_TRLGL_V4` only) are a declared aggregate-level non-evaluable condition, not a data edit.

### 6.7 Release-level source gaps (v1.3)

- `Raw/ForcePlate/35/35_MNTRL_FP_V4_{left,right}.csv` are referenced by `Metadata/OLST_Attempts.csv` (capture `35_MNTRL_V4`, 4 attempts) but absent from `SHA256SUMS.txt`. The loader refuses to build those fixtures (no source hash for the pointer). Recorded here; not a maintainer-published exclusion, so not in §3.1.

### 6.8 Global conventions

- Lexicographic key order in JSON objects.
- Floats: 6 decimal places. No `NaN` / `Inf` — use explicit `null` plus `<field>__missing_reason` where needed.
- Trial-internal times: milliseconds from trial start (the trial start is the MoCap clock zero referenced by `MOCAP_Start_Time`).
- Session metadata timestamps: ISO 8601 UTC where applicable.
- Canonical JSON byte-stable per spec §7.

---

## 7. Content hashes and identifiers

Three distinct identifiers, all SHA-256 hex digests, computed by the harness:

- **`fixture_id`** — SHA-256 of the UTF-8-encoded fixture JSON bytes **as read from disk**, with no normalization. Identifies the specific JSON we ran. Different from `output_hash`: a fixture with extra whitespace produces a different `fixture_id` but (assuming canonicalization absorbs the whitespace) the same `output_hash`.
- **`output_hash`** — SHA-256 over UTF-8 encoding of the **canonical JSON** of the harness output. Scope: `{emu_outputs, criterion_evaluations, non_evaluable_criteria, traceability, mapping_spec_version, dataset_version}` with stable key order per §6, lists sorted deterministically. **Includes `traceability`** — entries (`emu_id`, `payload_hash`, `rule_version`) are all deterministic given identical inputs; excluding them would let two runs produce identical `output_hash` while diverging on which evidence pointers were emitted, silently violating NC-0 traceability.
- **EMU `payload_hash`** — SHA-256 over canonical JSON of an EMU payload only (no provenance), used to anchor traceability entries.

`capture_id` and `participant_id` are not hashes — they are dataset provenance strings read directly from the fixture.

No trailing newline on any canonical-JSON-derived hash unless specified.

---

## 8. Versioning

| Version | Date | Notes |
| ------- | ---- | ----- |
| v1 | 2026-05 | Task 1 findings: attempts, exclusion `12_MNTRL_V2`, radar `Seconds_per_Frame`, cohort duration asymmetry. |
| v1.1 | 2026-05-04 | Phase 0 corrections: `KNOWN_EXCLUSIONS` → `KNOWN_CAPTURE_EXCLUSIONS` + `KNOWN_PARTICIPANT_EXCLUSIONS` (capture-level vs participant-level); `DATA_VERSION = "1.0"` pinned; required fixture fields `participant_id` + `capture_id`; `output_hash` scope formalized to include `traceability`. No semantic change to Task 1 findings. |
| v1.2 | 2026-05-04 | §6 filled from participant-01 profile: concrete columns / units for MoCap, force plate, radar; stability-phase derivation rules; cohort assignment rule. `event_label_source = "OLST_Attempts.csv@v1.0"` is the canonical source of attempt-level event timing. |
| v1.3 | 2026-09-09 | D1 resolution (amendment A1–A6): §6.4 absent-stable-phase fixtures and the `t_break`-empty fallback made explicit; new §6.6 stance phase (`t_foot_up → t_end`), movement-code glossary incl. `TRLGL`/`TRLGR`, `acquisition_protocol` with observation ceiling by movement code, attempt-window integrity; new §6.7 release-level source gap `35_MNTRL_V4`. Thresholds, exclusions, and the v1 criterion map are unchanged. Changes `spec_id`; recorded as the pre-v1-full-corpus freeze. |
| v1.4 | 2026-09-10 | Source-metadata amendment (A14): §6.6 `MNTR*` `observation_ceiling_ms` `null` → `4000`, source Copeland et al. Gait Posture 2026 ("short (4 s) and long (20 s) OLST trials"); `TRLG*` unchanged. Not a clinical-map change; harness and maps untouched. Changes `spec_id` and the `MNTR*` fixture bytes only. |

---

## 9. Amendments

Add rows to §3 for new exclusions; extend §6 with concrete field names after PhysioNet directory profile is recorded.

- **2026-09-09** — `../protocol/AMENDMENT_2026-09-09_D1_RESOLUTION.md`: D1 resolved as construct correction with protocol censoring (D4a) and attempt-window integrity (D2a); spec v1.3.
- **2026-09-10** — same file, A14: `MNTR*` observation ceiling sourced to the companion paper (4000 ms); spec v1.4.
