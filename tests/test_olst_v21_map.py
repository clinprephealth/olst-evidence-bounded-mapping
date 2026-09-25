"""Criterion map v2.1 (amendment 2026-09-09 A12): sway loses categorical
authority, keeps evidentiary standing. Synthetic fixtures only.

Asserted:
  * v2.1 differs from v2 only in the gait rule's sway_gating flag and text.
  * Under v2.1 the label follows the censored duration construct regardless
    of sway; sway is still reported in detail and still an evidence pointer.
  * With the flag absent (v2) or true, the harness output is unchanged
    (the v2 golden file, asserted in test_olst_v2_map.py, is the proof).
  * v2 / v2.1 pair identity: same fixture_id, spec_id, harness_version;
    different criterion_map_id and run_id.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

import experiments.olst_nc_replay.olst_replay_harness as h
from experiments.olst_nc_replay import PROTOCOL_CENSORED, ExcludedCaptureError, run

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES_DIR = _REPO_ROOT / "experiments" / "olst_nc_replay" / "fixtures"
_SPECS_DIR = _REPO_ROOT / "experiments" / "olst_nc_replay" / "specs"
_V2 = _SPECS_DIR / "NC_CRITERION_EMU_MAP_v2.json"
_V21 = _SPECS_DIR / "NC_CRITERION_EMU_MAP_v2.1.json"
_GOLDEN_V21 = _FIXTURES_DIR / "golden_output_hashes_v2.1.json"

_V2_SHA256 = "d4ac623a2590f51bb8351bced784f58e88e3c4f75683482ca0cc1d2d2529d3c4"


def _runnable() -> list[Path]:
    return sorted(
        p for p in _FIXTURES_DIR.glob("*.json")
        if not p.name.startswith("golden_output_hashes_") and p.name != "excluded_capture_negative_control.json"
    )


def _run(p: Path, version: str):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return run(p, mapping_spec_version=version)


def _stance_fixture(sway: float, stance_ms: int, *, protocol: str, ceiling: int | None) -> dict:
    fx = json.loads((_FIXTURES_DIR / "clean_older_02_20s.json").read_text(encoding="utf-8"))
    fx["force_plate"]["sway_area_mm2"] = sway
    fx["stance_phase"] = {"foot_up_ms": 1000, "touchdown_ms": 1000 + stance_ms, "event_label_source": "OLST_Attempts.csv@v1.0"}
    fx["acquisition_protocol"] = {"protocol_code": protocol, "observation_ceiling_ms": ceiling, "observation_ceiling_source": "test"}
    return fx


def _gait(report):
    ev = next((c for c in report.criterion_evaluations if c["criterion_id"] == "gait_type"), None)
    ne = next((c for c in report.non_evaluable_criteria if c["criterion_id"] == "gait_type"), None)
    return ev, ne


def test_v2_map_bytes_are_frozen() -> None:
    import hashlib
    assert hashlib.sha256(_V2.read_bytes()).hexdigest() == _V2_SHA256, "v2 must stay byte-identical (A12: v2 is executed as frozen)"


def test_v21_differs_from_v2_only_in_sway_authority() -> None:
    v2 = json.loads(_V2.read_text(encoding="utf-8"))
    v21 = json.loads(_V21.read_text(encoding="utf-8"))
    assert v21["criteria"]["gait_type"]["rule"]["sway_gating"] is False
    assert "sway_gating" not in v2["criteria"]["gait_type"]["rule"]
    # thresholds, censoring, aggregation, derivability, required EMUs identical
    for key in ("duration_field", "thresholds", "protocol_censoring", "type"):
        assert v21["criteria"]["gait_type"]["rule"][key] == v2["criteria"]["gait_type"]["rule"][key], key
    assert v21["criteria"]["gait_type"]["required_emus"] == v2["criteria"]["gait_type"]["required_emus"] == ["gait_temporal_control", "postural_stability_index"]
    assert v21["criteria"]["gait_type"]["derivability"] == "partial"
    assert {k: v for k, v in v21["aggregation"].items() if k != "note"} == {k: v for k, v in v2["aggregation"].items() if k != "note"}
    for cid in v2["criteria"]:
        if cid == "gait_type":
            continue
        a = {k: v for k, v in v2["criteria"][cid].items() if k != "mapping_rule_version"}
        b = {k: v for k, v in v21["criteria"][cid].items() if k != "mapping_rule_version"}
        assert a == b, cid


@pytest.mark.parametrize(
    "sway,stance_ms,expected_v2,expected_v21",
    [
        (1800.0, 12000, "impaired", "normal"),   # the 66 long TRLG attempts: sway forces impaired under v2
        (1800.0, 7000, "impaired", "weak"),
        (1800.0, 3000, "impaired", "impaired"),
        (100.0, 12000, "normal", "normal"),
        (400.0, 12000, "weak", "normal"),         # v2: >=10 s but sway >= 250 -> weak
    ],
)
def test_v21_label_follows_duration_only(tmp_path: Path, sway: float, stance_ms: int, expected_v2: str, expected_v21: str) -> None:
    p = tmp_path / "f.json"
    p.write_text(json.dumps(_stance_fixture(sway, stance_ms, protocol="TRLGL", ceiling=20000), sort_keys=True), encoding="utf-8")
    ev2, _ = _gait(_run(p, "v2"))
    ev21, _ = _gait(_run(p, "v2.1"))
    assert ev2["evaluation"] == expected_v2
    assert ev21["evaluation"] == expected_v21
    assert ev21["detail"]["sway_area_mm2"] == sway, "sway is still reported"
    assert ev21["detail"]["sway_gating"] is False
    assert "sway_gating" not in ev2["detail"], "v2 output must not acquire the new key"


def test_v21_censoring_unchanged_and_sway_does_not_override_it(tmp_path: Path) -> None:
    p = tmp_path / "f.json"
    p.write_text(json.dumps(_stance_fixture(1800.0, 4800, protocol="MNTRL", ceiling=None), sort_keys=True), encoding="utf-8")
    ev2, _ = _gait(_run(p, "v2"))
    ev21, _ = _gait(_run(p, "v2.1"))
    assert ev2["evaluation"] == "impaired", "v2: sway >= 600 overrides censoring"
    assert ev21["evaluation"] == PROTOCOL_CENSORED, "v2.1: nothing overrides censoring"
    assert ev21["detail"]["unobservable_thresholds_ms"] == [10000, 5000]


def test_v21_keeps_sway_evidence_pointer_and_missingness(tmp_path: Path) -> None:
    fx = _stance_fixture(1800.0, 12000, protocol="TRLGL", ceiling=20000)
    p = tmp_path / "f.json"
    p.write_text(json.dumps(fx, sort_keys=True), encoding="utf-8")
    rep = _run(p, "v2.1")
    pointed = {e.emu_id.split(":")[0] for e in rep.traceability["gait_type"]}
    assert pointed == {"gait_temporal_control", "postural_stability_index"}
    # no stable phase -> no CoP EMU -> still non-evaluable (evidence requirement kept)
    fx["stability_phase"] = None
    fx["force_plate"] = None
    p.write_text(json.dumps(fx, sort_keys=True), encoding="utf-8")
    ev, ne = _gait(_run(p, "v2.1"))
    assert ev is None and "postural_stability_index" in ne["non_evaluable_reason"]


@pytest.mark.parametrize("fixture_path", _runnable(), ids=lambda p: p.name)
def test_v2_v21_pair_identity_on_synthetic_fixture(fixture_path: Path) -> None:
    r2, r21 = _run(fixture_path, "v2"), _run(fixture_path, "v2.1")
    assert r2.fixture_id == r21.fixture_id
    assert r2.spec_id == r21.spec_id and r2.harness_version == r21.harness_version
    assert r2.criterion_map_id != r21.criterion_map_id
    assert r2.run_id != r21.run_id


def test_v21_golden_vectors_match() -> None:
    golden = json.loads(_GOLDEN_V21.read_text(encoding="utf-8"))
    runnable = {p.name: p for p in _runnable()}
    assert set(runnable) <= set(golden)
    for name, expected in golden.items():
        if expected.get("expects_exception"):
            with pytest.raises(ExcludedCaptureError):
                _run(_FIXTURES_DIR / name, "v2.1")
            continue
        rep = _run(runnable[name], "v2.1")
        assert rep.fixture_id == expected["fixture_id"], name
        assert rep.output_hash == expected["output_hash"], name
