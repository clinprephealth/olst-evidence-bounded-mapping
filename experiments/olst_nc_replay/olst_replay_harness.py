"""
Replay harness for OLST fixtures → canonical bytes → EMUs → NC criterion mapping.

See docs/OLST_NC_REPLAY_BENCHMARK_EXECUTION.md (Tasks 2–5).
Exclusions: specs/OLST_CANONICALIZATION_SPEC_v1.md §3.
"""

from __future__ import annotations

import hashlib
import json
import math
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

DATASET_VERSION: str = "1.0"

# Capture-level exclusions — keys are capture ids of the form
# "{participant_id}_{movement_code}_V{version}". Per PhysioNet usage notes:
# "one capture (12_MNTRL_V2) is missing due to a data collection error and
# should be excluded from analysis."
KNOWN_CAPTURE_EXCLUSIONS: dict[str, str] = {
    "12_MNTRL_V2": "Data collection error — capture missing per PhysioNet usage notes.",
}

# Participant-level exclusions — empty in v1; slot kept so a future row addition is one line.
KNOWN_PARTICIPANT_EXCLUSIONS: dict[str, str] = {}

_CRITERION_MAP_PATH = Path(__file__).parent / "specs" / "NC_CRITERION_EMU_MAP_v1.json"
_CANONICALIZATION_SPEC_PATH = Path(__file__).parent / "specs" / "OLST_CANONICALIZATION_SPEC_v1.md"


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Content-addressed identity for the running harness source. Computed once at
# import — this correctly captures the bytes of the *running code*, not the
# bytes-on-disk (which can be edited mid-process without affecting what's
# actually executing). A harness source change requires re-import to take
# effect, and HARNESS_VERSION reflects that.
HARNESS_VERSION: str = _file_sha256(Path(__file__))


def spec_id() -> str:
    """SHA-256 of the OLST canonicalization spec file as it currently exists on disk.

    Recomputed on every call. A spec edit between runs surfaces immediately as
    a different ``run_id``, even if the harness was not re-imported. This is
    the spec-drift detection guarantee referenced in the methods section: the
    pair (HARNESS_VERSION, spec_id) being mismatched between two runs means
    the spec file changed without the harness implementation tracking it.
    """
    return _file_sha256(_CANONICALIZATION_SPEC_PATH)


class UnknownMappingSpecVersionError(ValueError):
    """Raised when no criterion map file exists for the requested mapping_spec_version.

    There is deliberately no fallback to v1: an unknown version is an error,
    never a silent default (same discipline as unknown domain policies).
    """


def _criterion_map_path(mapping_spec_version: str) -> Path:
    """Resolve the criterion map file for a mapping_spec_version.

    "v1" resolves to the module-level ``_CRITERION_MAP_PATH`` (kept as a
    module attribute so tests can redirect it); any other version resolves to
    ``specs/NC_CRITERION_EMU_MAP_<version>.json`` and must exist.
    """
    if mapping_spec_version == "v1":
        return _CRITERION_MAP_PATH
    candidate = Path(__file__).parent / "specs" / f"NC_CRITERION_EMU_MAP_{mapping_spec_version}.json"
    if not candidate.exists():
        raise UnknownMappingSpecVersionError(
            f"No criterion map for mapping_spec_version {mapping_spec_version!r} "
            f"(expected {candidate.name} in specs/). Unknown versions never fall back to v1."
        )
    return candidate


def criterion_map_id(mapping_spec_version: str = "v1") -> str:
    """SHA-256 of the NC criterion map JSON file as it currently exists on disk.

    Recomputed on every call. The criterion map is reloaded inside ``run()``
    on every invocation, so this correctly tracks the bytes that produced the
    current evaluation.
    """
    return _file_sha256(_criterion_map_path(mapping_spec_version))

# Concrete numeric thresholds for the gait_type criterion (rule v1). The spec
# documents the threshold structure; the numeric pinning lives here so that
# rule_version "v1" deterministically resolves to these values.
_GAIT_TYPE_RULE_V1_THRESHOLDS: dict[str, float] = {
    "stability_duration_normal_min_ms": 10000.0,
    "stability_duration_weak_min_ms": 5000.0,
    "sway_area_normal_max_mm2": 250.0,
    "sway_area_impaired_min_mm2": 600.0,
}


class FixtureSchemaError(ValueError):
    """Raised when a fixture is missing a required top-level provenance field."""


class ExcludedCaptureError(ValueError):
    """Raised when a fixture's capture_id is listed in KNOWN_CAPTURE_EXCLUSIONS."""


class ExcludedParticipantError(ValueError):
    """Raised when a fixture's participant_id is listed in KNOWN_PARTICIPANT_EXCLUSIONS."""


def assert_capture_not_excluded(capture_id: str) -> None:
    if capture_id in KNOWN_CAPTURE_EXCLUSIONS:
        reason = KNOWN_CAPTURE_EXCLUSIONS[capture_id]
        raise ExcludedCaptureError(
            f"Capture {capture_id!r} is excluded from canonical processing: {reason}"
        )


def assert_participant_not_excluded(participant_id: str) -> None:
    if participant_id in KNOWN_PARTICIPANT_EXCLUSIONS:
        reason = KNOWN_PARTICIPANT_EXCLUSIONS[participant_id]
        raise ExcludedParticipantError(
            f"Participant {participant_id!r} is excluded from canonical processing: {reason}"
        )


def participant_id_from_fixture(data: dict[str, Any]) -> str:
    raw = data.get("participant_id")
    if not isinstance(raw, str) or not raw.strip():
        raise FixtureSchemaError(
            "Fixture missing required top-level 'participant_id' string field."
        )
    return raw.strip()


def capture_id_from_fixture(data: dict[str, Any]) -> str:
    raw = data.get("capture_id")
    if not isinstance(raw, str) or not raw.strip():
        raise FixtureSchemaError(
            "Fixture missing required top-level 'capture_id' string field."
        )
    return raw.strip()


@dataclass(frozen=True)
class TraceabilityEntry:
    """One provenance link from a criterion line to an EMU."""

    emu_id: str
    payload_hash: str
    rule_version: str


@dataclass
class ReplayReport:
    """Structured output of one replay run (same fixture + spec → same output_hash).

    Identifier discipline:
      run_id         SHA-256 over the canonical input bundle (fixture_id +
                     spec_id + criterion_map_id + harness_version +
                     dataset_version + mapping_spec_version). Same inputs →
                     same run_id regardless of who ran it or when. A spec
                     amendment is a different run_id for the same fixture.
      fixture_id     SHA-256 hex digest of UTF-8 fixture bytes as read from disk.
                     Identifies what specific JSON we ran; computed by the harness.
      capture_id     Dataset provenance — which real-world PhysioNet capture
                     this fixture represents. Read directly from fixture.
      participant_id Dataset provenance — which real-world PhysioNet participant.
                     Read directly from fixture.
      output_hash    SHA-256 over the canonical OUTPUT bundle. Distinct from
                     run_id (input identity); see spec §7.
    """

    fixture_id: str
    capture_id: str
    participant_id: str
    dataset_version: str
    mapping_spec_version: str
    spec_id: str = ""
    criterion_map_id: str = ""
    harness_version: str = ""
    run_id: str = ""
    emu_outputs: list[dict[str, Any]] = field(default_factory=list)
    criterion_evaluations: list[dict[str, Any]] = field(default_factory=list)
    non_evaluable_criteria: list[dict[str, Any]] = field(default_factory=list)
    output_hash: str = ""
    traceability: dict[str, list[TraceabilityEntry]] = field(default_factory=dict)


# -------- canonicalization (O-CI-0) ----------------------------------------

def _canonicalize_value(value: Any) -> Any:
    """Recursively rewrite a JSON-shaped value into canonical form.

    Rules from spec §6:
      • dict keys are emitted in lex order (handled by json.dumps sort_keys)
      • floats are rounded to 6 decimal places
      • NaN / Inf are not allowed — caller must use null + missing_reason
      • integers, strings, bools, None pass through
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError(
                "Canonicalization refuses NaN/Inf floats — use explicit null + missing_reason."
            )
        return round(value, 6)
    if isinstance(value, str):
        return value
    if value is None:
        return None
    if isinstance(value, list):
        return [_canonicalize_value(v) for v in value]
    if isinstance(value, tuple):
        return [_canonicalize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _canonicalize_value(v) for k, v in value.items()}
    raise TypeError(f"Canonicalization does not support type {type(value).__name__!r}")


def _canonical_dumps(value: Any) -> str:
    """Serialize a JSON-shaped value to canonical JSON string (UTF-8, no whitespace, lex keys)."""
    canonical = _canonicalize_value(value)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_hash(value: Any) -> str:
    return _sha256_hex(_canonical_dumps(value).encode("utf-8"))


def _fixture_content_sha256(raw_bytes: bytes) -> str:
    return _sha256_hex(raw_bytes)


# -------- EMU derivation ---------------------------------------------------

def _emu_id(emu_type: str, capture_id: str, attempt_number: int) -> str:
    return f"{emu_type}:{capture_id}:attempt_{attempt_number}"


def _build_emu(
    emu_type: str,
    capture_id: str,
    attempt_number: int,
    provenance: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    canonical_payload = _canonicalize_value(payload)
    payload_hash = _canonical_hash(canonical_payload)
    return {
        "emu_type": emu_type,
        "emu_id": _emu_id(emu_type, capture_id, attempt_number),
        "non_authoritative": True,
        "requires_human_ack": True,
        "provenance": provenance,
        "payload": canonical_payload,
        "payload_hash": payload_hash,
    }


def _derive_emus(canonical: dict[str, Any]) -> list[dict[str, Any]]:
    """Emit the four EMU types (or skip with structured null when source data is missing).

    The fixture is the post-canonicalization JSON; this function only routes its
    fields into EMU shapes per olst_emu_schema_v1.yaml. No imputation, no defaults
    — if a required source field is absent, the EMU is omitted and downstream
    criterion evaluation will mark dependent criteria non-evaluable.
    """
    capture_id: str = canonical["capture_id"]
    attempt_number: int = int(canonical["attempt_number"])
    total_attempts: int = int(canonical["total_attempts_in_session"])
    norm_rule = canonical.get("normalization_rule_version", "v1")
    deriv_rule = canonical.get("derivation_rule_version", "v1")

    stability = canonical.get("stability_phase") or {}
    fp = canonical.get("force_plate") or {}
    stance_phase = canonical.get("stance_phase") or {}
    acquisition = canonical.get("acquisition_protocol") or {}

    emus: list[dict[str, Any]] = []

    # gait_temporal_control — needs trial_leg plus at least one event window:
    #   stable phase  (t_stable → t_break)   → stability_duration_ms   (v1 construct)
    #   stance phase  (t_foot_up → t_end)    → stance_duration_ms      (spec §6.6, v1.3)
    # Optional fields are added only when the fixture carries the source window,
    # so fixtures without them (all synthetic v1 fixtures) produce payloads and
    # provenance byte-identical to pre-v1.3 — the golden hashes assert this.
    start_ms = stability.get("start_ms")
    end_ms = stability.get("end_ms")
    have_stability = isinstance(start_ms, int) and isinstance(end_ms, int)
    foot_up_ms = stance_phase.get("foot_up_ms")
    touchdown_ms = stance_phase.get("touchdown_ms")
    have_stance = isinstance(foot_up_ms, int) and isinstance(touchdown_ms, int)
    trial_leg = canonical.get("trial_leg")
    event_source = stability.get("event_label_source") if have_stability else stance_phase.get("event_label_source")
    if (have_stability or have_stance) and isinstance(trial_leg, str) and isinstance(event_source, str):
        provenance: dict[str, Any] = {"source_trial_id": capture_id}
        payload: dict[str, Any] = {}
        if have_stability:
            provenance["stability_phase_start_ms"] = start_ms
            provenance["stability_phase_end_ms"] = end_ms
            payload["stability_duration_ms"] = end_ms - start_ms
        if have_stance:
            provenance["stance_phase_foot_up_ms"] = foot_up_ms
            provenance["stance_phase_touchdown_ms"] = touchdown_ms
            payload["stance_duration_ms"] = touchdown_ms - foot_up_ms
        if "observation_ceiling_ms" in acquisition:
            ceiling = acquisition.get("observation_ceiling_ms")
            if ceiling is not None and not isinstance(ceiling, int):
                raise FixtureSchemaError(
                    "acquisition_protocol.observation_ceiling_ms must be an integer or null."
                )
            payload["observation_ceiling_ms"] = ceiling
            if isinstance(acquisition.get("protocol_code"), str):
                payload["protocol_code"] = acquisition["protocol_code"]
            if isinstance(acquisition.get("observation_ceiling_source"), str):
                provenance["observation_ceiling_source"] = acquisition["observation_ceiling_source"]
        provenance.update(
            {
                "event_label_source": event_source,
                "normalization_rule_version": norm_rule,
                "attempt_number": attempt_number,
                "total_attempts_in_session": total_attempts,
            }
        )
        payload["trial_leg"] = trial_leg
        emus.append(
            _build_emu("gait_temporal_control", capture_id, attempt_number, provenance, payload)
        )

    # postural_stability_index — needs CoP fields
    mean_cop = fp.get("mean_cop_displacement_mm")
    sway = fp.get("sway_area_mm2")
    stance = fp.get("stance_duration_ms")
    if (
        isinstance(mean_cop, (int, float))
        and isinstance(sway, (int, float))
        and isinstance(stance, int)
        and isinstance(start_ms, int)
        and isinstance(end_ms, int)
    ):
        provenance = {
            "source_trial_id": capture_id,
            "stability_phase_start_ms": start_ms,
            "stability_phase_end_ms": end_ms,
            "normalization_rule_version": norm_rule,
            "attempt_number": attempt_number,
            "total_attempts_in_session": total_attempts,
        }
        payload = {
            "mean_cop_displacement_mm": float(mean_cop),
            "sway_area_mm2": float(sway),
            "stance_duration_ms": stance,
        }
        emus.append(
            _build_emu("postural_stability_index", capture_id, attempt_number, provenance, payload)
        )

    # weight_distribution_asymmetry — needs left/right
    left = fp.get("left_pct")
    right = fp.get("right_pct")
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        left_f = float(left)
        right_f = float(right)
        asymmetry = abs(left_f - right_f)
        provenance = {
            "source_trial_id": capture_id,
            "normalization_rule_version": norm_rule,
            "attempt_number": attempt_number,
            "total_attempts_in_session": total_attempts,
        }
        payload = {
            "left_pct": left_f,
            "right_pct": right_f,
            "asymmetry_index": asymmetry,
        }
        emus.append(
            _build_emu(
                "weight_distribution_asymmetry", capture_id, attempt_number, provenance, payload
            )
        )

    # balance_control_quality — derived composite, requires both gait_temporal_control
    # and postural_stability_index to have been emittable above.
    have_gait = any(
        e["emu_type"] == "gait_temporal_control" and "stability_duration_ms" in e["payload"]
        for e in emus
    )
    have_psi = any(e["emu_type"] == "postural_stability_index" for e in emus)
    if have_gait and have_psi:
        gtc_payload = next(e["payload"] for e in emus if e["emu_type"] == "gait_temporal_control")
        psi_payload = next(e["payload"] for e in emus if e["emu_type"] == "postural_stability_index")
        # Composite: stability seconds normalized to [0,1] with 10s ceiling, minus
        # sway penalty (sway / 1000). Bounded to [0, 1.5] so adversarial sway can't
        # produce nonsense negatives. Rule v1 — pinned so traceability is meaningful.
        stability_seconds = gtc_payload["stability_duration_ms"] / 1000.0
        sway_penalty = psi_payload["sway_area_mm2"] / 1000.0
        composite = max(0.0, min(stability_seconds, 10.0) / 10.0 - sway_penalty)
        provenance = {
            "source_trial_id": capture_id,
            "derivation_rule_version": deriv_rule,
            "attempt_number": attempt_number,
            "total_attempts_in_session": total_attempts,
        }
        payload = {"composite_score": composite}
        emus.append(
            _build_emu("balance_control_quality", capture_id, attempt_number, provenance, payload)
        )

    return emus


# -------- NC criterion mapping ---------------------------------------------

def _load_criterion_map(mapping_spec_version: str = "v1") -> dict[str, Any]:
    return json.loads(_criterion_map_path(mapping_spec_version).read_text(encoding="utf-8"))


def _evaluate_gait_type(
    gtc_payload: dict[str, Any],
    psi_payload: dict[str, Any],
) -> str:
    """Apply rule v1 thresholds → "normal" | "weak" | "impaired"."""
    duration = gtc_payload["stability_duration_ms"]
    sway = psi_payload["sway_area_mm2"]
    t = _GAIT_TYPE_RULE_V1_THRESHOLDS
    if duration >= t["stability_duration_normal_min_ms"] and sway < t["sway_area_normal_max_mm2"]:
        return "normal"
    if duration < t["stability_duration_weak_min_ms"] or sway >= t["sway_area_impaired_min_mm2"]:
        return "impaired"
    return "weak"


# Evaluation label emitted when the acquisition protocol did not permit the
# relevant duration threshold to be observed (amendment 2026-09-09, D4a).
PROTOCOL_CENSORED = "protocol_censored"


def _evaluate_duration_sway_rule(
    rule: dict[str, Any],
    gtc_payload: dict[str, Any],
    psi_payload: dict[str, Any],
) -> tuple[str | None, dict[str, Any], str | None]:
    """Map-declared duration + sway threshold rule with optional protocol censoring.

    Returns (evaluation, detail, non_evaluable_reason). Exactly one of
    evaluation / non_evaluable_reason is non-None.

    Semantics (spec §6.6, amendment A3):
      • sway_area_mm2 >= sway_area_impaired_min_mm2 → "impaired" regardless of
        the duration ceiling (sway is measured inside the stable window and is
        not bounded by the stance ceiling).
      • protocol_censoring on:
          ceiling null            → every duration threshold unobservable → PROTOCOL_CENSORED
          ceiling >= normal_min   → all categories observable → full rule
          weak_min <= ceiling < normal_min
                                  → "impaired" if duration < weak_min, else PROTOCOL_CENSORED
          ceiling < weak_min      → PROTOCOL_CENSORED
      • The measured duration is always reported in `detail`; censoring
        withholds the label, never the number.
      • rule["sway_gating"] (amendment 2026-09-09 A12, map v2.1): when
        false, sway_area_mm2 is reported in `detail` but takes no part in
        label determination; the label depends on the (censored) duration
        construct only. Absent or true → v1/v2 behaviour, byte-identical.
    """
    duration_field = rule["duration_field"]
    t = rule["thresholds"]
    normal_min = t["duration_normal_min_ms"]
    weak_min = t["duration_weak_min_ms"]
    sway_gating = bool(rule.get("sway_gating", True))
    sway_normal_max = t["sway_area_normal_max_mm2"] if sway_gating else None
    sway_impaired_min = t["sway_area_impaired_min_mm2"] if sway_gating else None

    duration = gtc_payload.get(duration_field)
    if not isinstance(duration, int):
        return None, {}, (
            f"gait_temporal_control lacks {duration_field!r}; the rule's duration "
            f"construct is not present for this attempt."
        )
    sway = psi_payload["sway_area_mm2"]

    detail: dict[str, Any] = {
        "duration_field": duration_field,
        "duration_ms": duration,
        "sway_area_mm2": sway,
    }
    if "sway_gating" in rule:
        detail["sway_gating"] = sway_gating

    def _full_rule() -> str:
        if not sway_gating:
            if duration >= normal_min:
                return "normal"
            return "weak" if duration >= weak_min else "impaired"
        if duration >= normal_min and sway < sway_normal_max:
            return "normal"
        if duration < weak_min or sway >= sway_impaired_min:
            return "impaired"
        return "weak"

    if not rule.get("protocol_censoring", False):
        return _full_rule(), detail, None

    if "observation_ceiling_ms" not in gtc_payload:
        return None, {}, (
            "Rule requires protocol censoring but gait_temporal_control carries no "
            "observation_ceiling_ms (fixture lacks acquisition_protocol)."
        )
    ceiling = gtc_payload["observation_ceiling_ms"]
    unobservable = [th for th in (normal_min, weak_min) if ceiling is None or th > ceiling]
    detail["observation_ceiling_ms"] = ceiling
    detail["protocol_code"] = gtc_payload.get("protocol_code")
    detail["unobservable_thresholds_ms"] = unobservable

    if sway_gating and sway >= sway_impaired_min:
        return "impaired", detail, None
    if not unobservable:
        return _full_rule(), detail, None
    if weak_min not in unobservable and duration < weak_min:
        return "impaired", detail, None
    return PROTOCOL_CENSORED, detail, None


def _evaluate_ordinal_duration_rule(
    rule: dict[str, Any],
    gtc_payload: dict[str, Any],
) -> tuple[str | None, dict[str, Any], str | None]:
    """Map-declared ordinal duration rubric with optional protocol censoring.

    Added 2026-09-10 for the Berg item 14 rubric (amendment A15). The
    v1/v2/v2.1 rule type could express only three fixed labels at two
    boundaries; this type takes the labels and boundaries from the map::

        "rule": {
          "type": "ordinal_duration_thresholds",
          "duration_field": "stance_duration_ms",
          "levels": [                       # descending; min_ms is the lower bound
            {"label": "score_4", "min_ms": 10001},   # > 10 s
            {"label": "score_3", "min_ms": 5000},
            {"label": "score_2", "min_ms": 3000}
          ],
          "floor_label": "score_1_or_0_unresolved",  # below the lowest min_ms
          "protocol_censoring": true
        }

    Censoring semantics (same principle as A3, kept consistent with the
    duration_sway rule): a level is labelled only if every boundary needed to
    place the duration in that level was observable under the protocol
    ceiling — its own lower boundary (for a non-floor level) and the next
    boundary above it (for a non-top level). Otherwise PROTOCOL_CENSORED. A
    null ceiling makes no boundary observable, so every attempt is censored.
    """
    duration_field = rule["duration_field"]
    levels = sorted(rule["levels"], key=lambda lv: -int(lv["min_ms"]))
    floor_label = rule["floor_label"]
    duration = gtc_payload.get(duration_field)
    if not isinstance(duration, int):
        return None, {}, (
            f"gait_temporal_control lacks {duration_field!r}; the rule's duration "
            f"construct is not present for this attempt."
        )
    detail: dict[str, Any] = {"duration_field": duration_field, "duration_ms": duration}

    attained = floor_label
    own_boundary: int | None = None
    next_boundary: int | None = None
    for i, lv in enumerate(levels):
        if duration >= int(lv["min_ms"]):
            attained = lv["label"]
            own_boundary = int(lv["min_ms"])
            next_boundary = int(levels[i - 1]["min_ms"]) if i > 0 else None
            break
    else:
        next_boundary = int(levels[-1]["min_ms"])
    detail["attained_level"] = attained
    detail["next_boundary_ms"] = next_boundary

    if not rule.get("protocol_censoring", False):
        return attained, detail, None
    if "observation_ceiling_ms" not in gtc_payload:
        return None, {}, (
            "Rule requires protocol censoring but gait_temporal_control carries no "
            "observation_ceiling_ms (fixture lacks acquisition_protocol)."
        )
    ceiling = gtc_payload["observation_ceiling_ms"]
    boundaries = [int(lv["min_ms"]) for lv in levels]
    unobservable = [b for b in boundaries if ceiling is None or b > ceiling]
    detail["observation_ceiling_ms"] = ceiling
    detail["protocol_code"] = gtc_payload.get("protocol_code")
    detail["unobservable_thresholds_ms"] = unobservable
    needed = [b for b in (own_boundary, next_boundary) if b is not None]
    if all(b not in unobservable for b in needed):
        return attained, detail, None
    return PROTOCOL_CENSORED, detail, None


def _apply_nc_map(
    emus: list[dict[str, Any]],
    criterion_map: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, list[TraceabilityEntry]],
]:
    """Walk the criterion map; emit evaluations + non-evaluables + traceability.

    No imputation: a criterion is non-evaluable when (a) its `derivability` is
    "non_evaluable" by spec, or (b) any of its required EMUs is absent from the
    derived set.
    """
    by_type: dict[str, dict[str, Any]] = {e["emu_type"]: e for e in emus}
    evaluations: list[dict[str, Any]] = []
    non_evaluable: list[dict[str, Any]] = []
    traceability: dict[str, list[TraceabilityEntry]] = {}

    for criterion_id, spec in criterion_map["criteria"].items():
        rule_version = spec.get("mapping_rule_version", "v1")
        derivability = spec["derivability"]
        if derivability == "non_evaluable":
            non_evaluable.append(
                {
                    "criterion_id": criterion_id,
                    "label": spec["label"],
                    "non_evaluable_reason": spec["non_evaluable_reason"],
                    "rule_version": rule_version,
                }
            )
            continue

        required = list(spec.get("required_emus", []))
        missing = [t for t in required if t not in by_type]
        if missing:
            non_evaluable.append(
                {
                    "criterion_id": criterion_id,
                    "label": spec["label"],
                    "non_evaluable_reason": (
                        f"Required EMU(s) absent from derived set: {sorted(missing)}."
                    ),
                    "rule_version": rule_version,
                }
            )
            continue

        evidence_entries = [
            TraceabilityEntry(
                emu_id=by_type[t]["emu_id"],
                payload_hash=by_type[t]["payload_hash"],
                rule_version=rule_version,
            )
            for t in required
        ]
        traceability[criterion_id] = evidence_entries

        detail: dict[str, Any] | None = None
        rule = spec.get("rule")
        if isinstance(rule, dict):
            # Map-declared rule (v2+). The map bytes define the rule; the
            # harness only interprets the declared type.
            rule_type = rule.get("type")
            if rule_type == "duration_sway_thresholds":
                evaluation, detail, reason = _evaluate_duration_sway_rule(
                    rule,
                    by_type["gait_temporal_control"]["payload"],
                    by_type["postural_stability_index"]["payload"],
                )
            elif rule_type == "ordinal_duration_thresholds":
                evaluation, detail, reason = _evaluate_ordinal_duration_rule(
                    rule, by_type["gait_temporal_control"]["payload"]
                )
            else:
                raise ValueError(
                    f"Criterion {criterion_id!r}: unsupported rule type {rule_type!r}."
                )
            if reason is not None:
                del traceability[criterion_id]
                non_evaluable.append(
                    {
                        "criterion_id": criterion_id,
                        "label": spec["label"],
                        "non_evaluable_reason": reason,
                        "rule_version": rule_version,
                    }
                )
                continue
        elif criterion_id == "gait_type":
            # v1 hard-pinned rule. Requires the stable-phase duration; a
            # gait_temporal_control EMU carrying only the stance window (an
            # attempt with no t_stable) cannot feed it.
            gtc_payload = by_type["gait_temporal_control"]["payload"]
            if "stability_duration_ms" not in gtc_payload:
                del traceability[criterion_id]
                non_evaluable.append(
                    {
                        "criterion_id": criterion_id,
                        "label": spec["label"],
                        "non_evaluable_reason": (
                            "gait_temporal_control lacks 'stability_duration_ms' (no stable "
                            "phase in this attempt); the v1 gait rule requires the "
                            "stable-phase duration."
                        ),
                        "rule_version": rule_version,
                    }
                )
                continue
            evaluation = _evaluate_gait_type(
                gtc_payload,
                by_type["postural_stability_index"]["payload"],
            )
        elif derivability == "partial":
            evaluation = "partial_evidence_only"
        else:
            evaluation = "derivable_no_rule_implemented"

        record: dict[str, Any] = {
            "criterion_id": criterion_id,
            "label": spec["label"],
            "derivability": derivability,
            "evaluation": evaluation,
            "rule_version": rule_version,
        }
        if detail:
            record["detail"] = detail
        evaluations.append(record)

    return evaluations, non_evaluable, traceability


# -------- output hashing ---------------------------------------------------

def _traceability_to_canonical(
    traceability: dict[str, list[TraceabilityEntry]],
) -> dict[str, list[dict[str, str]]]:
    """Lex-sorted keys; entries within each list sorted by (emu_id, payload_hash, rule_version)."""
    out: dict[str, list[dict[str, str]]] = {}
    for criterion_id in sorted(traceability):
        entries = sorted(
            traceability[criterion_id],
            key=lambda e: (e.emu_id, e.payload_hash, e.rule_version),
        )
        out[criterion_id] = [asdict(e) for e in entries]
    return out


def _compute_run_id(
    *,
    fixture_id: str,
    dataset_version: str,
    mapping_spec_version: str,
    spec_id: str,
    criterion_map_id: str,
    harness_version: str,
) -> str:
    """Composite content-addressed identity for one execution.

    run_id = sha256(canonical({fixture_id, dataset_version, mapping_spec_version,
    spec_id, criterion_map_id, harness_version})).
    Same inputs → same run_id, deterministically. Distinct from output_hash
    (which addresses the result, not the inputs).

    All identity arguments are required (no defaults from module constants) so
    callers must explicitly choose between captured-at-import and
    re-read-at-call values. ``run()`` always re-reads spec_id and
    criterion_map_id at call time so spec drift surfaces immediately.
    """
    bundle = {
        "fixture_id": fixture_id,
        "dataset_version": dataset_version,
        "mapping_spec_version": mapping_spec_version,
        "spec_id": spec_id,
        "criterion_map_id": criterion_map_id,
        "harness_version": harness_version,
    }
    return _canonical_hash(bundle)


def _output_hash(report: ReplayReport) -> str:
    """Hash scope: emu_outputs, criterion_evaluations, non_evaluable_criteria,
    traceability, mapping_spec_version, dataset_version. See spec §7.
    """
    scope = {
        "dataset_version": report.dataset_version,
        "mapping_spec_version": report.mapping_spec_version,
        "emu_outputs": sorted(
            (_canonicalize_value(e) for e in report.emu_outputs),
            key=lambda e: e["emu_id"],
        ),
        "criterion_evaluations": sorted(
            (_canonicalize_value(c) for c in report.criterion_evaluations),
            key=lambda c: c["criterion_id"],
        ),
        "non_evaluable_criteria": sorted(
            (_canonicalize_value(c) for c in report.non_evaluable_criteria),
            key=lambda c: c["criterion_id"],
        ),
        "traceability": _traceability_to_canonical(report.traceability),
    }
    return _canonical_hash(scope)


# -------- top-level entry --------------------------------------------------

def run(fixture_path: str | Path, mapping_spec_version: str) -> ReplayReport:
    """Load fixture JSON → canonicalize (O-CI-0) → derive EMUs → apply NC mapping → hash outputs.

    Same fixture path content + same mapping_spec_version yields identical
    `output_hash`. Excluded captures or participants raise without producing
    a partial result (gap visibility at ingest, not after).
    """
    path = Path(fixture_path)
    raw_bytes = path.read_bytes()
    fixture_id = _fixture_content_sha256(raw_bytes)

    text = raw_bytes.decode("utf-8")
    data: dict[str, Any] = json.loads(text)

    capture_id = capture_id_from_fixture(data)
    assert_capture_not_excluded(capture_id)

    participant_id = participant_id_from_fixture(data)
    assert_participant_not_excluded(participant_id)

    fixture_dataset_version = data.get("dataset_version")
    if not isinstance(fixture_dataset_version, str) or not fixture_dataset_version.strip():
        raise FixtureSchemaError(
            "Fixture missing required top-level 'dataset_version' string field."
        )
    if fixture_dataset_version != DATASET_VERSION:
        warnings.warn(
            f"Fixture dataset_version {fixture_dataset_version!r} differs from "
            f"harness DATASET_VERSION {DATASET_VERSION!r}; proceeding but flagging.",
            UserWarning,
            stacklevel=2,
        )

    if "attempt_number" not in data or "total_attempts_in_session" not in data:
        raise FixtureSchemaError(
            "Fixture missing required top-level 'attempt_number' and "
            "'total_attempts_in_session' integer fields."
        )

    canonical = _canonicalize_value(data)

    emus = _derive_emus(canonical)
    criterion_map = _load_criterion_map(mapping_spec_version)
    evaluations, non_evaluable, traceability = _apply_nc_map(emus, criterion_map)

    # Re-read spec and criterion map digests at call time (not at import) so
    # an edit to either file between two run() calls in the same process
    # surfaces as a different run_id. Spec-drift detection per spec §7.
    current_spec_id = spec_id()
    current_criterion_map_id = criterion_map_id(mapping_spec_version)

    report = ReplayReport(
        fixture_id=fixture_id,
        capture_id=capture_id,
        participant_id=participant_id,
        dataset_version=fixture_dataset_version,
        mapping_spec_version=mapping_spec_version,
        spec_id=current_spec_id,
        criterion_map_id=current_criterion_map_id,
        harness_version=HARNESS_VERSION,
        emu_outputs=emus,
        criterion_evaluations=evaluations,
        non_evaluable_criteria=non_evaluable,
        traceability=traceability,
    )
    report.run_id = _compute_run_id(
        fixture_id=fixture_id,
        dataset_version=fixture_dataset_version,
        mapping_spec_version=mapping_spec_version,
        spec_id=current_spec_id,
        criterion_map_id=current_criterion_map_id,
        harness_version=HARNESS_VERSION,
    )
    report.output_hash = _output_hash(report)
    return report
