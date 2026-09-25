"""Naive heuristic baseline for the OLST/NC comparison.

Threshold the 10-second clinical cutoff on stability duration; map directly to
Morse gait categories. No EMU layer, no traceability, no explicit non-evaluable
markers, no replay determinism guarantees beyond what Python's stdlib trivially
gives. This is the strawman the governed harness is measured against.

Usage:
    from experiments.olst_nc_replay.olst_naive_baseline import naive_run

    result = naive_run(fixture_path)
    # -> {"capture_id": ..., "gait_type": "normal" | "weak" | "impaired" | None}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Same 10s cutoff as the OLST clinical convention. The naive version is
# duration-only — it ignores sway, missing data, axis flips, unit mismatches.
_CLINICAL_CUTOFF_MS = 10000


def naive_run(fixture_path: str | Path) -> dict[str, Any]:
    path = Path(fixture_path)
    data = json.loads(path.read_text(encoding="utf-8"))

    capture_id = data.get("capture_id", "unknown")
    stability = data.get("stability_phase") or {}
    start = stability.get("start_ms")
    end = stability.get("end_ms")

    # Naive fallback: zero-fill missing stability fields. The whole point of
    # this baseline is that it does NOT surface gaps — it produces a number.
    if not isinstance(start, int):
        start = 0
    if not isinstance(end, int):
        end = 0
    duration_ms = end - start

    if duration_ms >= _CLINICAL_CUTOFF_MS:
        gait_type: str = "normal"
    elif duration_ms >= 5000:
        gait_type = "weak"
    else:
        gait_type = "impaired"

    return {
        "capture_id": capture_id,
        "stability_duration_ms": duration_ms,
        "gait_type": gait_type,
        # Crucially absent: traceability, EMU pointers, non-evaluable reasons.
    }
