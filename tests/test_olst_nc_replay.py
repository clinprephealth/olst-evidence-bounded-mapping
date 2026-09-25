"""OLST/NC replay benchmark tests.

Asserted invariants:
  • O-CI-0 determinism: same fixture + same spec version → same output_hash, every run.
  • Golden vector stability: committed fixture_id and output_hash do not drift.
  • Exclusion gate: 12_MNTRL_V2 raises ExcludedCaptureError before any EMU work.
  • Schema discipline: missing required top-level fields raise FixtureSchemaError.
  • Gap visibility: missing source data → non-evaluable criteria with reason, never imputation.
  • Traceability completeness: every derivable / partial criterion has ≥1 evidence pointer;
    every non-evaluable criterion has a non-empty reason.

Determinism N is configurable via OLST_DETERMINISM_N env var (default 50).
The paper's reported number is whatever value was passed at run time —
the test prints the actual N so the claim isn't hardcoded.
"""

from __future__ import annotations

import json
import os
import warnings
from pathlib import Path

import pytest

from experiments.olst_nc_replay import (
    ExcludedCaptureError,
    FixtureSchemaError,
    UnknownMappingSpecVersionError,
    run,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES_DIR = _REPO_ROOT / "experiments" / "olst_nc_replay" / "fixtures"
_GOLDEN_PATH = _FIXTURES_DIR / "golden_output_hashes_v1.json"

_NEGATIVE_CONTROL = "excluded_capture_negative_control.json"

_DETERMINISM_N = int(os.environ.get("OLST_DETERMINISM_N", "50"))


def _load_golden() -> dict[str, dict]:
    return json.loads(_GOLDEN_PATH.read_text(encoding="utf-8"))


def _runnable_fixtures() -> list[Path]:
    """All fixtures except the exclusion negative control."""
    return sorted(
        p for p in _FIXTURES_DIR.glob("*.json")
        if p.name != _NEGATIVE_CONTROL.split("/")[-1] and not p.name.startswith("golden_output_hashes_")
    )


# -------- determinism ------------------------------------------------------

@pytest.mark.parametrize("fixture_path", _runnable_fixtures(), ids=lambda p: p.name)
def test_replay_is_deterministic(fixture_path: Path) -> None:
    """Run each fixture N times; output_hash is identical across all runs.

    With OLST_DETERMINISM_N=1000 the paper claims 1000-run stability; default 50 is for CI.
    """
    hashes: set[str] = set()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # dataset_version mismatch noise
        for _ in range(_DETERMINISM_N):
            report = run(fixture_path, mapping_spec_version="v1")
            hashes.add(report.output_hash)
    assert len(hashes) == 1, (
        f"Replay determinism failure on {fixture_path.name}: "
        f"got {len(hashes)} distinct output_hash values across N={_DETERMINISM_N} runs."
    )


def test_determinism_N_is_reported(capsys: pytest.CaptureFixture[str]) -> None:
    """Make N visible in the test session output so the paper cites the actual value."""
    print(f"\n[OLST] determinism N = {_DETERMINISM_N}")


# -------- golden vectors ---------------------------------------------------

def test_golden_vectors_match() -> None:
    """fixture_id (content sha256) and output_hash committed in golden file are stable."""
    golden = _load_golden()
    runnable = {p.name: p for p in _runnable_fixtures()}
    for name, expected in golden.items():
        if expected.get("expects_exception"):
            continue  # exclusion control covered separately
        assert name in runnable, f"Golden references missing fixture {name!r}"
        report = run(runnable[name], mapping_spec_version="v1")
        assert report.fixture_id == expected["fixture_id"], (
            f"Fixture content drift on {name}: "
            f"expected fixture_id {expected['fixture_id']}, got {report.fixture_id}. "
            f"Either regenerate fixtures or the file was edited by hand."
        )
        assert report.output_hash == expected["output_hash"], (
            f"Output hash drift on {name}: expected {expected['output_hash']}, "
            f"got {report.output_hash}."
        )


def test_golden_covers_every_runnable_fixture() -> None:
    golden = _load_golden()
    runnable_names = {p.name for p in _runnable_fixtures()}
    runnable_names.add(_NEGATIVE_CONTROL)
    missing = runnable_names - set(golden)
    assert not missing, f"Golden file missing entries for: {sorted(missing)}"


# -------- exclusion gate ---------------------------------------------------

def test_excluded_capture_raises_before_emu_derivation() -> None:
    fp = _FIXTURES_DIR / _NEGATIVE_CONTROL
    with pytest.raises(ExcludedCaptureError) as excinfo:
        run(fp, mapping_spec_version="v1")
    assert "12_MNTRL_V2" in str(excinfo.value)
    assert "PhysioNet" in str(excinfo.value) or "data collection error" in str(excinfo.value).lower()


# -------- schema discipline ------------------------------------------------

@pytest.mark.parametrize(
    "drop_field,expected_message_contains",
    [
        ("participant_id", "participant_id"),
        ("capture_id", "capture_id"),
        ("dataset_version", "dataset_version"),
    ],
)
def test_missing_required_field_raises_fixture_schema_error(
    drop_field: str, expected_message_contains: str, tmp_path: Path
) -> None:
    base = json.loads(
        (_FIXTURES_DIR / "clean_young_01.json").read_text(encoding="utf-8")
    )
    base.pop(drop_field, None)
    p = tmp_path / "broken.json"
    p.write_text(json.dumps(base), encoding="utf-8")
    with pytest.raises(FixtureSchemaError) as excinfo:
        run(p, mapping_spec_version="v1")
    assert expected_message_contains in str(excinfo.value)


def test_dataset_version_mismatch_warns_and_continues(tmp_path: Path) -> None:
    base = json.loads(
        (_FIXTURES_DIR / "clean_young_01.json").read_text(encoding="utf-8")
    )
    base["dataset_version"] = "0.9"
    p = tmp_path / "old_version.json"
    p.write_text(json.dumps(base), encoding="utf-8")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        report = run(p, mapping_spec_version="v1")
    assert report.output_hash, "should produce a result, not a silent skip"
    assert any(
        issubclass(w.category, UserWarning) and "0.9" in str(w.message) for w in caught
    ), f"Expected UserWarning about dataset_version=0.9; got: {[str(w.message) for w in caught]}"


# -------- gap visibility ---------------------------------------------------

def test_missing_fp_channel_yields_non_evaluable_gait_type() -> None:
    """When postural_stability_index can't be derived, gait_type must be non_evaluable."""
    fp = _FIXTURES_DIR / "missing_fp_channel.json"
    report = run(fp, mapping_spec_version="v1")
    eval_ids = {c["criterion_id"] for c in report.criterion_evaluations}
    non_eval_ids = {c["criterion_id"] for c in report.non_evaluable_criteria}
    assert "gait_type" in non_eval_ids, "gait_type should be non_evaluable when FP missing"
    assert "gait_type" not in eval_ids, "gait_type must not be evaluated with imputed values"
    reason = next(
        c["non_evaluable_reason"] for c in report.non_evaluable_criteria if c["criterion_id"] == "gait_type"
    )
    assert "postural_stability_index" in reason, (
        f"Non-evaluable reason should name the missing EMU; got: {reason}"
    )


def test_missing_mocap_events_yields_non_evaluable_gait_and_aids() -> None:
    fp = _FIXTURES_DIR / "missing_mocap_events.json"
    report = run(fp, mapping_spec_version="v1")
    non_eval_ids = {c["criterion_id"] for c in report.non_evaluable_criteria}
    assert "gait_type" in non_eval_ids
    assert "ambulatory_aids" in non_eval_ids


def test_no_imputation_in_non_evaluable_outputs() -> None:
    """Every non-evaluable result carries a non-empty `non_evaluable_reason` and no `evaluation`."""
    for fp in _runnable_fixtures():
        report = run(fp, mapping_spec_version="v1")
        for entry in report.non_evaluable_criteria:
            assert entry.get("non_evaluable_reason"), (
                f"{fp.name}: non-evaluable {entry['criterion_id']} missing reason"
            )
            assert "evaluation" not in entry, (
                f"{fp.name}: non-evaluable {entry['criterion_id']} unexpectedly carries 'evaluation'"
            )


# -------- traceability completeness ---------------------------------------

def test_every_evaluated_criterion_has_evidence_pointer() -> None:
    """Derivable + partial criteria → ≥1 traceability entry naming a real EMU."""
    for fp in _runnable_fixtures():
        report = run(fp, mapping_spec_version="v1")
        emu_ids = {e["emu_id"] for e in report.emu_outputs}
        for ev in report.criterion_evaluations:
            cid = ev["criterion_id"]
            entries = report.traceability.get(cid, [])
            assert entries, f"{fp.name}: criterion {cid} evaluated but has no traceability"
            for entry in entries:
                assert entry.emu_id in emu_ids, (
                    f"{fp.name}: traceability for {cid} points at unknown EMU {entry.emu_id}"
                )
                assert entry.payload_hash, f"{fp.name}: traceability missing payload_hash"
                assert entry.rule_version, f"{fp.name}: traceability missing rule_version"


def test_traceability_payload_hash_matches_emu_payload_hash() -> None:
    """Cross-check that traceability entries carry the EMU's actual payload_hash."""
    for fp in _runnable_fixtures():
        report = run(fp, mapping_spec_version="v1")
        emu_by_id = {e["emu_id"]: e for e in report.emu_outputs}
        for cid, entries in report.traceability.items():
            for entry in entries:
                assert entry.payload_hash == emu_by_id[entry.emu_id]["payload_hash"], (
                    f"{fp.name}: payload_hash drift for {entry.emu_id} in criterion {cid}"
                )


# -------- output_hash scope --------------------------------------------------

def test_run_id_is_deterministic_across_runs() -> None:
    fp = _FIXTURES_DIR / "clean_young_01.json"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        r1 = run(fp, mapping_spec_version="v1")
        r2 = run(fp, mapping_spec_version="v1")
    assert r1.run_id == r2.run_id, "run_id must be deterministic across runs"
    assert r1.run_id, "run_id must be populated"


def test_run_id_distinct_from_fixture_id_and_output_hash() -> None:
    fp = _FIXTURES_DIR / "clean_young_01.json"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        r = run(fp, mapping_spec_version="v1")
    assert r.run_id != r.fixture_id, "run_id (input bundle) must be distinct from fixture_id (fixture content)"
    assert r.run_id != r.output_hash, "run_id (input bundle) must be distinct from output_hash (output bundle)"


def test_spec_id_is_recomputed_on_every_call(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """spec_id() must hash the spec file as it currently exists on disk, not a
    value cached at import. Editing the spec between two runs in the same
    process must surface as a different run_id without requiring re-import.
    This is the spec-drift detection guarantee the methods section depends on.
    """
    import experiments.olst_nc_replay.olst_replay_harness as h

    # Snapshot the real spec, point the module path at a tmp file we can edit.
    real_spec = h._CANONICALIZATION_SPEC_PATH
    fake_spec = tmp_path / "fake_spec.md"
    fake_spec.write_text("# spec content A\n", encoding="utf-8")
    monkeypatch.setattr(h, "_CANONICALIZATION_SPEC_PATH", fake_spec)

    id_a = h.spec_id()
    fake_spec.write_text("# spec content B (edited mid-process)\n", encoding="utf-8")
    id_b = h.spec_id()
    assert id_a != id_b, (
        "spec_id() must re-hash the file on every call; got the same digest "
        "for two different file contents — module-level caching has crept back."
    )

    # And: a real run() call after the edit produces a different run_id than before.
    fp = _FIXTURES_DIR / "clean_young_01.json"
    fake_spec.write_text("# spec content A\n", encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        r_a = run(fp, mapping_spec_version="v1")
    fake_spec.write_text("# spec content B\n", encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        r_b = run(fp, mapping_spec_version="v1")
    assert r_a.run_id != r_b.run_id, (
        "run_id must change when the spec file changes between two runs in the "
        "same process. Spec-drift detection has regressed."
    )
    assert r_a.spec_id != r_b.spec_id

    # Cleanup: monkeypatch.setattr restores _CANONICALIZATION_SPEC_PATH for
    # subsequent tests; nothing further to do.
    _ = real_spec


def test_criterion_map_id_is_recomputed_on_every_call(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Same drift-detection guarantee for the criterion map JSON."""
    import experiments.olst_nc_replay.olst_replay_harness as h

    # Use the real criterion-map JSON content as a base so loading still
    # succeeds when run() reads it; edit the file between calls.
    real_path = h._CRITERION_MAP_PATH
    fake_path = tmp_path / "fake_map.json"
    fake_path.write_text(real_path.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(h, "_CRITERION_MAP_PATH", fake_path)

    id_a = h.criterion_map_id()
    # Append a benign whitespace difference; same parsed content, different bytes.
    fake_path.write_text(fake_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    id_b = h.criterion_map_id()
    assert id_a != id_b, "criterion_map_id() must re-hash on every call."


def test_unknown_mapping_spec_version_raises_not_defaults() -> None:
    """An unknown mapping_spec_version has no map file; the harness must refuse,
    never fall back to v1 (amendment 2026-09-09 A6.3)."""
    fp = _FIXTURES_DIR / "clean_young_01.json"
    with pytest.raises(UnknownMappingSpecVersionError) as excinfo:
        run(fp, mapping_spec_version="v2-hypothetical")
    assert "v2-hypothetical" in str(excinfo.value)


def test_run_id_changes_when_mapping_spec_version_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Same fixture, same map bytes, different mapping_spec_version → different run_id.

    Uses a copy of the v1 map registered under a second version name so the
    test isolates mapping_spec_version from criterion_map_id.
    """
    import experiments.olst_nc_replay.olst_replay_harness as h

    fp = _FIXTURES_DIR / "clean_young_01.json"
    real_resolve = h._criterion_map_path
    alt = tmp_path / "NC_CRITERION_EMU_MAP_vX.json"
    alt.write_text(h._CRITERION_MAP_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    def _resolve(version: str) -> Path:
        return alt if version == "vX" else real_resolve(version)

    monkeypatch.setattr(h, "_criterion_map_path", _resolve)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        r_v1 = run(fp, mapping_spec_version="v1")
        r_vx = run(fp, mapping_spec_version="vX")
    assert r_v1.criterion_map_id == r_vx.criterion_map_id, "same map bytes by construction"
    assert r_v1.run_id != r_vx.run_id, (
        "run_id must change when mapping_spec_version changes — otherwise the "
        "lakehouse cannot distinguish runs across spec amendments."
    )


def test_lakehouse_ingest_recall_round_trip(tmp_path: Path) -> None:
    from experiments.olst_nc_replay.lakehouse import ingest, recall, verify_replay

    lh = tmp_path / "lakehouse"
    fp = _FIXTURES_DIR / "clean_young_01.json"
    fixture_text = fp.read_text(encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        original = run(fp, mapping_spec_version="v1")

    ingest(original, fixture_text, lh, executed_at="2026-05-04T00:00:00Z")
    recalled = recall(original.run_id, lh)
    assert recalled.run_id == original.run_id
    assert recalled.fixture_id == original.fixture_id
    assert recalled.output_hash == original.output_hash
    assert len(recalled.emu_outputs) == len(original.emu_outputs)
    assert len(recalled.criterion_evaluations) == len(original.criterion_evaluations)
    assert len(recalled.non_evaluable_criteria) == len(original.non_evaluable_criteria)
    assert set(recalled.traceability) == set(original.traceability)
    assert verify_replay(original.run_id, lh) is True


def test_lakehouse_ingest_is_idempotent(tmp_path: Path) -> None:
    from experiments.olst_nc_replay.lakehouse import ingest, list_runs

    lh = tmp_path / "lakehouse"
    fp = _FIXTURES_DIR / "clean_young_01.json"
    fixture_text = fp.read_text(encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        rep = run(fp, mapping_spec_version="v1")

    first = ingest(rep, fixture_text, lh)
    second = ingest(rep, fixture_text, lh)
    assert any(v > 0 for v in first.values()), "first ingest must write something"
    assert all(v == 0 for v in second.values()), (
        f"second ingest must be a no-op; got {second}"
    )
    assert len(list_runs(lh)) == 1


def test_lakehouse_separates_runs_by_run_id(tmp_path: Path) -> None:
    """Two different fixtures produce two distinct lakehouse rows."""
    from experiments.olst_nc_replay.lakehouse import ingest, list_runs

    lh = tmp_path / "lakehouse"
    for name in ("clean_young_01.json", "noisy_01.json"):
        fp = _FIXTURES_DIR / name
        fixture_text = fp.read_text(encoding="utf-8")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            rep = run(fp, mapping_spec_version="v1")
        ingest(rep, fixture_text, lh)

    runs = list_runs(lh)
    assert len(runs) == 2
    assert len({r["run_id"] for r in runs}) == 2


def test_lakehouse_verify_replay_detects_fixture_drift(tmp_path: Path) -> None:
    """If the stored fixture_text is corrupted, verify_replay raises."""
    from experiments.olst_nc_replay.lakehouse import ingest, verify_replay

    lh = tmp_path / "lakehouse"
    fp = _FIXTURES_DIR / "clean_young_01.json"
    fixture_text = fp.read_text(encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        rep = run(fp, mapping_spec_version="v1")
    ingest(rep, fixture_text, lh)

    # Tamper the fixtures.jsonl to point at different bytes
    fixtures_path = lh / "fixtures.jsonl"
    rows = [json.loads(line) for line in fixtures_path.read_text(encoding="utf-8").splitlines() if line]
    rows[0]["fixture_text"] = rows[0]["fixture_text"].replace("01_MNTRR_V1", "01_MNTRR_V9")
    fixtures_path.write_text(
        "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in rows) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError):
        verify_replay(rep.run_id, lh)


def test_traceability_drift_changes_output_hash() -> None:
    """Sanity check that traceability is in the output_hash scope: a forged report
    with a tampered traceability entry must hash differently. Exercises the spec §7
    decision to include traceability in the hash.
    """
    from experiments.olst_nc_replay.olst_replay_harness import (
        TraceabilityEntry,
        _output_hash,
    )

    fp = _FIXTURES_DIR / "clean_young_01.json"
    report = run(fp, mapping_spec_version="v1")
    original_hash = report.output_hash

    # Tamper traceability without touching anything else
    first_cid = next(iter(report.traceability))
    report.traceability[first_cid] = [
        TraceabilityEntry(emu_id="forged", payload_hash="0" * 64, rule_version="v1")
    ]
    tampered_hash = _output_hash(report)
    assert tampered_hash != original_hash, (
        "output_hash must include traceability; tampering changed nothing — "
        "the spec §7 invariant has regressed."
    )
