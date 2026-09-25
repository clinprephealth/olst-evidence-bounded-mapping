"""Generate the manuscript's data figures from committed artifacts.

Figure 2  — duration constructs by acquisition protocol (D1): ECDFs of the
            stable-phase window and the stance interval, per attempt, with
            the clinical boundaries and the two protocol ceilings marked.
Figure 3  — the versioned recalibration: per-attempt label composition under
            v1, v2, v2.1 for the short (MNTR) and sustained (TRLG) protocols,
            plus the capture-level aggregate.

Inputs are the committed artifacts only (no PhysioNet data needed):
    protocol/d1_distributions.json
    artifacts/olst_full_corpus_{v1,v2,v2.1}.json

Usage (from repo root, any Python with matplotlib):
    python experiments/olst_nc_replay/paper/figures/_make_figures.py
Writes fig2_duration_constructs.{svg,png} and fig3_versioned_recalibration.{svg,png}
next to this script. Deterministic: no randomness, fixed ordering.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
D1 = REPO / "experiments" / "olst_nc_replay" / "protocol" / "d1_distributions.json"
ART = REPO / "artifacts"

# Palette: validated categorical slots 1-3 (all-pairs) for protocol groups;
# one-hue ordinal ramp for the label states; neutrals for withheld states.
GROUP_COLOR = {"young MNTR": "#2a78d6", "older MNTR": "#eb6834", "older TRLG": "#1baf7a"}
LABEL_COLOR = {
    "normal": "#1c5cab",
    "weak": "#3987e5",
    "impaired": "#86b6ef",
    "protocol_censored": "#c3c2b7",
    "non-evaluable": "#e1e0d9",
}
INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 8.5,
    "axes.edgecolor": BASE,
    "axes.labelcolor": INK2,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "svg.fonttype": "none",
})


def _group(cohort: str, capture: str) -> str:
    return f"{cohort} {'TRLG' if capture.split('_')[1].startswith('TRLG') else 'MNTR'}"


def _ecdf(values: list[float]) -> tuple[list[float], list[float]]:
    xs = sorted(values)
    n = len(xs)
    return xs, [(i + 1) / n for i in range(n)]


def figure2() -> None:
    d = json.load(open(D1))
    rows = d["rows"]
    groups = ["young MNTR", "older MNTR", "older TRLG"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
    panels = [
        ("stable_phase_s", "a  Stable-phase window  (t_stable to t_break)", "window length (s), log scale"),
        ("stance_s", "b  Stance interval  (t_foot_up to t_end)", "stance duration (s), log scale"),
    ]
    for ax, (field, title, xlabel) in zip(axes, panels):
        ax.set_xscale("log")
        ax.set_xlim(0.02, 30)
        ax.set_ylim(0, 1.0)
        for x, lab in ((3, "3 s"), (5, "5 s"), (10, "10 s")):
            ax.axvline(x, color=GRID, lw=1, zorder=0)
            ax.text(x * 1.04, 0.985, lab, ha="left", va="top", fontsize=6.5, color=MUTED)
        # protocol ceilings (instructed durations): 4 s cue, 20 s trial
        ax.axvline(4, color=INK2, lw=1, ls=(0, (2, 2)), zorder=1)
        ax.axvline(20, color=INK2, lw=1, ls=(0, (2, 2)), zorder=1)
        ax.text(4 / 1.06, 0.50, "4 s cue", rotation=90, ha="right", va="center", fontsize=6.5, color=INK2)
        ax.text(20 / 1.06, 0.50, "20 s trial", rotation=90, ha="right", va="center", fontsize=6.5, color=INK2)
        for g in groups:
            vals = [r[field] for r in rows if r[field] is not None and _group(r["cohort"], r["capture"]) == g]
            if not vals:
                continue
            xs, ys = _ecdf(vals)
            ax.step(xs, ys, where="post", color=GROUP_COLOR[g], lw=2, label=f"{g} (n={len(vals)})")
        ax.set_title(title, loc="left", fontsize=9, color=INK, pad=6)
        ax.set_xlabel(xlabel)
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.legend(loc="upper left", frameon=False, fontsize=7)
    axes[0].set_ylabel("cumulative fraction of attempts")
    fig.tight_layout()
    for ext in ("svg", "png"):
        fig.savefig(HERE / f"fig2_duration_constructs.{ext}", dpi=300)
    plt.close(fig)


def _label(r: dict) -> str:
    return r["governed_gait"] or "non-evaluable"


def figure3() -> None:
    maps = ["v1", "v2", "v2.1"]
    order = ["normal", "weak", "impaired", "protocol_censored", "non-evaluable"]
    protocols = [("MNTR", "Short cued protocol (MNTR, 776 attempts; 4 s cue, ceiling unpublished at execution)"),
                 ("TRLG", "Sustained protocol (TRLG, 457 attempts; 20 s trial)")]
    data = {v: json.load(open(ART / f"olst_full_corpus_{v}.json")) for v in maps}
    aggs = {v: data[v].get("aggregates") for v in maps}

    fig, axes = plt.subplots(2, 1, figsize=(7.2, 3.6), sharex=True)
    for ax, (proto, title) in zip(axes, protocols):
        for i, v in enumerate(maps):
            rows = [r for r in data[v]["rows"] if r["status"] == "built" and r["protocol_code"].startswith(proto)]
            c = Counter(_label(r) for r in rows)
            total = sum(c.values())
            left = 0.0
            for lab in order:
                n = c.get(lab, 0)
                if n == 0:
                    continue
                w = n / total
                hatch = "////" if lab == "protocol_censored" else None
                ax.barh(i, w, left=left, height=0.62, color=LABEL_COLOR[lab], edgecolor="#fcfcfb", linewidth=1.5, hatch=hatch)
                if w > 0.07:
                    ink = "#ffffff" if lab in ("normal", "weak") else INK
                    ax.text(left + w / 2, i, f"{n}", ha="center", va="center", fontsize=7.5, color=ink)
                left += w
        ax.set_yticks(range(len(maps)))
        ax.set_yticklabels(["v1  (stable phase, sway gate)", "v2  (stance, censoring, sway gate)", "v2.1  (stance, censoring, sway reported only)"], fontsize=7.5)
        ax.invert_yaxis()
        ax.set_xlim(0, 1)
        ax.set_title(title, loc="left", fontsize=8.5, color=INK)
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
        ax.grid(axis="x", color=GRID, lw=0.6, zorder=0)
        ax.set_axisbelow(True)
    axes[1].set_xlabel("fraction of attempts")
    handles = [Patch(facecolor=LABEL_COLOR[l], edgecolor="#fcfcfb", hatch="////" if l == "protocol_censored" else None,
                     label={"non-evaluable": "non-evaluable (no stable phase, so no CoP evidence)", "protocol_censored": "protocol censored"}.get(l, l))
               for l in order]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, fontsize=7, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    for ext in ("svg", "png"):
        fig.savefig(HERE / f"fig3_versioned_recalibration.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # Numbers for the caption / A14 panel, printed for the author.
    for v in maps:
        rows = [r for r in data[v]["rows"] if r["status"] == "built"]
        print(v, dict(Counter(_label(r) for r in rows)))
        if aggs[v]:
            print("   aggregates:", aggs[v]["count"], "evaluable", aggs[v]["evaluable"], aggs[v]["distribution"])


if __name__ == "__main__":
    figure2()
    figure3()
    print("wrote", sorted(p.name for p in HERE.glob("fig*.*")))
