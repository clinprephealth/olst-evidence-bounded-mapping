"""Ingest every committed fixture (synthetic + real) into the local lakehouse.

Re-running is a no-op — `ingest()` is keyed by content hash. Use this script
to refresh the snapshot under `artifacts/olst_lakehouse/` after fixture or
spec changes.

Usage (from repo root):
    PYTHONPATH=. python -m experiments.olst_nc_replay._ingest_all
"""

from __future__ import annotations

import warnings
from pathlib import Path

from experiments.olst_nc_replay import ExcludedCaptureError, run
from experiments.olst_nc_replay.lakehouse import (
    DEFAULT_LAKEHOUSE_DIR,
    ingest,
    list_runs,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SYNTHETIC = _REPO_ROOT / "experiments" / "olst_nc_replay" / "fixtures"
_REAL = _SYNTHETIC / "real"


def main() -> None:
    DEFAULT_LAKEHOUSE_DIR.mkdir(parents=True, exist_ok=True)

    pre = len(list_runs(DEFAULT_LAKEHOUSE_DIR))

    fixtures: list[Path] = []
    fixtures.extend(sorted(p for p in _SYNTHETIC.glob("*.json") if not p.name.startswith("golden_output_hashes_")))
    if _REAL.exists():
        fixtures.extend(sorted(_REAL.glob("*.json")))

    ingested = 0
    skipped = 0
    excluded = 0

    for fp in fixtures:
        fixture_text = fp.read_text(encoding="utf-8")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                rep = run(fp, mapping_spec_version="v1")
        except ExcludedCaptureError:
            excluded += 1
            continue
        appended = ingest(rep, fixture_text, DEFAULT_LAKEHOUSE_DIR)
        if any(v > 0 for v in appended.values()):
            ingested += 1
        else:
            skipped += 1

    post = len(list_runs(DEFAULT_LAKEHOUSE_DIR))
    print(f"lakehouse: {DEFAULT_LAKEHOUSE_DIR}")
    print(f"  fixtures scanned:    {len(fixtures)}")
    print(f"  newly ingested:      {ingested}")
    print(f"  already present:     {skipped} (idempotent no-ops)")
    print(f"  excluded by gate:    {excluded} (e.g. 12_MNTRL_V2)")
    print(f"  total runs in store: {post} (was {pre})")


if __name__ == "__main__":
    main()
