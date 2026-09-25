"""Plan Step 1 / Step 2.4 assertions over the committed full-corpus artifacts.

Skips when the artifacts do not exist yet. Once ``_run_full_corpus.py`` has
produced ``artifacts/olst_full_corpus_v1.json`` (and ``_v2.json``) these
become paper claims:

  * Step 1: every metadata attempt is accounted for by a status; no attempt
    is `source_missing_local`; no determinism divergence at the recorded N.
  * Step 2.4: for every real fixture run under both maps, run_id differs,
    fixture_id / spec_id / harness_version are equal, criterion_map_id differs;
    verify_replay holds on stored runs; recall of a v1 run after v2 ingest
    reproduces the v1 output hash.

Full-store verify_replay over every run is slow (each call re-reads the
streams); by default a seeded sample of 40 runs is verified. Set
OLST_FULL_STORE_VERIFY=1 to verify every run.
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path

import pytest

from experiments.olst_nc_replay.lakehouse import (
    DEFAULT_LAKEHOUSE_DIR,
    list_aggregates,
    list_runs,
    recall,
    verify_replay,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ART = _REPO_ROOT / "artifacts"
_V1 = _ART / "olst_full_corpus_v1.json"
_V1_STEP1 = _ART / "olst_full_corpus_v1__harness_193dba29.json"   # Step 1 run, pre-A12 harness
_V2 = _ART / "olst_full_corpus_v2.json"
_V21 = _ART / "olst_full_corpus_v2.1.json"

pytestmark = pytest.mark.skipif(not (_V1.exists() or _V1_STEP1.exists()), reason="Step 1 artifact not present")

if not _V1.exists() and _V1_STEP1.exists():
    _V1 = _V1_STEP1


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _built(summary: dict) -> dict[tuple[str, int], dict]:
    return {(r["capture_id"], r["attempt_number"]): r for r in summary["rows"] if r["status"] == "built"}


# -------- Step 1 -----------------------------------------------------------

def test_step1_v1_corpus_is_complete_and_deterministic() -> None:
    s = _load(_V1)
    assert s["mapping_spec_version"] == "v1"
    assert s["allow_partial"] is False, "committed Step 1 must run on a complete, verified mirror"
    st = s["statuses"]
    assert st.get("source_missing_local", 0) == 0
    assert s["sources"]["raw"]["mismatch"] == []
    assert s["sources"]["metadata"]["Metadata/OLST_Attempts.csv"]["matches_manifest"]
    assert sum(st.values()) == s["inventory"]["n_attempt_rows"]
    assert s["determinism"]["divergent_fixtures"] == []
    assert s["determinism"]["n_per_fixture"] >= 100
    assert s["inventory"]["n_participants"] == 32
    assert s["inventory"]["n_captures"] == 333
    # release-level gap (spec §6.7): 35_MNTRL_V4 cannot be built; nothing else is refused
    refused = {r["capture_id"] for r in s["rows"] if r["status"] in ("build_refused", "source_missing_upstream")}
    assert refused <= {"35_MNTRL_V4"}, refused


def test_step1_stored_runs_match_artifact_rows() -> None:
    s = _load(_V1)
    stored = {r["run_id"] for r in list_runs(DEFAULT_LAKEHOUSE_DIR)}
    missing = [k for k, r in _built(s).items() if r["run_id"] not in stored]
    assert not missing, f"{len(missing)} v1 runs in the artifact are absent from the store, e.g. {missing[:3]}"


# -------- Step 2.4 ---------------------------------------------------------

@pytest.mark.skipif(not _V2.exists(), reason="Step 2 artifact not present")
def test_step2_v1_v2_pairs_share_fixture_and_harness_but_not_map_or_run_id() -> None:
    s1, s2 = _load(_V1), _load(_V2)
    assert s1["identity"]["harness_version"] == s2["identity"]["harness_version"]
    assert s1["identity"]["spec_id"] == s2["identity"]["spec_id"]
    assert s1["identity"]["criterion_map_id"] != s2["identity"]["criterion_map_id"]
    b1, b2 = _built(s1), _built(s2)
    assert set(b1) == set(b2), "the two maps must have been run over the same attempts"
    for key in b1:
        assert b1[key]["fixture_id"] == b2[key]["fixture_id"], key
        assert b1[key]["run_id"] != b2[key]["run_id"], key


@pytest.mark.skipif(not (_V1_STEP1.exists() and (_ART / "olst_full_corpus_v1.json").exists()), reason="v1 rerun under the A12 harness not present")
def test_a12_harness_flag_is_inert_for_v1_on_every_real_fixture() -> None:
    """The A12 harness change (sway_gating flag) must not alter any v1 output:
    the v1 rerun reproduces the Step 1 output_hash fixture by fixture, with a
    different harness_version and therefore different run_id."""
    s_old, s_new = _load(_V1_STEP1), _load(_ART / "olst_full_corpus_v1.json")
    assert s_old["identity"]["harness_version"] != s_new["identity"]["harness_version"]
    assert s_old["identity"]["spec_id"] == s_new["identity"]["spec_id"]
    assert s_old["identity"]["criterion_map_id"] == s_new["identity"]["criterion_map_id"]
    b_old, b_new = _built(s_old), _built(s_new)
    assert set(b_old) == set(b_new)
    for key in b_old:
        assert b_old[key]["fixture_id"] == b_new[key]["fixture_id"], key
        assert b_old[key]["output_hash"] == b_new[key]["output_hash"], key
        assert b_old[key]["run_id"] != b_new[key]["run_id"], key


@pytest.mark.skipif(not (_V2.exists() and _V21.exists()), reason="Step 2 v2.1 artifact not present")
def test_step2_v2_v21_pairs_share_fixture_and_harness_but_not_map_or_run_id() -> None:
    s2, s21 = _load(_V2), _load(_V21)
    assert s2["identity"]["harness_version"] == s21["identity"]["harness_version"]
    assert s2["identity"]["spec_id"] == s21["identity"]["spec_id"]
    assert s2["identity"]["criterion_map_id"] != s21["identity"]["criterion_map_id"]
    b2, b21 = _built(s2), _built(s21)
    assert set(b2) == set(b21)
    for key in b2:
        assert b2[key]["fixture_id"] == b21[key]["fixture_id"], key
        assert b2[key]["run_id"] != b21[key]["run_id"], key
    # v2.1 never emits a label on a sway-only basis: every v2.1 gait label is a
    # function of the duration detail alone, and sway is still reported.
    for r in b21.values():
        if r["governed_gait"] is not None:
            assert "sway_area_mm2" in r["governed_gait_detail"]
            assert r["governed_gait_detail"]["sway_gating"] is False


@pytest.mark.skipif(not _V2.exists(), reason="Step 2 artifact not present")
def test_step2_every_capture_has_a_v2_aggregate() -> None:
    s2 = _load(_V2)
    built_caps = {k[0] for k in _built(s2)}
    aggs = [a for a in list_aggregates(DEFAULT_LAKEHOUSE_DIR) if a["mapping_spec_version"] == "v2"]
    assert {a["capture_id"] for a in aggs} >= built_caps
    # several v2 execution contexts (spec v1.3, v1.4) may be in the store; judge per capture
    overlapping = sorted({a["capture_id"] for a in aggs if not a["evaluable"] and "overlap" in (a["non_evaluable_reason"] or "")})
    # 47_TRLGL_V4: final row spans the capture (A4). 56_TRLGL_V4: 350 ms boundary
    # overlap between an1 and an2, found by the aggregate check, not by the
    # attempt-order check (A13). Any overlap withholds the aggregate; no tolerance.
    assert overlapping == ["47_TRLGL_V4", "56_TRLGL_V4"], overlapping
    assert all(a["evaluable"] for a in aggs if a["capture_id"] not in overlapping)


# -------- A14: spec v1.4 execution context ---------------------------------

_S14 = {v: _ART / f"olst_full_corpus_{v}__spec1.4.json" for v in ("v1", "v2", "v2.1")}


@pytest.mark.skipif(not all(p.exists() for p in _S14.values()) or not _V21.exists(), reason="spec v1.4 artifacts not present")
def test_a14_better_acquisition_metadata_changes_identity_not_decision() -> None:
    """Same measurements, sourced MNTR ceiling: MNTR fixtures get new
    fixture_ids and unchanged labels; TRLG fixtures are byte-identical with
    identical output_hash; every run_id differs through spec_id; harness and
    map identities are unchanged."""
    for v, p14 in _S14.items():
        s13 = _load(_ART / f"olst_full_corpus_{v}.json")
        s14 = _load(p14)
        assert s13["identity"]["harness_version"] == s14["identity"]["harness_version"]
        assert s13["identity"]["criterion_map_id"] == s14["identity"]["criterion_map_id"]
        assert s13["identity"]["spec_id"] != s14["identity"]["spec_id"]
        assert s14["determinism"]["divergent_fixtures"] == []
        b13, b14 = _built(s13), _built(s14)
        assert set(b13) == set(b14)
        for key, r13 in b13.items():
            r14 = b14[key]
            assert r13["run_id"] != r14["run_id"], key
            assert r13["governed_gait"] == r14["governed_gait"], (v, key)
            assert r13["governed_gait_non_evaluable_reason"] == r14["governed_gait_non_evaluable_reason"], (v, key)
            if r13["protocol_code"].startswith("TRLG"):
                assert r13["fixture_id"] == r14["fixture_id"], key
                assert r13["output_hash"] == r14["output_hash"], key
            else:
                assert r13["fixture_id"] != r14["fixture_id"], key
                assert r14["observation_ceiling_ms"] == 4000, key
    s14 = _load(_S14["v2.1"])
    mntr = [r for r in _built(s14).values() if r["protocol_code"].startswith("MNTR") and r["governed_gait"] is not None]
    assert mntr and all(r["governed_gait"] == "protocol_censored" for r in mntr)
    assert all(r["governed_gait_detail"]["unobservable_thresholds_ms"] == [10000, 5000] for r in mntr)


# -------- A15: Berg on the spec v1.4 fixtures --------------------------------

_BERG = _ART / "olst_full_corpus_berg_v1__spec1.4.json"


@pytest.mark.skipif(not (_BERG.exists() and _S14["v2.1"].exists()), reason="Berg artifact not present")
def test_a15_berg_item14_versus_morse_gait_on_the_same_attempts() -> None:
    sb, sm = _load(_BERG), _load(_S14["v2.1"])
    # identity: same fixtures and spec as the A14 v2.1 run; different map and harness
    assert sb["identity"]["spec_id"] == sm["identity"]["spec_id"]
    assert sb["identity"]["criterion_map_id"] != sm["identity"]["criterion_map_id"]
    assert sb["identity"]["harness_version"] != sm["identity"]["harness_version"], "A15: harness change is the reported fact"
    assert sb["determinism"]["divergent_fixtures"] == []
    bb, bm = _built(sb), _built(sm)
    assert set(bb) == set(bm)
    for key in bb:
        assert bb[key]["fixture_id"] == bm[key]["fixture_id"], key
    # item 14 is scorable on every built attempt (only the stance window is required)
    assert all(r["governed_gait"] is not None for r in bb.values()), "the driver reports the map's duration criterion under governed_gait"
    mntr = [r for r in bb.values() if r["protocol_code"].startswith("MNTR")]
    trlg = [r for r in bb.values() if r["protocol_code"].startswith("TRLG")]
    assert {r["governed_gait"] for r in mntr} <= {"protocol_censored", "score_1_or_0_unresolved"}
    assert {r["governed_gait"] for r in trlg} <= {"score_4", "score_3", "score_2", "score_1_or_0_unresolved"}
    # the 151 attempts with no stable phase: non-evaluable for Morse gait, scored for Berg 14
    no_stable = [k for k, r in bm.items() if not r["stability_phase_present"]]
    assert len(no_stable) == 151
    assert all(bm[k]["governed_gait"] is None for k in no_stable)
    assert all(bb[k]["governed_gait"] is not None for k in no_stable)


def test_stored_runs_replay_bit_for_bit() -> None:
    runs = list_runs(DEFAULT_LAKEHOUSE_DIR)
    if os.environ.get("OLST_FULL_STORE_VERIFY") == "1":
        sample = runs
    else:
        rng = random.Random(20260909)
        sample = rng.sample(runs, min(40, len(runs)))
    for row in sample:
        assert verify_replay(row["run_id"], DEFAULT_LAKEHOUSE_DIR), row["run_id"]


@pytest.mark.skipif(not _V2.exists(), reason="Step 2 artifact not present")
def test_recall_of_v1_after_v2_ingest_reproduces_v1_hash() -> None:
    s1 = _load(_V1)
    rows = list(_built(s1).values())
    rng = random.Random(20260909)
    for r in rng.sample(rows, min(25, len(rows))):
        rep = recall(r["run_id"], DEFAULT_LAKEHOUSE_DIR)
        assert rep.output_hash == r["output_hash"]
        assert rep.mapping_spec_version == "v1"
