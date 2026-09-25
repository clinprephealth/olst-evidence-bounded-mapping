"""Step 1 / Step 2 driver: run every OLST attempt through the governed harness.

For one ``mapping_spec_version`` this script

  1. verifies the metadata CSVs and every referenced raw file against the
     release ``SHA256SUMS.txt`` (plan Step 1.1) and refuses to run unless the
     local mirror is complete, or ``--allow-partial`` is given (smoke tests
     only; never for the committed store);
  2. builds one fixture per attempt with ``olst_real_loader.build_fixture``
     and records a status per attempt:
        built | excluded_capture | source_missing_local |
        source_missing_upstream | build_refused
     Only ``built`` attempts produce runs. The two ``source_missing_*`` states
     are availability facts, not evidence gaps, and are never turned into
     non-evaluable criteria (amendment A7);
  3. runs each fixture N times (``--determinism-n``) and asserts one
     output_hash, ingests once, runs the naive baseline for comparison;
  4. if the map declares an ``aggregation`` block, aggregates each capture with
     ``olst_capture_aggregate`` and ingests the aggregate;
  5. writes ``artifacts/olst_full_corpus_<version>.json`` with inventory,
     statuses, identity digests, determinism, label distributions by
     cohort x protocol, and baseline agreement.

Usage (from repo root)::

    PYTHONPATH=. python -m experiments.olst_nc_replay._run_full_corpus \
        --mapping-spec-version v1 --determinism-n 100

Smoke test into the scratchpad::

    ... --allow-partial --limit-captures 3 --lakehouse /tmp/x/lake \
        --fixtures-dir /tmp/x/fixtures --out /tmp/x/summary.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
import time
import warnings
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from experiments.olst_nc_replay import (
    HARNESS_VERSION,
    ExcludedCaptureError,
    criterion_map_id,
    run,
    spec_id,
)
from experiments.olst_nc_replay.lakehouse import (
    DEFAULT_LAKEHOUSE_DIR,
    ingest,
    ingest_aggregate,
)
from experiments.olst_nc_replay.olst_capture_aggregate import AGGREGATOR_VERSION, aggregate_capture
from experiments.olst_nc_replay.olst_naive_baseline import naive_run
from experiments.olst_nc_replay.olst_real_loader import (
    _capture_id_modless,
    _parse_attempts,
    _parse_demographics,
    _parse_sha256sums,
    build_fixture,
)
from experiments.olst_nc_replay.olst_replay_harness import _criterion_map_path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATASET_ROOT = _REPO_ROOT / "data" / "physionet_olst" / "olst-mocap-forceplate-radar" / "1.0"
_DEFAULT_FIXTURES_DIR = _REPO_ROOT / "experiments" / "olst_nc_replay" / "fixtures" / "real_full"
_ARTIFACTS_DIR = _REPO_ROOT / "artifacts"

_EXCLUDED_RADAR_PREFIX = "12_MNTRL_RR_V2"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _raw_files_for(capture_id: str) -> list[str]:
    pid, movement, version = capture_id.split("_")
    return [
        f"Raw/MOCAP/{pid}/{pid}_{movement}_MC_{version}_pos.csv",
        f"Raw/ForcePlate/{pid}/{pid}_{movement}_FP_{version}_left.csv",
        f"Raw/ForcePlate/{pid}/{pid}_{movement}_FP_{version}_right.csv",
    ]


def _verify_sources(dataset_root: Path, captures: list[str]) -> dict[str, Any]:
    """Check metadata + referenced raw files against SHA256SUMS.txt."""
    sums = _parse_sha256sums(dataset_root / "SHA256SUMS.txt")
    report: dict[str, Any] = {"metadata": {}, "raw": {"verified": 0, "mismatch": [], "missing_local": [], "missing_upstream": []}}
    for rel in ("Metadata/OLST_Attempts.csv", "Metadata/Participant_Demographics.csv"):
        digest = _sha256(dataset_root / rel)
        report["metadata"][rel] = {"sha256": digest, "matches_manifest": sums.get(rel) == digest}
    per_capture: dict[str, str] = {}
    for cap in captures:
        status = "ok"
        for rel in _raw_files_for(cap):
            path = dataset_root / rel
            if rel not in sums:
                report["raw"]["missing_upstream"].append(rel)
                status = "source_missing_upstream"
                continue
            if not path.exists() or path.stat().st_size == 0:
                report["raw"]["missing_local"].append(rel)
                if status == "ok":
                    status = "source_missing_local"
                continue
            if _sha256(path) != sums[rel]:
                report["raw"]["mismatch"].append(rel)
                status = "hash_mismatch"
            else:
                report["raw"]["verified"] += 1
        per_capture[cap] = status
    report["per_capture"] = per_capture
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mapping-spec-version", required=True)
    ap.add_argument("--dataset-root", type=Path, default=_DATASET_ROOT)
    ap.add_argument("--fixtures-dir", type=Path, default=_DEFAULT_FIXTURES_DIR)
    ap.add_argument("--lakehouse", type=Path, default=DEFAULT_LAKEHOUSE_DIR)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--determinism-n", type=int, default=100)
    ap.add_argument("--allow-partial", action="store_true", help="proceed with an incomplete local mirror (smoke tests only)")
    ap.add_argument("--limit-captures", type=int, default=0)
    ap.add_argument("--artifact-suffix", default="", help="appended to the artifact name, e.g. '__spec1.4', so a new execution context never overwrites an earlier artifact")
    args = ap.parse_args(argv)

    version = args.mapping_spec_version
    t0 = time.time()
    map_path = _criterion_map_path(version)
    criterion_map = json.loads(map_path.read_text(encoding="utf-8"))
    has_aggregation = isinstance(criterion_map.get("aggregation"), dict)
    # The per-attempt summary columns follow the map's duration criterion: the
    # criterion carrying a `rule` block (v2+, Berg), else Morse gait_type (v1).
    summary_criterion = next(
        (cid for cid, spec in criterion_map.get("criteria", {}).items() if isinstance(spec.get("rule"), dict)),
        "gait_type",
    )

    attempts = _parse_attempts(args.dataset_root / "Metadata" / "OLST_Attempts.csv")
    demographics = _parse_demographics(args.dataset_root / "Metadata" / "Participant_Demographics.csv")

    by_capture: dict[str, list[Any]] = defaultdict(list)
    excluded_rows = 0
    for a in attempts:
        if a.radar_capture.startswith(_EXCLUDED_RADAR_PREFIX):
            excluded_rows += 1
            continue
        by_capture[_capture_id_modless(a.radar_capture)].append(a)
    captures = sorted(by_capture)
    if args.limit_captures:
        captures = captures[: args.limit_captures]

    print(f"[corpus] mapping_spec_version={version} captures={len(captures)} excluded_rows={excluded_rows}")
    sources = _verify_sources(args.dataset_root, captures)
    n_missing_local = len(sources["raw"]["missing_local"])
    n_missing_up = len(sources["raw"]["missing_upstream"])
    n_mismatch = len(sources["raw"]["mismatch"])
    print(f"[sources] verified={sources['raw']['verified']} missing_local={n_missing_local} missing_upstream={n_missing_up} mismatch={n_mismatch}")
    if n_mismatch:
        print("[sources] hash mismatches present; refusing to run.", file=sys.stderr)
        return 2
    if n_missing_local and not args.allow_partial:
        print("[sources] local mirror incomplete; refusing to run without --allow-partial (plan Step 1.1).", file=sys.stderr)
        return 2

    args.fixtures_dir.mkdir(parents=True, exist_ok=True)
    args.lakehouse.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    statuses: Counter[str] = Counter()
    determinism_divergences: list[str] = []
    aggregates: list[dict[str, Any]] = []
    reports_by_capture: dict[str, list[Any]] = defaultdict(list)

    for cap in captures:
        pid = cap.split("_")[0]
        cohort = demographics.get(pid, "unknown")
        protocol = cap.split("_")[1]
        src_status = sources["per_capture"][cap]
        for a in sorted(by_capture[cap], key=lambda x: x.an):
            row: dict[str, Any] = {
                "capture_id": cap,
                "participant_id": pid,
                "age_cohort": cohort,
                "protocol_code": protocol,
                "attempt_number": a.an,
                "is_attempt_final": a.is_attempt_final,
                "olst_attempt_id": a.olst_attempt_id,
            }
            if src_status in ("source_missing_local", "source_missing_upstream"):
                row["status"] = src_status
                statuses[src_status] += 1
                rows.append(row)
                continue
            try:
                fixture = build_fixture(args.dataset_root, pid, cap, a.an)
            except (FileNotFoundError, ValueError) as e:
                row["status"] = "build_refused"
                row["build_refused_reason"] = str(e)
                statuses["build_refused"] += 1
                rows.append(row)
                continue
            fixture_path = args.fixtures_dir / f"{cap}_an{a.an}.json"
            fixture_text = json.dumps(fixture, sort_keys=True, separators=(",", ":"))
            fixture_path.write_text(fixture_text, encoding="utf-8")

            try:
                hashes: set[str] = set()
                rep = None
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    for _ in range(max(1, args.determinism_n)):
                        rep = run(fixture_path, mapping_spec_version=version)
                        hashes.add(rep.output_hash)
            except ExcludedCaptureError:
                row["status"] = "excluded_capture"
                statuses["excluded_capture"] += 1
                rows.append(row)
                continue
            assert rep is not None
            if len(hashes) != 1:
                determinism_divergences.append(fixture_path.name)
            ingest(rep, fixture_text, args.lakehouse)
            reports_by_capture[cap].append(rep)
            naive = naive_run(fixture_path)

            gtc = next((e["payload"] for e in rep.emu_outputs if e["emu_type"] == "gait_temporal_control"), {})
            gait_eval = next((c for c in rep.criterion_evaluations if c["criterion_id"] == summary_criterion), None)
            gait_ne = next((c for c in rep.non_evaluable_criteria if c["criterion_id"] == summary_criterion), None)
            row.update(
                {
                    "status": "built",
                    "fixture_path": str(fixture_path.relative_to(_REPO_ROOT)) if fixture_path.is_relative_to(_REPO_ROOT) else str(fixture_path),
                    "fixture_id": rep.fixture_id,
                    "run_id": rep.run_id,
                    "output_hash": rep.output_hash,
                    "stability_phase_present": fixture.get("stability_phase") is not None,
                    "stability_duration_ms": gtc.get("stability_duration_ms"),
                    "stance_duration_ms": gtc.get("stance_duration_ms"),
                    "observation_ceiling_ms": gtc.get("observation_ceiling_ms"),
                    "sway_area_mm2": (fixture.get("force_plate") or {}).get("sway_area_mm2"),
                    "governed_gait": gait_eval["evaluation"] if gait_eval else None,
                    "governed_gait_detail": gait_eval.get("detail") if gait_eval else None,
                    "governed_gait_non_evaluable_reason": gait_ne["non_evaluable_reason"] if gait_ne else None,
                    "naive_gait": naive["gait_type"],
                    "traceability_pointers": sum(len(v) for v in rep.traceability.values()),
                    "non_evaluable_count": len(rep.non_evaluable_criteria),
                    "determinism_runs": max(1, args.determinism_n),
                    "determinism_distinct_hashes": len(hashes),
                }
            )
            statuses["built"] += 1
            rows.append(row)

        if has_aggregation and reports_by_capture.get(cap):
            agg = aggregate_capture(reports_by_capture[cap], criterion_map)
            agg["age_cohort"] = cohort
            agg["protocol_code_from_capture"] = protocol
            ingest_aggregate(agg, args.lakehouse)
            aggregates.append(agg)
        print(f"  {cap}: {Counter(r['status'] for r in rows if r['capture_id'] == cap)}", flush=True)

    built = [r for r in rows if r["status"] == "built"]

    def _dist(key: str, subset: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
        out: dict[str, Counter[str]] = defaultdict(Counter)
        for r in subset:
            label = r.get(key)
            out[f"{r['age_cohort']}/{r['protocol_code']}"][str(label)] += 1
        return {k: dict(v) for k, v in sorted(out.items())}

    inventory = {
        "participants": sorted({r["participant_id"] for r in rows}),
        "n_participants": len({r["participant_id"] for r in rows}),
        "n_captures": len(captures),
        "n_attempt_rows": len(rows),
        "excluded_metadata_rows": excluded_rows,
        "captures_per_participant": dict(sorted(Counter(c.split("_")[0] for c in captures).items())),
        "attempts_per_capture_distribution": dict(sorted(Counter(len(by_capture[c]) for c in captures).items())),
        "cohort_split_participants": dict(Counter(demographics.get(p, "unknown") for p in {c.split("_")[0] for c in captures})),
        "cohort_x_protocol_captures": dict(sorted(Counter(f"{demographics.get(c.split('_')[0], 'unknown')}/{c.split('_')[1]}" for c in captures).items())),
    }

    summary: dict[str, Any] = {
        "mapping_spec_version": version,
        "summary_criterion_id": summary_criterion,
        "identity": {
            "harness_version": HARNESS_VERSION,
            "spec_id": spec_id(),
            "criterion_map_id": criterion_map_id(version),
            "criterion_map_path": str(map_path.relative_to(_REPO_ROOT)),
            "aggregator_version": AGGREGATOR_VERSION if has_aggregation else None,
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "dataset": {"release": "physionet/olst-mocap-forceplate-radar/1.0", "root": str(args.dataset_root)},
        "sources": {k: v for k, v in sources.items() if k != "per_capture"},
        "inventory": inventory,
        "statuses": dict(statuses),
        "allow_partial": args.allow_partial,
        "determinism": {
            "n_per_fixture": max(1, args.determinism_n),
            "fixtures": len(built),
            "total_executions": len(built) * max(1, args.determinism_n),
            "divergent_fixtures": determinism_divergences,
        },
        "governed_gait_distribution_per_attempt": _dist("governed_gait", built),
        "naive_gait_distribution_per_attempt": _dist("naive_gait", built),
        "baseline": {
            "attempts_compared": len(built),
            "agreement": sum(1 for r in built if r["governed_gait"] is not None and r["governed_gait"] == r["naive_gait"]),
            "governed_non_evaluable": sum(1 for r in built if r["governed_gait"] is None),
            "governed_pointers_total": sum(r["traceability_pointers"] for r in built),
            "naive_pointers_total": 0,
        },
        "aggregates": {
            "count": len(aggregates),
            "evaluable": sum(1 for a in aggregates if a["evaluable"]),
            "distribution": {
                k: dict(v)
                for k, v in sorted(
                    (
                        (key, Counter(str(a["aggregate_evaluation"]) for a in aggregates if f"{a['age_cohort']}/{a['protocol_code_from_capture']}" == key))
                        for key in sorted({f"{a['age_cohort']}/{a['protocol_code_from_capture']}" for a in aggregates})
                    )
                )
            },
            "non_evaluable_reasons": Counter(a["non_evaluable_reason"].split(":")[0] for a in aggregates if not a["evaluable"]),
        } if has_aggregation else None,
        "rows": rows,
        "elapsed_s": round(time.time() - t0, 1),
    }

    out = args.out or (_ARTIFACTS_DIR / f"olst_full_corpus_{version}{args.artifact_suffix}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, sort_keys=True, default=dict) + "\n", encoding="utf-8")
    print(f"[done] statuses={dict(statuses)} determinism_divergent={len(determinism_divergences)} aggregates={len(aggregates)} elapsed={summary['elapsed_s']}s")
    print(f"[done] wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
