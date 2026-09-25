"""Criterion map v2 (plan Step 2.4 assertions, synthetic-fixture half).

The real-fixture half (every real fixture: run_id(v1) != run_id(v2), equal
fixture_id / spec_id / harness_version, verify_replay on all, recall of v1
after v2 ingest) runs over the committed store once Step 1 and Step 2 have
executed on a complete mirror; it is not asserted here.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from experiments.olst_nc_replay import ExcludedCaptureError, run
from experiments.olst_nc_replay.lakehouse import ingest, recall, verify_replay

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES_DIR = _REPO_ROOT / "experiments" / "olst_nc_replay" / "fixtures"
_SPECS_DIR = _REPO_ROOT / "experiments" / "olst_nc_replay" / "specs"
_V1 = _SPECS_DIR / "NC_CRITERION_EMU_MAP_v1.json"
_V2 = _SPECS_DIR / "NC_CRITERION_EMU_MAP_v2.json"
_GOLDEN_V2 = _FIXTURES_DIR / "golden_output_hashes_v2.json"

# v1 map bytes as frozen at the pilot; any change here is a protocol violation.
_V1_SHA256 = "2267d7c95ee88df0856f16897317394838804d2bee3f63c9f857c57346c6e4ed"


def _runnable() -> list[Path]:
    return sorted(
        p for p in _FIXTURES_DIR.glob("*.json")
        if not p.name.startswith("golden_output_hashes_") and p.name != "excluded_capture_negative_control.json"
    )


def _run(p: Path, version: str):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return run(p, mapping_spec_version=version)


def test_v1_map_bytes_are_frozen() -> None:
    import hashlib
    assert hashlib.sha256(_V1.read_bytes()).hexdigest() == _V1_SHA256, "v1 map must stay byte-identical (plan Step 2.1)"


def test_v2_map_declares_decisions_d1_to_d4a() -> None:
    m = json.loads(_V2.read_text(encoding="utf-8"))
    gait = m["criteria"]["gait_type"]
    assert gait["derivability"] == "partial"                                   # D3
    assert gait["rule"]["duration_field"] == "stance_duration_ms"              # D1
    t = gait["rule"]["thresholds"]
    assert (t["duration_normal_min_ms"], t["duration_weak_min_ms"]) == (10000, 5000)   # D4
    assert (t["sway_area_normal_max_mm2"], t["sway_area_impaired_min_mm2"]) == (250.0, 600.0)
    assert gait["rule"]["protocol_censoring"] is True                         # D4a
    agg = m["aggregation"]
    assert agg["rule"] == "best_of_attempts" and agg["payload_field"] == "stance_duration_ms"   # D2
    assert agg["require_every_attempt"] is True and agg["require_non_overlapping_attempt_windows"] is True  # D2a
    assert m["summary"] == {**m["summary"], "derivable": 0, "partial": 2, "non_evaluable": 4, "total": 6}


def test_v2_keeps_non_gait_criteria_text_identical_to_v1() -> None:
    v1 = json.loads(_V1.read_text(encoding="utf-8"))["criteria"]
    v2 = json.loads(_V2.read_text(encoding="utf-8"))["criteria"]
    assert set(v1) == set(v2)
    for cid in v1:
        if cid == "gait_type":
            continue
        a = {k: v for k, v in v1[cid].items() if k != "mapping_rule_version"}
        b = {k: v for k, v in v2[cid].items() if k != "mapping_rule_version"}
        assert a == b, f"{cid} text drifted between v1 and v2"


@pytest.mark.parametrize("fixture_path", _runnable(), ids=lambda p: p.name)
def test_v1_v2_pair_identity_on_synthetic_fixture(fixture_path: Path) -> None:
    r1, r2 = _run(fixture_path, "v1"), _run(fixture_path, "v2")
    assert r1.fixture_id == r2.fixture_id
    assert r1.spec_id == r2.spec_id and r1.harness_version == r2.harness_version
    assert r1.criterion_map_id != r2.criterion_map_id
    assert r1.run_id != r2.run_id
    assert r1.mapping_spec_version == "v1" and r2.mapping_spec_version == "v2"


def test_v2_on_synthetic_fixtures_refuses_gait_without_stance_window() -> None:
    """Synthetic v1 fixtures carry no stance window, so under v2 gait_type is
    non-evaluable naming the missing construct — never labelled from the
    stable-phase duration."""
    for fp in _runnable():
        r2 = _run(fp, "v2")
        assert "gait_type" not in {c["criterion_id"] for c in r2.criterion_evaluations}, fp.name
        ne = {c["criterion_id"]: c["non_evaluable_reason"] for c in r2.non_evaluable_criteria}
        assert "gait_type" in ne, fp.name
        assert "stance_duration_ms" in ne["gait_type"] or "postural_stability_index" in ne["gait_type"] or "gait_temporal_control" in ne["gait_type"], (fp.name, ne["gait_type"])


def test_v2_golden_vectors_match() -> None:
    golden = json.loads(_GOLDEN_V2.read_text(encoding="utf-8"))
    runnable = {p.name: p for p in _runnable()}
    assert set(golden) - set(runnable) == {"excluded_capture_negative_control.json"}
    assert set(runnable) <= set(golden), f"v2 golden missing: {sorted(set(runnable) - set(golden))}"
    for name, expected in golden.items():
        if expected.get("expects_exception"):
            with pytest.raises(ExcludedCaptureError):
                _run(_FIXTURES_DIR / name, "v2")
            continue
        rep = _run(runnable[name], "v2")
        assert rep.fixture_id == expected["fixture_id"], name
        assert rep.output_hash == expected["output_hash"], name


def test_v2_replay_and_v1_recall_coexist_in_one_store(tmp_path: Path) -> None:
    fp = _FIXTURES_DIR / "clean_older_02_20s.json"
    text = fp.read_text(encoding="utf-8")
    r1, r2 = _run(fp, "v1"), _run(fp, "v2")
    lake = tmp_path / "lake"
    ingest(r1, text, lake)
    ingest(r2, text, lake)
    assert verify_replay(r1.run_id, lake) and verify_replay(r2.run_id, lake)
    assert recall(r1.run_id, lake).output_hash == r1.output_hash
    assert recall(r2.run_id, lake).output_hash == r2.output_hash
    assert r1.output_hash != r2.output_hash
