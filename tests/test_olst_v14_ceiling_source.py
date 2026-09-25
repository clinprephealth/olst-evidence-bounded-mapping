"""Spec v1.4 (amendment A14): the MNTR* observation ceiling is a sourced
4000 ms instead of null. Not a map change. Synthetic fixtures only; the
real-fixture consequences are asserted in test_olst_full_corpus_store.py
once the __spec1.4 artifacts exist.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from experiments.olst_nc_replay import PROTOCOL_CENSORED, run
from experiments.olst_nc_replay.olst_real_loader import _ACQUISITION_PROTOCOL, _acquisition_protocol

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES_DIR = _REPO_ROOT / "experiments" / "olst_nc_replay" / "fixtures"


def test_loader_table_carries_sourced_ceilings() -> None:
    for code in ("MNTRL", "MNTRR"):
        p = _acquisition_protocol(code)
        assert p["observation_ceiling_ms"] == 4000
        assert "10.1016/j.gaitpost.2026.110108" in p["observation_ceiling_source"]
        assert "4 s" in p["observation_ceiling_source"]
    for code in ("TRLGL", "TRLGR"):
        p = _acquisition_protocol(code)
        assert p["observation_ceiling_ms"] == 20000
        assert "20-second" in p["observation_ceiling_source"]
    assert set(_ACQUISITION_PROTOCOL) == {"MNTRL", "MNTRR", "TRLGL", "TRLGR"}
    with pytest.raises(ValueError):
        _acquisition_protocol("XXXXX")


def _fixture(stance_ms: int, sway: float, ceiling: int | None) -> dict:
    fx = json.loads((_FIXTURES_DIR / "clean_older_02_20s.json").read_text(encoding="utf-8"))
    fx["force_plate"]["sway_area_mm2"] = sway
    fx["stance_phase"] = {"foot_up_ms": 1000, "touchdown_ms": 1000 + stance_ms, "event_label_source": "OLST_Attempts.csv@v1.0"}
    fx["acquisition_protocol"] = {"protocol_code": "MNTRL", "observation_ceiling_ms": ceiling, "observation_ceiling_source": "test"}
    return fx


def _gait(report):
    return next((c for c in report.criterion_evaluations if c["criterion_id"] == "gait_type"), None)


@pytest.mark.parametrize("stance_ms", [980, 4800, 5200, 6340])
def test_sub_5s_ceiling_censors_every_duration_threshold(tmp_path: Path, stance_ms: int) -> None:
    """A14: ceiling 4000 < weak_min 5000 -> no duration category observable ->
    protocol_censored, identical outcome to the null ceiling, under v2.1."""
    p_null = tmp_path / "null.json"
    p_4000 = tmp_path / "c4000.json"
    p_null.write_text(json.dumps(_fixture(stance_ms, 100.0, None), sort_keys=True), encoding="utf-8")
    p_4000.write_text(json.dumps(_fixture(stance_ms, 100.0, 4000), sort_keys=True), encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        r_null = run(p_null, mapping_spec_version="v2.1")
        r_4000 = run(p_4000, mapping_spec_version="v2.1")
    g_null, g_4000 = _gait(r_null), _gait(r_4000)
    assert g_null["evaluation"] == g_4000["evaluation"] == PROTOCOL_CENSORED
    assert g_4000["detail"]["unobservable_thresholds_ms"] == [10000, 5000]
    assert g_4000["detail"]["observation_ceiling_ms"] == 4000
    assert g_4000["detail"]["duration_ms"] == stance_ms
    # same decision, different evidence identity
    assert r_null.fixture_id != r_4000.fixture_id
    assert r_null.output_hash != r_4000.output_hash


def test_sub_5s_ceiling_under_v2_is_still_overridden_by_sway(tmp_path: Path) -> None:
    p = tmp_path / "f.json"
    p.write_text(json.dumps(_fixture(4800, 1800.0, 4000), sort_keys=True), encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        assert _gait(run(p, mapping_spec_version="v2"))["evaluation"] == "impaired"
        assert _gait(run(p, mapping_spec_version="v2.1"))["evaluation"] == PROTOCOL_CENSORED
