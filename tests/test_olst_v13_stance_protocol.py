"""Spec v1.3 additions (amendment 2026-09-09): stance window, acquisition
protocol ceiling, map-declared rule with protocol censoring, and the D2
capture aggregate.

These tests use synthetic fixtures only. Golden-hash inertness of the new
fields for pre-v1.3 fixtures is asserted by test_olst_nc_replay.py.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

import experiments.olst_nc_replay.olst_replay_harness as h
from experiments.olst_nc_replay import PROTOCOL_CENSORED, run
from experiments.olst_nc_replay.lakehouse import ingest, ingest_aggregate, list_aggregates
from experiments.olst_nc_replay.olst_capture_aggregate import aggregate_capture

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES_DIR = _REPO_ROOT / "experiments" / "olst_nc_replay" / "fixtures"


def _base() -> dict:
    return json.loads((_FIXTURES_DIR / "clean_older_02_20s.json").read_text(encoding="utf-8"))


def _with_stance(fx: dict, *, foot_up_ms: int, touchdown_ms: int, protocol: str, ceiling: int | None) -> dict:
    fx = dict(fx)
    fx["stance_phase"] = {"foot_up_ms": foot_up_ms, "touchdown_ms": touchdown_ms, "event_label_source": "OLST_Attempts.csv@v1.0"}
    fx["acquisition_protocol"] = {"protocol_code": protocol, "observation_ceiling_ms": ceiling, "observation_ceiling_source": "test"}
    return fx


def _write(tmp_path: Path, name: str, fx: dict) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(fx, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    return p


def _run(p: Path, version: str = "v1"):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return run(p, mapping_spec_version=version)


def _gtc(report) -> dict:
    return next(e for e in report.emu_outputs if e["emu_type"] == "gait_temporal_control")


# -------- EMU derivation ---------------------------------------------------

def test_stance_fields_added_only_when_fixture_carries_them(tmp_path: Path) -> None:
    plain = _run(_write(tmp_path, "plain.json", _base()))
    assert set(_gtc(plain)["payload"]) == {"stability_duration_ms", "trial_leg"}

    fx = _with_stance(_base(), foot_up_ms=1000, touchdown_ms=21000, protocol="TRLGL", ceiling=20000)
    rep = _run(_write(tmp_path, "stance.json", fx))
    payload = _gtc(rep)["payload"]
    assert payload["stance_duration_ms"] == 20000
    assert payload["observation_ceiling_ms"] == 20000
    assert payload["protocol_code"] == "TRLGL"
    assert payload["stability_duration_ms"] == fx["stability_phase"]["end_ms"] - fx["stability_phase"]["start_ms"]
    prov = _gtc(rep)["provenance"]
    assert prov["stance_phase_foot_up_ms"] == 1000 and prov["stance_phase_touchdown_ms"] == 21000
    assert prov["observation_ceiling_source"] == "test"


def test_stance_only_fixture_emits_gtc_and_v1_gait_is_non_evaluable(tmp_path: Path) -> None:
    """An attempt with no t_stable: stability_phase and force_plate are null,
    stance window present. gait_temporal_control is emitted with the stance
    duration only; v1 gait_type is non-evaluable naming the missing EMU."""
    fx = _with_stance(_base(), foot_up_ms=500, touchdown_ms=7780, protocol="TRLGR", ceiling=20000)
    fx["stability_phase"] = None
    fx["stability_phase__missing_reason"] = "no t_stable event"
    fx["force_plate"] = None
    fx["force_plate__missing_reason"] = "defined over the stable phase"
    rep = _run(_write(tmp_path, "stance_only.json", fx))
    payload = _gtc(rep)["payload"]
    assert "stability_duration_ms" not in payload
    assert payload["stance_duration_ms"] == 7280
    assert {e["emu_type"] for e in rep.emu_outputs} == {"gait_temporal_control"}
    ne = {c["criterion_id"]: c["non_evaluable_reason"] for c in rep.non_evaluable_criteria}
    assert "gait_type" in ne and "postural_stability_index" in ne["gait_type"]
    assert "gait_type" not in {c["criterion_id"] for c in rep.criterion_evaluations}
    assert "gait_type" not in rep.traceability


def test_null_ceiling_is_carried_as_null_not_dropped(tmp_path: Path) -> None:
    fx = _with_stance(_base(), foot_up_ms=1000, touchdown_ms=5800, protocol="MNTRL", ceiling=None)
    rep = _run(_write(tmp_path, "mntr.json", fx))
    payload = _gtc(rep)["payload"]
    assert "observation_ceiling_ms" in payload and payload["observation_ceiling_ms"] is None


def test_non_integer_ceiling_is_schema_error(tmp_path: Path) -> None:
    fx = _with_stance(_base(), foot_up_ms=1000, touchdown_ms=5800, protocol="MNTRL", ceiling=None)
    fx["acquisition_protocol"]["observation_ceiling_ms"] = "20s"
    with pytest.raises(h.FixtureSchemaError):
        _run(_write(tmp_path, "bad.json", fx))


# -------- map-declared rule with censoring ---------------------------------

def _v2_like_map(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, censoring: bool = True) -> dict:
    """Register a v1-map copy under version 'vT' whose gait_type carries a
    declarative rule on stance_duration_ms (same numeric thresholds as v1)."""
    m = json.loads(h._CRITERION_MAP_PATH.read_text(encoding="utf-8"))
    m["criteria"]["gait_type"]["derivability"] = "partial"
    m["criteria"]["gait_type"]["rule"] = {
        "type": "duration_sway_thresholds",
        "duration_field": "stance_duration_ms",
        "thresholds": {
            "duration_normal_min_ms": 10000,
            "duration_weak_min_ms": 5000,
            "sway_area_normal_max_mm2": 250.0,
            "sway_area_impaired_min_mm2": 600.0,
        },
        "protocol_censoring": censoring,
    }
    m["aggregation"] = {
        "criterion_id": "gait_type",
        "rule": "best_of_attempts",
        "emu_type": "gait_temporal_control",
        "payload_field": "stance_duration_ms",
        "require_every_attempt": True,
        "require_non_overlapping_attempt_windows": True,
        "protocol_censoring": censoring,
    }
    path = tmp_path / "NC_CRITERION_EMU_MAP_vT.json"
    path.write_text(json.dumps(m, indent=2), encoding="utf-8")
    real = h._criterion_map_path
    monkeypatch.setattr(h, "_criterion_map_path", lambda v: path if v == "vT" else real(v))
    return m


def _gait(report):
    ev = next((c for c in report.criterion_evaluations if c["criterion_id"] == "gait_type"), None)
    ne = next((c for c in report.non_evaluable_criteria if c["criterion_id"] == "gait_type"), None)
    return ev, ne


def test_rule_labels_when_ceiling_permits_all_thresholds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _v2_like_map(tmp_path, monkeypatch)
    base = _base()
    base["force_plate"]["sway_area_mm2"] = 100.0
    for stance, expected in ((12000, "normal"), (7000, "weak"), (3000, "impaired")):
        fx = _with_stance(base, foot_up_ms=1000, touchdown_ms=1000 + stance, protocol="TRLGL", ceiling=20000)
        ev, ne = _gait(_run(_write(tmp_path, f"t{stance}.json", fx), "vT"))
        assert ne is None and ev["evaluation"] == expected, (stance, ev, ne)
        assert ev["derivability"] == "partial"
        assert ev["detail"]["duration_ms"] == stance
        assert ev["detail"]["unobservable_thresholds_ms"] == []


def test_rule_censors_when_ceiling_is_null(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _v2_like_map(tmp_path, monkeypatch)
    base = _base()
    base["force_plate"]["sway_area_mm2"] = 100.0
    for stance in (4800, 980, 5200):
        fx = _with_stance(base, foot_up_ms=1000, touchdown_ms=1000 + stance, protocol="MNTRR", ceiling=None)
        ev, ne = _gait(_run(_write(tmp_path, f"c{stance}.json", fx), "vT"))
        assert ne is None and ev["evaluation"] == PROTOCOL_CENSORED, (stance, ev, ne)
        assert ev["detail"]["duration_ms"] == stance, "censoring withholds the label, not the number"
        assert ev["detail"]["unobservable_thresholds_ms"] == [10000, 5000]
        assert ev["detail"]["observation_ceiling_ms"] is None


def test_rule_intermediate_ceiling_emits_impaired_below_weak_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _v2_like_map(tmp_path, monkeypatch)
    base = _base()
    base["force_plate"]["sway_area_mm2"] = 100.0
    fx = _with_stance(base, foot_up_ms=0, touchdown_ms=3000, protocol="HYPO", ceiling=7000)
    ev, _ = _gait(_run(_write(tmp_path, "i1.json", fx), "vT"))
    assert ev["evaluation"] == "impaired" and ev["detail"]["unobservable_thresholds_ms"] == [10000]
    fx = _with_stance(base, foot_up_ms=0, touchdown_ms=6000, protocol="HYPO", ceiling=7000)
    ev, _ = _gait(_run(_write(tmp_path, "i2.json", fx), "vT"))
    assert ev["evaluation"] == PROTOCOL_CENSORED


def test_sway_bound_is_not_censored_by_duration_ceiling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _v2_like_map(tmp_path, monkeypatch)
    base = _base()
    base["force_plate"]["sway_area_mm2"] = 900.0
    fx = _with_stance(base, foot_up_ms=1000, touchdown_ms=5800, protocol="MNTRL", ceiling=None)
    ev, _ = _gait(_run(_write(tmp_path, "sway.json", fx), "vT"))
    assert ev["evaluation"] == "impaired"


def test_rule_without_stance_field_is_non_evaluable_with_reason(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _v2_like_map(tmp_path, monkeypatch)
    rep = _run(_write(tmp_path, "plain.json", _base()), "vT")  # synthetic v1 fixture: no stance window
    ev, ne = _gait(rep)
    assert ev is None and "stance_duration_ms" in ne["non_evaluable_reason"]
    assert "gait_type" not in rep.traceability


def test_rule_and_v1_differ_in_run_id_and_output_for_same_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _v2_like_map(tmp_path, monkeypatch)
    fx = _with_stance(_base(), foot_up_ms=1000, touchdown_ms=13000, protocol="TRLGL", ceiling=20000)
    p = _write(tmp_path, "pair.json", fx)
    r1, r2 = _run(p, "v1"), _run(p, "vT")
    assert r1.fixture_id == r2.fixture_id
    assert r1.harness_version == r2.harness_version and r1.spec_id == r2.spec_id
    assert r1.criterion_map_id != r2.criterion_map_id
    assert r1.run_id != r2.run_id and r1.output_hash != r2.output_hash


# -------- D2 aggregate -----------------------------------------------------

def _capture_reports(tmp_path: Path, version: str, windows: list[tuple[int, int]], *, protocol: str, ceiling: int | None, total: int | None = None, sway: float = 100.0):
    base = _base()
    base["force_plate"]["sway_area_mm2"] = sway
    base["total_attempts_in_session"] = total if total is not None else len(windows)
    reports = []
    for i, (fu, td) in enumerate(windows, start=1):
        fx = _with_stance(base, foot_up_ms=fu, touchdown_ms=td, protocol=protocol, ceiling=ceiling)
        fx["attempt_number"] = i
        reports.append(_run(_write(tmp_path, f"{protocol}_an{i}.json", fx), version))
    return reports


def test_aggregate_best_of_labels_under_permissive_ceiling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    m = _v2_like_map(tmp_path, monkeypatch)
    reps = _capture_reports(tmp_path, "vT", [(1000, 4000), (6000, 17000), (19000, 21000)], protocol="TRLGL", ceiling=20000)
    agg = aggregate_capture(reps, m)
    assert agg["evaluable"] is True and agg["non_evaluable_reason"] is None
    assert agg["best_of"] == {"stance_duration_ms": 11000, "attempt_number": 2}
    assert agg["aggregate_evaluation"] == "normal"
    assert agg["detail"]["sway_considered"] is False
    assert [x["attempt_number"] for x in agg["per_attempt"]] == [1, 2, 3]
    assert len(agg["attempt_run_ids"]) == 3 and agg["aggregate_id"]
    # deterministic
    assert aggregate_capture(reps, m)["aggregate_id"] == agg["aggregate_id"]


def test_aggregate_censored_under_null_ceiling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    m = _v2_like_map(tmp_path, monkeypatch)
    reps = _capture_reports(tmp_path, "vT", [(1000, 5800), (9000, 13700), (17000, 20000)], protocol="MNTRL", ceiling=None)
    agg = aggregate_capture(reps, m)
    assert agg["evaluable"] is True
    assert agg["best_of"]["stance_duration_ms"] == 4800
    assert agg["aggregate_evaluation"] == PROTOCOL_CENSORED
    assert agg["detail"]["unobservable_thresholds_ms"] == [10000, 5000]


def test_aggregate_requires_every_attempt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    m = _v2_like_map(tmp_path, monkeypatch)
    reps = _capture_reports(tmp_path, "vT", [(1000, 4000), (6000, 17000)], protocol="TRLGL", ceiling=20000, total=3)
    agg = aggregate_capture(reps, m)
    assert agg["evaluable"] is False and "[3]" in agg["non_evaluable_reason"]
    assert agg["best_of"] is None and agg["aggregate_evaluation"] is None
    assert len(agg["per_attempt"]) == 2, "per-attempt rows stay in the output next to the (absent) aggregate"


def test_aggregate_refuses_overlapping_windows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """47_TRLGL_V4 shape: a final row spanning the whole capture."""
    m = _v2_like_map(tmp_path, monkeypatch)
    reps = _capture_reports(tmp_path, "vT", [(10780, 22570), (23460, 23670), (24440, 30300), (11090, 30300)], protocol="TRLGL", ceiling=20000)
    agg = aggregate_capture(reps, m)
    assert agg["evaluable"] is False and "overlap" in agg["non_evaluable_reason"]
    assert "an4" in agg["non_evaluable_reason"]
    # A4.2: rows ordered by foot-up time, an4 sorts second
    assert [x["attempt_number"] for x in agg["per_attempt"]] == [1, 4, 2, 3]


def test_aggregate_orders_rows_by_foot_up_not_attempt_number(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    m = _v2_like_map(tmp_path, monkeypatch)
    reps = _capture_reports(tmp_path, "vT", [(9000, 12000), (1000, 4000)], protocol="TRLGL", ceiling=20000)
    agg = aggregate_capture(reps, m)
    assert [x["attempt_number"] for x in agg["per_attempt"]] == [2, 1]


def test_aggregate_requires_declaration_and_consistent_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    m = _v2_like_map(tmp_path, monkeypatch)
    reps = _capture_reports(tmp_path, "vT", [(1000, 4000)], protocol="TRLGL", ceiling=20000)
    with pytest.raises(ValueError):
        aggregate_capture(reps, {"criteria": {}})
    other = _run(_write(tmp_path, "other.json", _base()), "v1")
    with pytest.raises(ValueError):
        aggregate_capture(reps + [other], m)


def test_aggregate_ingest_requires_constituent_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    m = _v2_like_map(tmp_path, monkeypatch)
    reps = _capture_reports(tmp_path, "vT", [(1000, 4000), (6000, 17000)], protocol="TRLGL", ceiling=20000)
    agg = aggregate_capture(reps, m)
    lake = tmp_path / "lake"
    with pytest.raises(ValueError):
        ingest_aggregate(agg, lake)
    for r in reps:
        ingest(r, "{}", lake)
    assert ingest_aggregate(agg, lake) == 1
    assert ingest_aggregate(agg, lake) == 0, "idempotent"
    assert [a["aggregate_id"] for a in list_aggregates(lake)] == [agg["aggregate_id"]]
