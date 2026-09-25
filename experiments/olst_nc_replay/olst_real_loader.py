"""Load real PhysioNet OLST data into the canonical fixture shape.

For each (participant, capture, attempt) tuple, read:
  - Metadata/OLST_Attempts.csv          → event timing, attempt number
  - Metadata/Participant_Demographics.csv → age cohort
  - Raw/MOCAP/<NN>/<capture>_MC_V<n>_pos.csv  (only header for shape)
  - Raw/ForcePlate/<NN>/<capture>_FP_V<n>_left.csv
  - Raw/ForcePlate/<NN>/<capture>_FP_V<n>_right.csv

Emit a fixture JSON dict matching the spec's required schema:
  dataset_version, participant_id, capture_id, attempt_number,
  total_attempts_in_session, trial_leg, age_cohort, stability_phase,
  force_plate, normalization_rule_version, derivation_rule_version.

CoP and force-plate metrics are derived per spec §6.4 over the stability
phase of the requested attempt only — not the whole capture.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_DATASET_VERSION = "1.0"


@dataclass(frozen=True)
class _AttemptRow:
    olst_attempt_id: str
    radar_capture: str
    mocap_start_time: float
    mocap_end_time: float
    seconds_per_frame: float
    an: int
    is_attempt_final: bool
    t_foot_up: float | None
    t_stable: float | None
    t_break: float | None
    t_end: float


def _parse_sha256sums(path: Path) -> dict[str, str]:
    """Return {relative_path: sha256_hex} from a PhysioNet SHA256SUMS.txt file.

    Format: "<sha256> <relative_path>" per line.
    """
    out: dict[str, str] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split(" ", 1)
            if len(parts) != 2:
                continue
            digest, rel = parts
            out[rel.strip()] = digest.strip()
    return out


def _parse_demographics(path: Path) -> dict[str, str]:
    """Return participant_id (zero-padded "NN") -> age cohort ("young"/"older")."""
    out: dict[str, str] = {}
    with path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row["Participant_ID"].strip().zfill(2)
            cohort = "young" if row["Age_Group"].strip().lower().startswith("y") else "older"
            out[pid] = cohort
    return out


def _opt_float(raw: str) -> float | None:
    raw = raw.strip()
    return float(raw) if raw else None


def _parse_attempts(path: Path) -> list[_AttemptRow]:
    rows: list[_AttemptRow] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(
                _AttemptRow(
                    olst_attempt_id=r["OLST_attempt_id"].strip(),
                    radar_capture=r["RADAR_capture"].strip(),
                    mocap_start_time=float(r["MOCAP_Start_Time"]),
                    mocap_end_time=float(r["MOCAP_End_Time"]),
                    seconds_per_frame=float(r["Seconds_per_Frame"]),
                    an=int(r["an"]),
                    is_attempt_final=r["is_attempt_final"].strip().lower() == "true",
                    t_foot_up=_opt_float(r.get("t_foot_up", "")),
                    t_stable=_opt_float(r.get("t_stable", "")),
                    t_break=_opt_float(r.get("t_break", "")),
                    t_end=float(r["t_end"]),
                )
            )
    return rows


def _capture_id_modless(radar_capture_id: str) -> str:
    """01_MNTRR_RR_V2 -> 01_MNTRR_V2 (strip the modality token)."""
    parts = radar_capture_id.split("_")
    if len(parts) != 4:
        raise ValueError(f"Unexpected capture id shape: {radar_capture_id!r}")
    pid, movement, _modality, version = parts
    return f"{pid}_{movement}_{version}"


def _trial_leg_from_movement(movement_code: str) -> str:
    """Base leg from the movement code (spec §6.6).

    `MNTR*` per the dataset README ("right foot as base" for MNTRR). `TRLG*`
    verified from force-plate vertical load on 30_TRLGL_V1 / 30_TRLGR_V1
    (amendment 2026-09-09 A2), not assumed from the letter.
    """
    if movement_code in ("MNTRR", "TRLGR"):
        return "right"
    if movement_code in ("MNTRL", "TRLGL"):
        return "left"
    raise ValueError(f"Unknown movement code: {movement_code!r}")


# Acquisition protocol by movement code (spec §6.6, amendment A3). The ceiling
# is an acquisition fact with a named source. `None` means unpublished; it is
# never inferred from the observed duration distribution.
_MNTR_SOURCE = (
    "Copeland D et al. Gait Posture 2026;126:110108 (doi 10.1016/j.gaitpost.2026.110108): "
    "'short (4 s) and long (20 s) OLST trials'. README.txt does not state the cue."
)
_ACQUISITION_PROTOCOL: dict[str, dict[str, Any]] = {
    # spec v1.4 (amendment A14): 4000 ms sourced to the companion paper. In spec
    # v1.3 (executed A11/A13) this was None with the README-silence note.
    "MNTRL": {
        "protocol_code": "MNTRL",
        "observation_ceiling_ms": 4000,
        "observation_ceiling_source": _MNTR_SOURCE,
    },
    "MNTRR": {
        "protocol_code": "MNTRR",
        "observation_ceiling_ms": 4000,
        "observation_ceiling_source": _MNTR_SOURCE,
    },
    "TRLGL": {
        "protocol_code": "TRLGL",
        "observation_ceiling_ms": 20000,
        "observation_ceiling_source": "README.txt: 'older adult participants completed longer 20-second trials'",
    },
    "TRLGR": {
        "protocol_code": "TRLGR",
        "observation_ceiling_ms": 20000,
        "observation_ceiling_source": "README.txt: 'older adult participants completed longer 20-second trials'",
    },
}


def _acquisition_protocol(movement_code: str) -> dict[str, Any]:
    try:
        return dict(_ACQUISITION_PROTOCOL[movement_code])
    except KeyError:
        raise ValueError(f"No acquisition protocol declared for movement code {movement_code!r}") from None


def _read_force_plate_csv(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Some captures have a single trailing partial-frame row with empty
            # numeric columns. Skip — not a substantive data quality issue.
            def _present(key: str) -> bool:
                v = r.get(key)
                return isinstance(v, str) and v.strip() != ""
            if not all(_present(k) for k in ("time", "Force_Z", "COP_X", "COP_Y")):
                continue
            rows.append(
                {
                    "time": float(r["time"]),
                    "Force_Z": float(r["Force_Z"]),
                    "COP_X": float(r["COP_X"]),
                    "COP_Y": float(r["COP_Y"]),
                }
            )
    return rows


def _slice_by_time(rows: list[dict[str, float]], start_s: float, end_s: float) -> list[dict[str, float]]:
    return [r for r in rows if start_s <= r["time"] <= end_s]


def _mean(xs: list[float]) -> float:
    # math.fsum is correctly rounded and therefore interpreter-independent.
    # Built-in sum() switched to compensated summation in Python 3.12, which
    # changes the last bits of a float mean between 3.9 and 3.12+ (observed:
    # pilot fixtures built on 3.9.6 vs rebuild on 3.14.6, amendment A6.7).
    # output_hash was never affected (canonicalization rounds to 6 dp) but
    # fixture_id is raw bytes, so the fixture builder must not depend on the
    # interpreter's sum() implementation.
    return math.fsum(xs) / len(xs) if xs else 0.0


def _confidence_ellipse_area_mm2(xs: list[float], ys: list[float]) -> float:
    """95% confidence ellipse area using the chi-square approximation:
        area = pi * 5.991 * sqrt(var_x * var_y - cov_xy²)
    Pinned as rule v1 — same numbers in, same area out.
    """
    n = len(xs)
    if n < 2:
        return 0.0
    mx = _mean(xs)
    my = _mean(ys)
    var_x = math.fsum((x - mx) ** 2 for x in xs) / (n - 1)
    var_y = math.fsum((y - my) ** 2 for y in ys) / (n - 1)
    cov = math.fsum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (n - 1)
    det = var_x * var_y - cov * cov
    if det <= 0.0:
        return 0.0
    return math.pi * 5.991 * math.sqrt(det)


def build_fixture(
    dataset_root: Path,
    participant_id: str,
    capture_id: str,
    attempt_number: int,
    *,
    normalization_rule_version: str = "v1",
    derivation_rule_version: str = "v1",
) -> dict[str, Any]:
    """Build a canonical fixture dict for one attempt.

    Args:
        dataset_root: path to the unzipped PhysioNet release root
            (e.g. data/physionet_olst/olst-mocap-forceplate-radar/1.0/).
        participant_id: zero-padded ("01"…"56").
        capture_id: modality-stripped capture id ("01_MNTRR_V2").
        attempt_number: 1-based.
    """
    demographics = _parse_demographics(dataset_root / "Metadata" / "Participant_Demographics.csv")
    attempts = _parse_attempts(dataset_root / "Metadata" / "OLST_Attempts.csv")

    # Match attempts whose modality-stripped capture id == requested capture.
    capture_attempts = [a for a in attempts if _capture_id_modless(a.radar_capture) == capture_id]
    if not capture_attempts:
        raise FileNotFoundError(f"No OLST_Attempts row for capture {capture_id!r}.")
    total_attempts = len(capture_attempts)

    target = next((a for a in capture_attempts if a.an == attempt_number), None)
    if target is None:
        raise FileNotFoundError(
            f"capture {capture_id!r} has {total_attempts} attempts; "
            f"requested attempt_number={attempt_number} is out of range."
        )

    movement = capture_id.split("_")[1]
    version = capture_id.split("_")[2]

    # Force-plate CSVs are named with `RR` modality canonical id, but the FILES use `FP`.
    fp_left = dataset_root / "Raw" / "ForcePlate" / participant_id / f"{participant_id}_{movement}_FP_{version}_left.csv"
    fp_right = dataset_root / "Raw" / "ForcePlate" / participant_id / f"{participant_id}_{movement}_FP_{version}_right.csv"
    if not fp_left.exists() or not fp_right.exists():
        raise FileNotFoundError(f"Force plate CSV(s) missing for {capture_id!r}: {fp_left}, {fp_right}")

    left_rows = _read_force_plate_csv(fp_left)
    right_rows = _read_force_plate_csv(fp_right)

    leg = _trial_leg_from_movement(movement)

    # Stance phase (spec §6.6): foot-lift -> foot-touchdown. Present on every
    # kept attempt in release 1.0; emitted only when both events exist.
    stance_phase: dict[str, Any] | None = None
    if target.t_foot_up is not None:
        if target.t_end < target.t_foot_up:
            raise ValueError(
                f"Attempt {target.olst_attempt_id}: t_end {target.t_end} < t_foot_up "
                f"{target.t_foot_up}; data quality issue — fixture build refuses."
            )
        stance_phase = {
            "foot_up_ms": int(round(target.t_foot_up * 1000)),
            "touchdown_ms": int(round(target.t_end * 1000)),
            "event_label_source": "OLST_Attempts.csv@v1.0",
        }

    # Stability phase (spec §6.4). When `t_stable` is empty the participant
    # never reached stability: the fixture is built with the phase declared
    # absent, and the CoP / load metrics defined over it are absent too.
    # Nothing is imputed (spec §6.4, amendment A5).
    stability_phase: dict[str, Any] | None
    force_plate: dict[str, Any] | None
    stability_missing_reason: str | None = None
    force_plate_missing_reason: str | None = None

    if target.t_stable is None:
        stability_phase = None
        force_plate = None
        stability_missing_reason = (
            "no t_stable event in OLST_Attempts.csv: the participant did not reach "
            "stability during this attempt"
        )
        force_plate_missing_reason = (
            "CoP and load metrics are defined over the stable phase (spec §6.4), "
            "which is absent for this attempt"
        )
    else:
        start_s = target.t_stable
        end_s = target.t_end if target.is_attempt_final or target.t_break is None else target.t_break
        if end_s < start_s:
            raise ValueError(
                f"Attempt {target.olst_attempt_id}: stability end {end_s} < start {start_s}; "
                f"data quality issue — fixture build refuses."
            )

        # Slice to stability phase
        left_stab = _slice_by_time(left_rows, start_s, end_s)
        right_stab = _slice_by_time(right_rows, start_s, end_s)

        if not left_stab or not right_stab:
            raise ValueError(
                f"Attempt {target.olst_attempt_id}: no force-plate samples in stability window "
                f"[{start_s}, {end_s}] s — fixture build refuses (would imply silent imputation)."
            )

        # Pick the stance side for CoP metrics (the leg the participant is balancing on)
        stance = right_stab if leg == "right" else left_stab

        cop_x = [r["COP_X"] for r in stance]
        cop_y = [r["COP_Y"] for r in stance]
        # Displacement is from-mean (the per-attempt CoP centroid), not from plate origin.
        # Plate-coordinate CoP values include a fixed plate-to-foot offset that varies by
        # participant; differencing from the mean removes it deterministically.
        mx = _mean(cop_x)
        my = _mean(cop_y)
        mean_cop_disp = _mean([math.sqrt((x - mx) ** 2 + (y - my) ** 2) for x, y in zip(cop_x, cop_y)])
        sway_area = _confidence_ellipse_area_mm2(cop_x, cop_y)

        fz_left_mean = _mean([r["Force_Z"] for r in left_stab])
        fz_right_mean = _mean([r["Force_Z"] for r in right_stab])
        total = fz_left_mean + fz_right_mean
        if total <= 0:
            raise ValueError(
                f"Attempt {target.olst_attempt_id}: nonpositive total Force_Z over stability window; "
                f"refusing to compute left/right percentages."
            )
        left_pct = 100.0 * fz_left_mean / total
        right_pct = 100.0 * fz_right_mean / total

        stability_phase = {
            "start_ms": int(round(start_s * 1000)),
            "end_ms": int(round(end_s * 1000)),
            "event_label_source": "OLST_Attempts.csv@v1.0",
        }
        force_plate = {
            "mean_cop_displacement_mm": mean_cop_disp,
            "sway_area_mm2": sway_area,
            # Misnomer retained for v1 output-hash stability: this is the
            # stable-window length, not the stance. See olst_emu_schema_v1.yaml.
            "stance_duration_ms": int(round((end_s - start_s) * 1000)),
            "left_pct": left_pct,
            "right_pct": right_pct,
        }

    # dataset_pointer: pin every source file we touched to its PhysioNet
    # SHA256SUMS.txt entry. A future PhysioNet republish (corrected data,
    # v1.1, …) changes those digests, so the fixture content (and thus
    # fixture_id, run_id, and output_hash) all shift — divergence is
    # detectable, never silent.
    sha_path = dataset_root / "SHA256SUMS.txt"
    if not sha_path.exists():
        raise FileNotFoundError(
            f"PhysioNet SHA256SUMS.txt missing at {sha_path}; refusing to build "
            f"a fixture without source-data content addressing."
        )
    sums = _parse_sha256sums(sha_path)

    def _pointer(rel: str) -> dict[str, str]:
        digest = sums.get(rel)
        if digest is None:
            raise ValueError(
                f"Source file {rel!r} not found in SHA256SUMS.txt — refusing to "
                f"build fixture without a source-data content hash."
            )
        return {"path": rel, "sha256": digest}

    mc_rel = f"Raw/MOCAP/{participant_id}/{participant_id}_{movement}_MC_{version}_pos.csv"
    fp_left_rel = f"Raw/ForcePlate/{participant_id}/{participant_id}_{movement}_FP_{version}_left.csv"
    fp_right_rel = f"Raw/ForcePlate/{participant_id}/{participant_id}_{movement}_FP_{version}_right.csv"
    olst_attempts_rel = "Metadata/OLST_Attempts.csv"
    demographics_rel = "Metadata/Participant_Demographics.csv"

    dataset_pointer = {
        "release": "physionet/olst-mocap-forceplate-radar/1.0",
        "sha256sums_source": "SHA256SUMS.txt",
        # Sorted to keep the fixture content deterministic regardless of build order.
        "files": sorted(
            (
                _pointer(mc_rel),
                _pointer(fp_left_rel),
                _pointer(fp_right_rel),
                _pointer(olst_attempts_rel),
                _pointer(demographics_rel),
            ),
            key=lambda p: p["path"],
        ),
    }

    fixture: dict[str, Any] = {
        "dataset_version": _DATASET_VERSION,
        "participant_id": participant_id,
        "capture_id": capture_id,
        "attempt_number": attempt_number,
        "total_attempts_in_session": total_attempts,
        "trial_leg": leg,
        "age_cohort": demographics.get(participant_id, "unknown"),
        "stability_phase": stability_phase,
        "force_plate": force_plate,
        "stance_phase": stance_phase,
        "acquisition_protocol": _acquisition_protocol(movement),
        "normalization_rule_version": normalization_rule_version,
        "derivation_rule_version": derivation_rule_version,
        "dataset_pointer": dataset_pointer,
        "_provenance": {
            "olst_attempt_id": target.olst_attempt_id,
            "radar_capture": target.radar_capture,
            "mocap_start_time_s": target.mocap_start_time,
            "mocap_end_time_s": target.mocap_end_time,
            "seconds_per_frame": target.seconds_per_frame,
            "is_attempt_final": target.is_attempt_final,
        },
    }
    if stability_missing_reason is not None:
        fixture["stability_phase__missing_reason"] = stability_missing_reason
    if force_plate_missing_reason is not None:
        fixture["force_plate__missing_reason"] = force_plate_missing_reason
    return fixture
