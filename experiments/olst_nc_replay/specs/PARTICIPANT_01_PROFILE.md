# Participant 01 — Single-Participant Profile (Phase 1)

Profile of the PhysioNet OLST dataset (release `1.0`) recorded against `data/physionet_olst/olst-mocap-forceplate-radar/1.0/` after a partial mirror of participant `01` plus dataset-wide `Metadata/`, `Code/`, and `README.txt`. ~82 MB total.

## Source layout

```
1.0/
├── Code/                                 utility notebook viz_OLST_attempt.ipynb
├── Metadata/
│   ├── OLST_Attempts.csv                 attempt-level event labels (system of record)
│   ├── Participant_Demographics.csv      age cohort, height, weight, ...
│   ├── MOCAP_Markers_Locations.csv       joint-name → marker-location map
│   ├── MOCAP_Settings.xlsx               capture rate, marker count
│   ├── ForcePlate_Settings.xlsx          channel/unit settings
│   └── FMCWRadar_Settings.xlsx           radar config
├── Raw/MOCAP/<NN>/                       per-participant MoCap CSVs
├── Raw/ForcePlate/<NN>/                  per-participant force-plate CSVs (split per side)
├── Processed/Radar_RDMs/<NN>/            preprocessed Range-Doppler Maps (.mat)
└── OLST_QTM/                             full Qualisys QTM project
```

Participant directories are zero-padded numeric (`01`–`56`, with non-contiguous gaps; the published cohort is N=32). The `12_MNTRL_V2` capture in `KNOWN_CAPTURE_EXCLUSIONS` (spec §3.1) is missing from this layout per PhysioNet usage notes.

## File naming

`{ParticipantID}_{MovementCode}_{Modality}_V{n}{suffix}` where:

- `ParticipantID` — `01`–`56`.
- `MovementCode` — `MNTRL` (Mountain-to-Tree, left foot base) or `MNTRR` (right foot base).
- `Modality` — `MC` (motion capture), `FP` (force plate), `RR` (radar recording). The capture id used in usage notes (`12_MNTRL_V2`) and in `KNOWN_CAPTURE_EXCLUSIONS` strips the modality token: `{ParticipantID}_{MovementCode}_V{n}`.
- `V{n}` — version, typically `V1`, `V2`, `V3`. Each combination has 3 attempts (`an1`–`an3`) inside.
- `suffix` — `_pos.csv` for MoCap; `_left.csv` / `_right.csv` for force plate (one CSV per plate); none for radar `.mat`.

## Modality details

### Motion capture (`Raw/MOCAP/01/01_MNTRR_MC_V1_pos.csv`)

- Sampling rate: **100 Hz** (4001 samples per ~40 s capture).
- Columns: `frame, time, participant_id, {Joint}_pos_{X,Y,Z}` for ~25 joints (Actuator, Wrist_R/L, Elbow_R/L, Shoulder_R/L, Upper_Back, Lower_Back, Chest, Belly, Hip_R/L_Ant, Hip_R/L_Post, Knee_R/L, Ankle_R/L). Marker map lives in `Metadata/MOCAP_Markers_Locations.csv`.
- Position units: **millimeters**; time units: **seconds** from MoCap-clock zero.
- `participant_id` is repeated as a string column on every row.

### Force plate (`Raw/ForcePlate/01/01_MNTRR_FP_V1_{left,right}.csv`)

- Sampling rate: **1200 Hz** (48001 samples per ~40 s capture). Two CSVs per capture, one per plate.
- Columns: `SAMPLE, time, Force_X, Force_Y, Force_Z, Moment_X, Moment_Y, Moment_Z, COP_X, COP_Y, COP_Z, COP_speed`.
- **Force is in Newtons** (raw, not body-weight normalized). Sample data: during one-legged stand on right plate, left plate Force_Z values are 275–280 N (residual contact + sensor noise); on the stance plate values reach hundreds of Newtons. No BW conversion factor in the raw export.
- CoP units: **millimeters**; CoP_speed: **mm/s**.

### Radar (`Processed/Radar_RDMs/01/...`)

- Processed Range-Doppler Maps in MATLAB `.mat` format (cropped + annotated per capture). Raw radar IQ not provided in this release.
- Sampling rate: ~27.6 Hz nominal but **never use a global rate**: the per-capture `Seconds_per_Frame` column in `OLST_Attempts.csv` is the system of record (values vary capture-to-capture: 0.0365, 0.03664, 0.03651, …). Per spec §4 the time conversion is `time = cumsum(Seconds_per_Frame)` from trial origin.

### Event labels (`Metadata/OLST_Attempts.csv`) — authoritative

One row per **attempt** (not capture). The harness's `attempt_number` and `total_attempts_in_session` map to this table directly.

| Column | Meaning |
| --- | --- |
| `OLST_attempt_id` | `{capture_id}_an{n}` — primary key |
| `RADAR_capture` | The capture id that this attempt belongs to (in `*_RR_*` form) |
| `MOCAP_Start_Time`, `MOCAP_End_Time` | Capture-relative seconds (MoCap clock) |
| `RADAR_Start_Frame`, `RADAR_End_Frame` | Radar frame indices for the capture |
| `Seconds_per_Frame` | Per-capture radar frame duration |
| `an` | Attempt number, 1-based |
| `is_attempt_final` | True for the last attempt in the capture (the others end at `t_break`; the last ends at `t_end` because the participant stops) |
| `t_foot_up`, `t_stable`, `t_break`, `t_end` | Event times in MoCap-clock seconds. Stability phase = `[t_stable, t_break]` (or `[t_stable, t_end]` for the final attempt) |
| `frame_foot_up`, `frame_stable`, `frame_break`, `frame_end` | Same events in radar frame indices |

For participant 01, captures are `01_MNTRL_RR_V1..V3` and `01_MNTRR_RR_V1..V3` — six captures × three attempts = 18 attempts per participant. `total_attempts_in_session` = 3 for every attempt within a single capture.

## Spec mapping

- `attempt_number` → `OLST_Attempts.csv:an`
- `total_attempts_in_session` → count of rows per `RADAR_capture` (3 for participant 01; the spec must not assume this is universal)
- `stability_phase.start_ms` → `t_stable * 1000` (rounded to int)
- `stability_phase.end_ms` → `t_break * 1000` (final attempt: `t_end * 1000`)
- `stability_phase.event_label_source` → fixed string `"OLST_Attempts.csv@v1.0"`
- `force_plate.mean_cop_displacement_mm` → mean(sqrt(COP_X² + COP_Y²)) over stability phase
- `force_plate.sway_area_mm2` → 95% confidence-ellipse area of CoP scatter over stability phase (rule v1)
- `force_plate.stance_duration_ms` → end_ms − start_ms (consistent with `t_break − t_stable`)
- `force_plate.left_pct`, `right_pct` → mean(Force_Z left) / (mean(Force_Z left) + mean(Force_Z right)) × 100, computed over stability phase. Unit normalization is not required when both plates report in Newtons.
- `trial_leg` → derived from `MovementCode`: `MNTRL` → `"left"`, `MNTRR` → `"right"`.
- `age_cohort` → from `Metadata/Participant_Demographics.csv`: `young` if age ≤ 32, `older` if age ≥ 64. The 20s captures (longer-trial cohort) are exclusively older — gate at fixture-build time.

The spec §6 placeholder is now filled (see `OLST_CANONICALIZATION_SPEC_v1.md` v1.1 amendment row).
