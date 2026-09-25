"""Local lakehouse for OLST/NC replay reports.

Five JSONL streams keyed by content hash so writes are idempotent:

  runs.jsonl                    run_id → ReplayReport summary + executed_at
  emus.jsonl                    (run_id, emu_id) → payload + payload_hash + provenance
  criterion_evaluations.jsonl   (run_id, criterion_id) → evaluation + evidence pointers
  non_evaluable.jsonl           (run_id, criterion_id) → non_evaluable_reason
  fixtures.jsonl                fixture_id → exact UTF-8 fixture bytes

Recall round-trip:
  ``ingest(report, fixture_text)`` writes all five streams; re-ingesting the
  same run is a no-op.
  ``recall(run_id)`` returns the stored ReplayReport rebuilt from the streams.
  ``verify_replay(run_id)`` reads the stored fixture, re-runs through the
  harness, and asserts the new output_hash matches the stored one — bit-for-bit
  reproduction is testable, not assumed.

The default lakehouse directory is ``<repo_root>/artifacts/olst_lakehouse/``.
"""

from __future__ import annotations

import datetime as _dt
import json
import tempfile
import warnings
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from experiments.olst_nc_replay.olst_replay_harness import (
    ReplayReport,
    TraceabilityEntry,
    run as _harness_run,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LAKEHOUSE_DIR: Path = _REPO_ROOT / "artifacts" / "olst_lakehouse"

_RUNS = "runs.jsonl"
_EMUS = "emus.jsonl"
_EVALUATIONS = "criterion_evaluations.jsonl"
_NON_EVALUABLE = "non_evaluable.jsonl"
_FIXTURES = "fixtures.jsonl"
# Sixth stream (2026-09-09): capture-level aggregates from olst_capture_aggregate,
# keyed by aggregate_id. Per-attempt runs remain the unit of replay; an
# aggregate points at its constituent run_ids.
_AGGREGATES = "capture_aggregates.jsonl"


# -------- JSONL helpers ----------------------------------------------------

def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            out.append(json.loads(line))
    return out


def _append_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    """Append rows in order. Caller is responsible for de-duplication."""
    rows = list(rows)
    if not rows:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")))
            f.write("\n")
    return len(rows)


def _existing_keys(path: Path, key_fn) -> set:
    return {key_fn(row) for row in _read_jsonl(path)}


# -------- ingest -----------------------------------------------------------

def _utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_summary(report: ReplayReport, executed_at: str | None) -> dict[str, Any]:
    return {
        "run_id": report.run_id,
        "fixture_id": report.fixture_id,
        "capture_id": report.capture_id,
        "participant_id": report.participant_id,
        "dataset_version": report.dataset_version,
        "spec_id": report.spec_id,
        "criterion_map_id": report.criterion_map_id,
        "harness_version": report.harness_version,
        "mapping_spec_version": report.mapping_spec_version,
        "output_hash": report.output_hash,
        "executed_at": executed_at or _utc_now_iso(),
        "emu_count": len(report.emu_outputs),
        "criterion_evaluation_count": len(report.criterion_evaluations),
        "non_evaluable_count": len(report.non_evaluable_criteria),
        "traceability_pointer_count": sum(len(v) for v in report.traceability.values()),
    }


def ingest(
    report: ReplayReport,
    fixture_text: str,
    lakehouse_dir: Path = DEFAULT_LAKEHOUSE_DIR,
    *,
    executed_at: str | None = None,
) -> dict[str, int]:
    """Write all five streams idempotently. Returns {stream: rows_appended}.

    Args:
        report: a finalized ReplayReport (run_id and output_hash populated).
        fixture_text: the exact UTF-8 string the harness read for this run.
            Stored verbatim so recall reproduces the fixture bytes precisely.
        lakehouse_dir: target directory; created if absent.
        executed_at: optional ISO-8601 UTC timestamp; defaults to now.

    Re-ingesting the same run is a no-op (every stream is keyed by content
    hash and existing keys are skipped).
    """
    if not report.run_id:
        raise ValueError("ReplayReport.run_id is empty; refuse to ingest.")
    lakehouse_dir.mkdir(parents=True, exist_ok=True)

    appended: dict[str, int] = {}

    # 1. runs.jsonl — keyed by run_id
    runs_path = lakehouse_dir / _RUNS
    existing_runs = _existing_keys(runs_path, lambda r: r["run_id"])
    if report.run_id not in existing_runs:
        appended[_RUNS] = _append_jsonl(runs_path, [_run_summary(report, executed_at)])
    else:
        appended[_RUNS] = 0

    # 2. emus.jsonl — keyed by (run_id, emu_id)
    emus_path = lakehouse_dir / _EMUS
    existing_emus = _existing_keys(emus_path, lambda r: (r["run_id"], r["emu_id"]))
    new_emus = []
    for emu in report.emu_outputs:
        key = (report.run_id, emu["emu_id"])
        if key in existing_emus:
            continue
        new_emus.append({"run_id": report.run_id, **emu})
    appended[_EMUS] = _append_jsonl(emus_path, new_emus)

    # 3. criterion_evaluations.jsonl — keyed by (run_id, criterion_id)
    evals_path = lakehouse_dir / _EVALUATIONS
    existing_evals = _existing_keys(evals_path, lambda r: (r["run_id"], r["criterion_id"]))
    new_evals = []
    for ev in report.criterion_evaluations:
        cid = ev["criterion_id"]
        key = (report.run_id, cid)
        if key in existing_evals:
            continue
        evidence = [asdict(e) for e in report.traceability.get(cid, [])]
        new_evals.append({"run_id": report.run_id, "evidence": evidence, **ev})
    appended[_EVALUATIONS] = _append_jsonl(evals_path, new_evals)

    # 4. non_evaluable.jsonl — keyed by (run_id, criterion_id)
    neval_path = lakehouse_dir / _NON_EVALUABLE
    existing_neval = _existing_keys(neval_path, lambda r: (r["run_id"], r["criterion_id"]))
    new_neval = []
    for ne in report.non_evaluable_criteria:
        key = (report.run_id, ne["criterion_id"])
        if key in existing_neval:
            continue
        new_neval.append({"run_id": report.run_id, **ne})
    appended[_NON_EVALUABLE] = _append_jsonl(neval_path, new_neval)

    # 5. fixtures.jsonl — keyed by fixture_id (one row per fixture content)
    fixtures_path = lakehouse_dir / _FIXTURES
    existing_fixtures = _existing_keys(fixtures_path, lambda r: r["fixture_id"])
    if report.fixture_id not in existing_fixtures:
        appended[_FIXTURES] = _append_jsonl(
            fixtures_path,
            [{"fixture_id": report.fixture_id, "fixture_text": fixture_text}],
        )
    else:
        appended[_FIXTURES] = 0

    return appended


def ingest_aggregate(
    aggregate: dict[str, Any],
    lakehouse_dir: Path = DEFAULT_LAKEHOUSE_DIR,
    *,
    executed_at: str | None = None,
) -> int:
    """Append one capture aggregate (from ``olst_capture_aggregate``) keyed by
    aggregate_id. Returns rows appended (0 when already present). Every
    constituent run_id must already be in runs.jsonl; otherwise raise, because
    an aggregate without its attempts is not replayable."""
    agg_id = aggregate.get("aggregate_id")
    if not agg_id:
        raise ValueError("aggregate has no aggregate_id; refuse to ingest.")
    known_runs = _existing_keys(lakehouse_dir / _RUNS, lambda r: r["run_id"])
    missing = [rid for rid in aggregate.get("attempt_run_ids", {}).values() if rid not in known_runs]
    if missing:
        raise ValueError(f"aggregate {agg_id[:12]} references run_ids not in the store: {missing[:3]}")
    existing = _existing_keys(lakehouse_dir / _AGGREGATES, lambda r: r["aggregate_id"])
    if agg_id in existing:
        return 0
    row = dict(aggregate)
    row["executed_at"] = executed_at or _utc_now_iso()
    return _append_jsonl(lakehouse_dir / _AGGREGATES, [row])


def list_aggregates(lakehouse_dir: Path = DEFAULT_LAKEHOUSE_DIR) -> list[dict[str, Any]]:
    return _read_jsonl(lakehouse_dir / _AGGREGATES)


# -------- recall -----------------------------------------------------------

def list_runs(lakehouse_dir: Path = DEFAULT_LAKEHOUSE_DIR) -> list[dict[str, Any]]:
    return _read_jsonl(lakehouse_dir / _RUNS)


def _find_run(lakehouse_dir: Path, run_id: str) -> dict[str, Any]:
    for row in _read_jsonl(lakehouse_dir / _RUNS):
        if row["run_id"] == run_id:
            return row
    raise KeyError(f"run_id {run_id!r} not found in lakehouse at {lakehouse_dir}.")


def _find_fixture(lakehouse_dir: Path, fixture_id: str) -> str:
    for row in _read_jsonl(lakehouse_dir / _FIXTURES):
        if row["fixture_id"] == fixture_id:
            return row["fixture_text"]
    raise KeyError(f"fixture_id {fixture_id!r} not found in lakehouse at {lakehouse_dir}.")


def recall(run_id: str, lakehouse_dir: Path = DEFAULT_LAKEHOUSE_DIR) -> ReplayReport:
    """Rebuild a ReplayReport from the lakehouse streams.

    The returned object carries the same fields as the original ReplayReport,
    including traceability entries. Use `verify_replay` for the bit-for-bit
    re-execution check.
    """
    run_row = _find_run(lakehouse_dir, run_id)

    emus = [
        {k: v for k, v in row.items() if k != "run_id"}
        for row in _read_jsonl(lakehouse_dir / _EMUS)
        if row["run_id"] == run_id
    ]
    evaluations = []
    traceability: dict[str, list[TraceabilityEntry]] = {}
    for row in _read_jsonl(lakehouse_dir / _EVALUATIONS):
        if row["run_id"] != run_id:
            continue
        evidence = row.get("evidence", [])
        if evidence:
            traceability[row["criterion_id"]] = [
                TraceabilityEntry(**e) for e in evidence
            ]
        evaluations.append(
            {k: v for k, v in row.items() if k not in ("run_id", "evidence")}
        )
    non_evaluable = [
        {k: v for k, v in row.items() if k != "run_id"}
        for row in _read_jsonl(lakehouse_dir / _NON_EVALUABLE)
        if row["run_id"] == run_id
    ]

    return ReplayReport(
        fixture_id=run_row["fixture_id"],
        capture_id=run_row["capture_id"],
        participant_id=run_row["participant_id"],
        dataset_version=run_row["dataset_version"],
        mapping_spec_version=run_row["mapping_spec_version"],
        spec_id=run_row["spec_id"],
        criterion_map_id=run_row["criterion_map_id"],
        harness_version=run_row["harness_version"],
        run_id=run_row["run_id"],
        emu_outputs=emus,
        criterion_evaluations=evaluations,
        non_evaluable_criteria=non_evaluable,
        output_hash=run_row["output_hash"],
        traceability=traceability,
    )


def verify_replay(run_id: str, lakehouse_dir: Path = DEFAULT_LAKEHOUSE_DIR) -> bool:
    """Re-execute the stored fixture through the current harness and assert the
    new output_hash matches the stored one. Returns True on match; raises
    AssertionError on divergence.

    A divergence means **either** the fixture bytes drifted (impossible if
    fixture_id matches; the function checks first) **or** the harness /
    spec / criterion-map content changed since the run was ingested. Either
    way, the lakehouse trail makes the divergence explicit and inspectable.
    """
    run_row = _find_run(lakehouse_dir, run_id)
    stored_fixture_id = run_row["fixture_id"]
    stored_output_hash = run_row["output_hash"]

    fixture_text = _find_fixture(lakehouse_dir, stored_fixture_id)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", encoding="utf-8", delete=False
    ) as tmp:
        tmp.write(fixture_text)
        tmp_path = Path(tmp.name)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            replayed = _harness_run(tmp_path, mapping_spec_version=run_row["mapping_spec_version"])
    finally:
        tmp_path.unlink(missing_ok=True)

    if replayed.fixture_id != stored_fixture_id:
        raise AssertionError(
            f"replay fixture_id {replayed.fixture_id} does not match stored "
            f"{stored_fixture_id} — fixture bytes drifted between ingest and recall."
        )
    if replayed.output_hash != stored_output_hash:
        raise AssertionError(
            f"replay output_hash {replayed.output_hash} does not match stored "
            f"{stored_output_hash}. The harness, spec, or criterion map changed "
            f"since the run was ingested. Stored harness_version="
            f"{run_row['harness_version']}, current={replayed.harness_version}."
        )
    return True
