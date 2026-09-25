"""Generate the 16-fixture synthetic suite (one-shot; commit the resulting JSON files).

Usage (from repo root):
    PYTHONPATH=. python -m experiments.olst_nc_replay.fixtures._generate_fixtures

Re-running is idempotent (same input → same JSON). Determinism is the point.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_HERE = Path(__file__).parent

_DATASET_VERSION = "1.0"


def _fp(
    mean_cop: float,
    sway: float,
    stance_ms: int,
    left: float,
    right: float,
    missing: list[str] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "mean_cop_displacement_mm": mean_cop,
        "sway_area_mm2": sway,
        "stance_duration_ms": stance_ms,
        "left_pct": left,
        "right_pct": right,
    }
    if missing:
        for k in missing:
            out[k] = None
            out[f"{k}__missing_reason"] = "channel_absent_in_export"
    return out


def _stab(start_ms: int, end_ms: int, src: str = "MoCap.events.v1") -> dict[str, Any]:
    return {"start_ms": start_ms, "end_ms": end_ms, "event_label_source": src}


def _base(
    capture_id: str,
    participant_id: str,
    cohort: str,
    leg: str,
    attempt: int,
    total: int,
    stability: dict[str, Any],
    fp: dict[str, Any],
    *,
    notes: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fixture: dict[str, Any] = {
        "dataset_version": _DATASET_VERSION,
        "participant_id": participant_id,
        "capture_id": capture_id,
        "attempt_number": attempt,
        "total_attempts_in_session": total,
        "trial_leg": leg,
        "age_cohort": cohort,
        "stability_phase": stability,
        "force_plate": fp,
        "normalization_rule_version": "v1",
        "derivation_rule_version": "v1",
    }
    if notes:
        fixture["fixture_notes"] = notes
    if extra:
        fixture.update(extra)
    return fixture


# ---- 5 clean trials -------------------------------------------------------
clean_young_01 = _base(
    "01_MNTRR_V1", "01", "young", "right", 1, 3,
    _stab(1500, 12500), _fp(8.42, 142.6, 11000, 12.0, 88.0),
    notes="Clean young-cohort trial; expect gait_type=normal.",
)
clean_young_02 = _base(
    "02_MNTRL_V1", "02", "young", "left", 1, 2,
    _stab(2000, 13200), _fp(9.10, 198.4, 11200, 87.5, 12.5),
    notes="Clean young left-leg trial; expect gait_type=normal.",
)
clean_older_01 = _base(
    "33_MNTRR_V1", "33", "older", "right", 1, 4,
    _stab(2500, 13500), _fp(11.20, 215.8, 11000, 18.0, 82.0),
    notes="Clean older-cohort trial right at the normal/weak boundary.",
)
clean_older_02_20s = _base(
    "33_MNTRR_V2", "33", "older", "right", 2, 4,
    _stab(0, 20000), _fp(14.50, 230.0, 20000, 22.0, 78.0),
    notes="20s capture older-cohort only — spec §5 cohort asymmetry.",
)
clean_older_03 = _base(
    "40_MNTRL_V1", "40", "older", "left", 1, 3,
    _stab(3000, 14000), _fp(10.05, 188.0, 11000, 79.0, 21.0),
    notes="Clean older left-leg.",
)

# ---- 3 noisy trials -------------------------------------------------------
noisy_01 = _base(
    "05_MNTRR_V3", "05", "young", "right", 3, 3,
    _stab(2000, 11000), _fp(18.40, 480.5, 9000, 35.0, 65.0),
    notes="High CoP variance; sway crosses normal-max threshold.",
)
noisy_02 = _base(
    "07_MNTRL_V2", "07", "older", "left", 2, 5,
    _stab(2500, 9500), _fp(22.10, 540.0, 7000, 60.0, 40.0),
    notes="High sway, short stability — expect weak.",
)
noisy_03 = _base(
    "09_MNTRR_V4", "09", "young", "right", 4, 4,
    _stab(1500, 10000), _fp(19.80, 510.5, 8500, 30.0, 70.0),
    notes="Borderline weak; high sway, sub-10s duration.",
)

# ---- 2 missing-data trials ------------------------------------------------
missing_fp_channel = _base(
    "11_MNTRR_V1", "11", "older", "right", 1, 3,
    _stab(2000, 12000),
    _fp(0.0, 0.0, 0, 0.0, 0.0, missing=["mean_cop_displacement_mm", "sway_area_mm2", "stance_duration_ms"]),
    notes="Force-plate CoP channels missing — expect postural_stability_index EMU not derived; "
          "gait_type should fall to non_evaluable for missing required EMU.",
)
# Override fp explicitly so the typed nulls are present (helper masked them as 0.0 first).
missing_fp_channel["force_plate"] = {
    "mean_cop_displacement_mm": None,
    "mean_cop_displacement_mm__missing_reason": "channel_absent_in_export",
    "sway_area_mm2": None,
    "sway_area_mm2__missing_reason": "channel_absent_in_export",
    "stance_duration_ms": None,
    "stance_duration_ms__missing_reason": "channel_absent_in_export",
    "left_pct": 22.0,
    "right_pct": 78.0,
}
missing_mocap_events = _base(
    "13_MNTRL_V1", "13", "young", "left", 1, 2,
    _stab(0, 0, src="MoCap.events.v1"),
    _fp(9.5, 165.0, 11000, 80.0, 20.0),
)
missing_mocap_events["stability_phase"] = {
    "start_ms": None,
    "start_ms__missing_reason": "MoCap event labels dropout for this attempt",
    "end_ms": None,
    "end_ms__missing_reason": "MoCap event labels dropout for this attempt",
    "event_label_source": None,
    "event_label_source__missing_reason": "MoCap event labels dropout for this attempt",
}
missing_mocap_events["fixture_notes"] = (
    "MoCap event-label dropout — gait_temporal_control EMU should be skipped, "
    "ambulatory_aids and gait_type should both fall to non_evaluable."
)

# ---- 2 axis-flip trials (left/right swapped accidentally) -----------------
axis_flip_01 = _base(
    "15_MNTRR_V1", "15", "young", "right", 1, 3,
    _stab(1800, 12300), _fp(8.2, 145.0, 10500, 85.0, 15.0),
    notes="trial_leg=right but force-plate left/right swapped — asymmetry index detects it.",
)
axis_flip_02 = _base(
    "17_MNTRL_V1", "17", "older", "left", 1, 4,
    _stab(2200, 13500), _fp(11.5, 210.0, 11300, 22.0, 78.0),
    notes="trial_leg=left but force-plate left/right swapped.",
)

# ---- 2 unit-mismatch trials (force in BW-normalized vs Newtons) -----------
unit_mismatch_bw = _base(
    "19_MNTRR_V1", "19", "young", "right", 1, 3,
    _stab(1500, 12500), _fp(0.95, 8.4, 11000, 12.0, 88.0),
    notes="Force values in body-weight normalized scale by mistake — sway artificially low.",
    extra={"force_plate_unit_declared": "BW_normalized"},
)
unit_mismatch_n = _base(
    "21_MNTRL_V1", "21", "older", "left", 1, 4,
    _stab(2000, 13000), _fp(102.5, 1820.4, 11000, 80.0, 20.0),
    notes="Force values in Newtons but downstream rule expected BW-normalized — sway above impaired threshold.",
    extra={"force_plate_unit_declared": "Newtons"},
)

# ---- 2 borderline (right at the 10s clinical cutoff) ----------------------
borderline_just_over = _base(
    "23_MNTRR_V1", "23", "older", "right", 1, 3,
    _stab(2500, 12500), _fp(10.5, 245.0, 10000, 17.0, 83.0),
    notes="Stability exactly 10000ms and sway just under normal-max → expect normal.",
)
borderline_just_under = _base(
    "25_MNTRL_V1", "25", "older", "left", 1, 3,
    _stab(2500, 12499), _fp(10.6, 246.0, 9999, 82.0, 18.0),
    notes="Stability 9999ms (1 ms below cutoff) → expect weak.",
)

# ---- 2 adversarial --------------------------------------------------------
adversarial_conflicting_events = _base(
    "27_MNTRR_V1", "27", "young", "right", 1, 3,
    _stab(5000, 3000),
    _fp(8.5, 150.0, 11000, 13.0, 87.0),
    notes="end_ms < start_ms — derives a negative stability_duration_ms; harness does not "
          "self-correct; criterion evaluator must observe negative input and route accordingly.",
)
adversarial_stale_metadata = _base(
    "29_MNTRL_V1", "29", "older", "left", 1, 3,
    _stab(2000, 13000), _fp(10.0, 200.0, 11000, 78.0, 22.0),
    notes="Stale metadata version label.",
    extra={
        "metadata_recorded_at": "2025-04-01T00:00:00Z",
        "metadata_supersedes": "2026-01-01T00:00:00Z",
    },
)


_FIXTURES: dict[str, dict[str, Any]] = {
    "clean_young_01": clean_young_01,
    "clean_young_02": clean_young_02,
    "clean_older_01": clean_older_01,
    "clean_older_02_20s": clean_older_02_20s,
    "clean_older_03": clean_older_03,
    "noisy_01": noisy_01,
    "noisy_02": noisy_02,
    "noisy_03": noisy_03,
    "missing_fp_channel": missing_fp_channel,
    "missing_mocap_events": missing_mocap_events,
    "axis_flip_01": axis_flip_01,
    "axis_flip_02": axis_flip_02,
    "unit_mismatch_bw": unit_mismatch_bw,
    "unit_mismatch_n": unit_mismatch_n,
    "borderline_just_over": borderline_just_over,
    "borderline_just_under": borderline_just_under,
    "adversarial_conflicting_events": adversarial_conflicting_events,
    "adversarial_stale_metadata": adversarial_stale_metadata,
}


# Negative-control fixture for the exclusion gate (asserted via test, not run)
EXCLUDED_NEGATIVE_CONTROL = {
    "name": "excluded_capture_negative_control",
    "fixture": _base(
        "12_MNTRL_V2", "12", "older", "left", 2, 4,
        _stab(2000, 13000), _fp(11.0, 220.0, 11000, 80.0, 20.0),
        notes="Asserts ExcludedCaptureError fires before any EMU derivation.",
    ),
}


def main() -> None:
    for name, fixture in _FIXTURES.items():
        out_path = _HERE / f"{name}.json"
        # Stable serialization for replay determinism: sort_keys, no trailing newline.
        text = json.dumps(fixture, sort_keys=True, separators=(",", ":"))
        out_path.write_text(text, encoding="utf-8")
        print(f"wrote {out_path.name}")

    # Negative control written separately so test code can find it without running run().
    nc_path = _HERE / f"{EXCLUDED_NEGATIVE_CONTROL['name']}.json"
    text = json.dumps(EXCLUDED_NEGATIVE_CONTROL["fixture"], sort_keys=True, separators=(",", ":"))
    nc_path.write_text(text, encoding="utf-8")
    print(f"wrote {nc_path.name}")


if __name__ == "__main__":
    main()
