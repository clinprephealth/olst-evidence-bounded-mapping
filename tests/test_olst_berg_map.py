"""Berg Balance Scale criterion map (amendment A15): second-framework test.

Synthetic fixtures only. Asserts the verified item 14 rubric is encoded as
published, the ordinal rule's boundaries and censoring semantics, that the
same EMU is `partial` for Morse gait and `derivable` for Berg item 14, and
map identity across frameworks.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from experiments.olst_nc_replay import PROTOCOL_CENSORED, ExcludedCaptureError, run

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES_DIR = _REPO_ROOT / "experiments" / "olst_nc_replay" / "fixtures"
_SPECS_DIR = _REPO_ROOT / "experiments" / "olst_nc_replay" / "specs"
_BERG = _SPECS_DIR / "NC_CRITERION_EMU_MAP_berg_v1.json"
_GOLDEN = _FIXTURES_DIR / "golden_output_hashes_berg_v1.json"
ITEM14 = "berg_14_standing_on_one_leg"


def _runnable() -> list[Path]:
    return sorted(
        p for p in _FIXTURES_DIR.glob("*.json")
        if not p.name.startswith("golden_output_hashes_") and p.name != "excluded_capture_negative_control.json"
    )


def _run(p: Path, version: str):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return run(p, mapping_spec_version=version)


def _fixture(stance_ms: int, *, protocol: str, ceiling: int | None, stable: bool = True) -> dict:
    fx = json.loads((_FIXTURES_DIR / "clean_older_02_20s.json").read_text(encoding="utf-8"))
    fx["stance_phase"] = {"foot_up_ms": 1000, "touchdown_ms": 1000 + stance_ms, "event_label_source": "OLST_Attempts.csv@v1.0"}
    fx["acquisition_protocol"] = {"protocol_code": protocol, "observation_ceiling_ms": ceiling, "observation_ceiling_source": "test"}
    if not stable:
        fx["stability_phase"] = None
        fx["force_plate"] = None
    return fx


def _item(report, cid: str):
    ev = next((c for c in report.criterion_evaluations if c["criterion_id"] == cid), None)
    ne = next((c for c in report.non_evaluable_criteria if c["criterion_id"] == cid), None)
    return ev, ne


def _write(tmp_path: Path, fx: dict) -> Path:
    p = tmp_path / "f.json"
    p.write_text(json.dumps(fx, sort_keys=True), encoding="utf-8")
    return p


# -------- map content ------------------------------------------------------

def test_berg_map_encodes_verified_rubric() -> None:
    m = json.loads(_BERG.read_text(encoding="utf-8"))
    assert m["framework"] == "Berg Balance Scale"
    assert len(m["criteria"]) == 14
    assert m["summary"] == {**m["summary"], "derivable": 1, "partial": 4, "non_evaluable": 9, "total": 14}
    counts = {"derivable": 0, "partial": 0, "non_evaluable": 0}
    for c in m["criteria"].values():
        counts[c["derivability"]] += 1
    assert counts == {"derivable": 1, "partial": 4, "non_evaluable": 9}
    i14 = m["criteria"][ITEM14]
    assert i14["derivability"] == "derivable"
    assert i14["required_emus"] == ["gait_temporal_control"], "Berg 14 is a duration rubric; sway is not required"
    rv = i14["rubric_verbatim"]
    assert rv["4"] == "able to lift leg independently and hold >10 seconds"
    assert rv["3"] == "able to lift leg independently and hold 5-10 seconds"
    assert rv["2"] == "able to lift leg independently and hold >=3 seconds"
    assert rv["1"].startswith("tries to lift leg unable to hold 3 seconds")
    assert rv["0"] == "unable to try or needs assist to prevent fall"
    levels = {lv["label"]: lv["min_ms"] for lv in i14["rule"]["levels"]}
    assert levels == {"score_4": 10001, "score_3": 5000, "score_2": 3000}
    assert i14["rule"]["floor_label"] == "score_1_or_0_unresolved"
    assert i14["rule"]["protocol_censoring"] is True
    assert "aggregation" not in m, "Berg is per-attempt; no best-of declared"
    # partial items name the condition difference
    for cid in ("berg_02_standing_unsupported", "berg_06_standing_eyes_closed", "berg_07_standing_feet_together", "berg_13_standing_one_foot_in_front"):
        assert m["criteria"][cid]["derivability"] == "partial" and m["criteria"][cid]["partial_reason"]


def test_same_emu_partial_for_morse_gait_derivable_for_berg_14(tmp_path: Path) -> None:
    p = _write(tmp_path, _fixture(12000, protocol="TRLGL", ceiling=20000))
    morse = _item(_run(p, "v2.1"), "gait_type")[0]
    berg = _item(_run(p, "berg_v1"), ITEM14)[0]
    assert morse["derivability"] == "partial" and morse["evaluation"] == "normal"
    assert berg["derivability"] == "derivable" and berg["evaluation"] == "score_4"


# -------- ordinal rule semantics -------------------------------------------

@pytest.mark.parametrize(
    "stance_ms,expected",
    [
        (12000, "score_4"),
        (10001, "score_4"),
        (10000, "score_3"),      # rubric says >10 seconds: exactly 10.000 s is not > 10 s
        (5000, "score_3"),
        (4999, "score_2"),
        (3000, "score_2"),
        (2999, "score_1_or_0_unresolved"),
        (500, "score_1_or_0_unresolved"),
    ],
)
def test_berg_14_levels_under_permissive_ceiling(tmp_path: Path, stance_ms: int, expected: str) -> None:
    p = _write(tmp_path, _fixture(stance_ms, protocol="TRLGL", ceiling=20000))
    ev, ne = _item(_run(p, "berg_v1"), ITEM14)
    assert ne is None and ev["evaluation"] == expected, (stance_ms, ev, ne)
    assert ev["detail"]["duration_ms"] == stance_ms
    assert ev["detail"]["unobservable_thresholds_ms"] == []


@pytest.mark.parametrize(
    "stance_ms,expected",
    [
        (2000, "score_1_or_0_unresolved"),   # 3000 boundary observable under 4000: failure to hold 3 s is established
        (3500, PROTOCOL_CENSORED),           # could be 2, 3 or 4
        (4800, PROTOCOL_CENSORED),
        (6340, PROTOCOL_CENSORED),           # observed maxima exceed the cue; still censored
    ],
)
def test_berg_14_under_sourced_4s_ceiling(tmp_path: Path, stance_ms: int, expected: str) -> None:
    p = _write(tmp_path, _fixture(stance_ms, protocol="MNTRL", ceiling=4000))
    ev, _ = _item(_run(p, "berg_v1"), ITEM14)
    assert ev["evaluation"] == expected, (stance_ms, ev)
    assert ev["detail"]["unobservable_thresholds_ms"] == [10001, 5000]


@pytest.mark.parametrize("stance_ms", [500, 3500, 12000])
def test_berg_14_null_ceiling_censors_every_level(tmp_path: Path, stance_ms: int) -> None:
    p = _write(tmp_path, _fixture(stance_ms, protocol="MNTRL", ceiling=None))
    ev, _ = _item(_run(p, "berg_v1"), ITEM14)
    assert ev["evaluation"] == PROTOCOL_CENSORED
    assert ev["detail"]["attained_level"] is not None and ev["detail"]["duration_ms"] == stance_ms


def test_berg_14_does_not_need_a_stable_phase(tmp_path: Path) -> None:
    """Berg 14 requires only the stance interval, so an attempt with no t_stable
    (no CoP EMU) is still scored; Morse gait on the same fixture stays
    non-evaluable because its map requires the sway EMU."""
    p = _write(tmp_path, _fixture(7000, protocol="TRLGR", ceiling=20000, stable=False))
    ev, ne = _item(_run(p, "berg_v1"), ITEM14)
    assert ne is None and ev["evaluation"] == "score_3"
    m_ev, m_ne = _item(_run(p, "v2.1"), "gait_type")
    assert m_ev is None and "postural_stability_index" in m_ne["non_evaluable_reason"]


def test_berg_14_without_stance_window_is_non_evaluable() -> None:
    for fp in _runnable():
        ev, ne = _item(_run(fp, "berg_v1"), ITEM14)
        assert ev is None and ne is not None, fp.name
        assert "stance_duration_ms" in ne["non_evaluable_reason"] or "gait_temporal_control" in ne["non_evaluable_reason"], fp.name


# -------- identity ---------------------------------------------------------

@pytest.mark.parametrize("fixture_path", _runnable(), ids=lambda p: p.name)
def test_berg_and_morse_v21_pair_identity(fixture_path: Path) -> None:
    r_m, r_b = _run(fixture_path, "v2.1"), _run(fixture_path, "berg_v1")
    assert r_m.fixture_id == r_b.fixture_id
    assert r_m.spec_id == r_b.spec_id and r_m.harness_version == r_b.harness_version
    assert r_m.criterion_map_id != r_b.criterion_map_id and r_m.run_id != r_b.run_id


def test_berg_golden_vectors_match() -> None:
    golden = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    runnable = {p.name: p for p in _runnable()}
    assert set(runnable) <= set(golden)
    for name, expected in golden.items():
        if expected.get("expects_exception"):
            with pytest.raises(ExcludedCaptureError):
                _run(_FIXTURES_DIR / name, "berg_v1")
            continue
        rep = _run(runnable[name], "berg_v1")
        assert rep.fixture_id == expected["fixture_id"], name
        assert rep.output_hash == expected["output_hash"], name
