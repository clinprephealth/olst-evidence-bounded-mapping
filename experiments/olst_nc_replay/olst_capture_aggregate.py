"""Capture-level best-of-attempts aggregation for the OLST/NC replay benchmark.

Implements the D2 aggregation rule as *declared in a criterion map*, never as
a silent merge (spec §2 rule 2). The harness stays per-attempt; this module
consumes the per-attempt ``ReplayReport`` objects of one capture and emits one
content-addressed aggregate record.

Declared in the map (v2+) as::

    "aggregation": {
      "criterion_id": "gait_type",
      "rule": "best_of_attempts",
      "emu_type": "gait_temporal_control",
      "payload_field": "stance_duration_ms",
      "require_every_attempt": true,
      "require_non_overlapping_attempt_windows": true,
      "protocol_censoring": true
    }

Rules (protocol/AMENDMENT_2026-09-09_D1_RESOLUTION.md):
  D2   best_of = max(payload_field) over attempts; evaluable only if every
       attempt in the capture produced the EMU with that field.
  D2a  non-evaluable when any two attempt windows overlap (47_TRLGL_V4);
       per-attempt rows are ordered by foot-up time, not by attempt number.
  D4a  protocol censoring on the aggregate: duration thresholds are taken
       from the criterion's own rule block; sway is per-attempt and does not
       enter the aggregate label. The per-attempt evaluations are listed next
       to the aggregate.

This module is outside ``HARNESS_VERSION``; it records its own file digest as
``aggregator_version`` so an aggregate is identified by (constituent run_ids,
map bytes, aggregator bytes).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from experiments.olst_nc_replay.olst_replay_harness import (
    PROTOCOL_CENSORED,
    ReplayReport,
    _canonical_hash,
)

AGGREGATOR_VERSION: str = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

AGGREGATE_KIND = "capture_best_of_attempts"


def _attempt_number_from_report(report: ReplayReport) -> int | None:
    for emu in report.emu_outputs:
        emu_id = emu.get("emu_id", "")
        if ":attempt_" in emu_id:
            try:
                return int(emu_id.rsplit(":attempt_", 1)[1])
            except ValueError:
                return None
    return None


def _emu(report: ReplayReport, emu_type: str) -> dict[str, Any] | None:
    for emu in report.emu_outputs:
        if emu.get("emu_type") == emu_type:
            return emu
    return None


def _criterion_outcome(report: ReplayReport, criterion_id: str) -> tuple[str | None, str | None]:
    for ev in report.criterion_evaluations:
        if ev["criterion_id"] == criterion_id:
            return ev["evaluation"], None
    for ne in report.non_evaluable_criteria:
        if ne["criterion_id"] == criterion_id:
            return None, ne["non_evaluable_reason"]
    return None, "criterion absent from report"


def aggregate_capture(
    reports: list[ReplayReport],
    criterion_map: dict[str, Any],
) -> dict[str, Any]:
    """Aggregate the per-attempt reports of one capture per the map's declaration.

    Raises ValueError if the map declares no aggregation, if the reports do
    not share capture_id / mapping_spec_version / criterion_map_id /
    harness_version, or if the declared rule is unsupported. Data gaps never
    raise: they produce ``evaluable: false`` with a reason.
    """
    decl = criterion_map.get("aggregation")
    if not isinstance(decl, dict):
        raise ValueError("criterion map declares no 'aggregation' block; nothing to aggregate.")
    if decl.get("rule") != "best_of_attempts":
        raise ValueError(f"unsupported aggregation rule {decl.get('rule')!r}.")
    if not reports:
        raise ValueError("no reports to aggregate.")

    criterion_id: str = decl["criterion_id"]
    emu_type: str = decl["emu_type"]
    field: str = decl["payload_field"]
    require_every = bool(decl.get("require_every_attempt", True))
    require_non_overlap = bool(decl.get("require_non_overlapping_attempt_windows", True))
    censoring = bool(decl.get("protocol_censoring", False))

    for key in ("capture_id", "participant_id", "mapping_spec_version", "criterion_map_id", "harness_version"):
        values = {getattr(r, key) for r in reports}
        if len(values) != 1:
            raise ValueError(f"reports disagree on {key}: {sorted(values)}")
    head = reports[0]

    reasons: list[str] = []
    per_attempt: list[dict[str, Any]] = []
    expected_totals: set[int] = set()
    ceilings: set[Any] = set()
    protocol_codes: set[Any] = set()

    for r in reports:
        an = _attempt_number_from_report(r)
        emu = _emu(r, emu_type)
        evaluation, ne_reason = _criterion_outcome(r, criterion_id)
        row: dict[str, Any] = {
            "attempt_number": an,
            "run_id": r.run_id,
            "output_hash": r.output_hash,
            field: None,
            "foot_up_ms": None,
            "touchdown_ms": None,
            "evaluation": evaluation,
            "non_evaluable_reason": ne_reason,
        }
        if an is None:
            reasons.append(f"run {r.run_id[:12]} emitted no EMUs; attempt number unknown")
        if emu is None:
            reasons.append(f"attempt {an}: no {emu_type} EMU")
        else:
            payload = emu.get("payload", {})
            prov = emu.get("provenance", {})
            value = payload.get(field)
            if isinstance(value, int):
                row[field] = value
            else:
                reasons.append(f"attempt {an}: {emu_type} lacks {field!r}")
            row["foot_up_ms"] = prov.get("stance_phase_foot_up_ms")
            row["touchdown_ms"] = prov.get("stance_phase_touchdown_ms")
            if isinstance(prov.get("total_attempts_in_session"), int):
                expected_totals.add(prov["total_attempts_in_session"])
            if "observation_ceiling_ms" in payload:
                ceilings.add(payload["observation_ceiling_ms"])
            protocol_codes.add(payload.get("protocol_code"))
        per_attempt.append(row)

    # A4.2: order by event time, not by attempt number.
    per_attempt.sort(key=lambda x: (x["foot_up_ms"] is None, x["foot_up_ms"] or 0, x["attempt_number"] or 0))

    seen = {x["attempt_number"] for x in per_attempt if x["attempt_number"] is not None}
    if len(expected_totals) > 1:
        reasons.append(f"attempts disagree on total_attempts_in_session: {sorted(expected_totals)}")
    expected = next(iter(expected_totals)) if len(expected_totals) == 1 else None
    if require_every and expected is not None:
        missing = sorted(set(range(1, expected + 1)) - seen)
        if missing:
            reasons.append(f"attempt(s) {missing} absent from the aggregate input (expected {expected})")
    if len(seen) != len(per_attempt):
        reasons.append("duplicate attempt numbers among reports")

    # A4.1: overlapping windows are not separate attempts.
    overlaps: list[str] = []
    if require_non_overlap:
        windows = [
            (x["foot_up_ms"], x["touchdown_ms"], x["attempt_number"])
            for x in per_attempt
            if isinstance(x["foot_up_ms"], int) and isinstance(x["touchdown_ms"], int)
        ]
        for i in range(len(windows)):
            for j in range(i + 1, len(windows)):
                a0, a1, an_a = windows[i]
                b0, b1, an_b = windows[j]
                if a0 < b1 and b0 < a1:
                    overlaps.append(f"an{an_a}[{a0}-{a1}] overlaps an{an_b}[{b0}-{b1}]")
        if overlaps:
            reasons.append("attempt windows overlap: " + "; ".join(overlaps))

    values = [(x[field], x["attempt_number"]) for x in per_attempt if isinstance(x[field], int)]
    evaluable = not reasons and bool(values)
    if not values and not reasons:
        reasons.append(f"no attempt carries {field!r}")
        evaluable = False

    best_of: dict[str, Any] | None = None
    aggregate_evaluation: str | None = None
    detail: dict[str, Any] = {}
    if evaluable:
        best_value, best_an = max(values, key=lambda v: (v[0], -(v[1] or 0)))
        best_of = {field: best_value, "attempt_number": best_an}

        rule = (criterion_map.get("criteria", {}).get(criterion_id) or {}).get("rule") or {}
        thresholds = rule.get("thresholds") or {}
        normal_min = thresholds.get("duration_normal_min_ms")
        weak_min = thresholds.get("duration_weak_min_ms")
        if not isinstance(normal_min, int) or not isinstance(weak_min, int):
            raise ValueError(
                f"criterion {criterion_id!r} has no duration thresholds in its rule block; "
                f"the aggregate cannot label without them."
            )
        detail = {
            "duration_field": field,
            "duration_ms": best_value,
            "thresholds_ms": {"normal_min": normal_min, "weak_min": weak_min},
            "sway_considered": False,
        }
        if censoring:
            if len(ceilings) != 1:
                reasons.append(f"attempts disagree on observation_ceiling_ms: {sorted(map(str, ceilings))}")
                evaluable = False
            else:
                ceiling = next(iter(ceilings))
                unobservable = [th for th in (normal_min, weak_min) if ceiling is None or th > ceiling]
                detail["observation_ceiling_ms"] = ceiling
                detail["protocol_code"] = next(iter(protocol_codes)) if len(protocol_codes) == 1 else sorted(map(str, protocol_codes))
                detail["unobservable_thresholds_ms"] = unobservable
                if not unobservable:
                    aggregate_evaluation = "normal" if best_value >= normal_min else ("weak" if best_value >= weak_min else "impaired")
                elif weak_min not in unobservable and best_value < weak_min:
                    aggregate_evaluation = "impaired"
                else:
                    aggregate_evaluation = PROTOCOL_CENSORED
        else:
            aggregate_evaluation = "normal" if best_value >= normal_min else ("weak" if best_value >= weak_min else "impaired")
        if not evaluable:
            best_of = None
            aggregate_evaluation = None
            detail = {}

    record: dict[str, Any] = {
        "aggregate_kind": AGGREGATE_KIND,
        "capture_id": head.capture_id,
        "participant_id": head.participant_id,
        "mapping_spec_version": head.mapping_spec_version,
        "criterion_map_id": head.criterion_map_id,
        "harness_version": head.harness_version,
        "aggregator_version": AGGREGATOR_VERSION,
        "criterion_id": criterion_id,
        "emu_type": emu_type,
        "payload_field": field,
        "attempt_run_ids": {str(x["attempt_number"]): x["run_id"] for x in sorted(per_attempt, key=lambda x: x["attempt_number"] or 0)},
        "attempts_expected": expected,
        "attempts_present": len(per_attempt),
        "per_attempt": per_attempt,
        "evaluable": evaluable,
        "non_evaluable_reason": "; ".join(reasons) if reasons else None,
        "best_of": best_of,
        "aggregate_evaluation": aggregate_evaluation,
        "detail": detail,
    }
    record["aggregate_id"] = _canonical_hash(record)
    return record
