#!/usr/bin/env python3
"""Plot the supplied held-out estimates and conditional intervals; no refitting."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source-root", type=Path, default=Path("."))
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
rows = {r["key"]: r for r in json.loads(
    (args.source_root / "analysis_summary/summary.json").read_text())}
args.out.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 12,
    "svg.fonttype": "path", "svg.hashsalt": "delivery-rules-20261012",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.edgecolor": "#bac7c7",
    "text.color": "#213534", "axes.labelcolor": "#425756",
    "xtick.color": "#536766", "ytick.color": "#213534",
})
fig, ax = plt.subplots(figsize=(11.4, 4.4), facecolor="white")
fig.subplots_adjust(left=.25, right=.94, top=.78, bottom=.22)
for suffix, offset, color, label in [
    ("S_to_P", .14, "#be592b", "Strict → partial"),
    ("P_to_S", -.14, "#087d76", "Partial → strict"),
]:
    for i, key in enumerate(["nine", "exact4", "at_most4"]):
        row = rows[f"{key}_{suffix}"]
        mean = row["estimate_pp"]
        ax.errorbar(mean, 2-i+offset,
                    xerr=[[mean-row["ci95_lower_pp"]],
                          [row["ci95_upper_pp"]-mean]],
                    fmt="o", color=color, markersize=7, capsize=4,
                    elinewidth=1.8, label=label if i == 0 else None)
        ax.annotate(f"{mean:.3f}", (row["ci95_upper_pp"], 2-i+offset),
                    xytext=(10, -4), textcoords="offset points",
                    fontsize=11, color=color)
ax.axvline(0, color="#a7b6b5", linewidth=1, linestyle="--", zorder=0)
ax.set_yticks([2, 1, 0], ["All nine configurations", "Exactly four solver calls\n6 configurations",
                         "At most four solver calls\n8 configurations"])
ax.set_ylim(-.5, 2.5)
ax.set_xlim(-.35, 8.8)
ax.set_xticks([0, 2, 4, 6, 8])
ax.set_xlabel("Target-rule selection minus source-rule selection (percentage points)", labelpad=12)
ax.tick_params(axis="y", length=0, pad=15)
ax.grid(axis="x", color="#e6eded", linewidth=.8)
ax.set_axisbelow(True)
ax.legend(loc="lower left", bbox_to_anchor=(-.34, 1.12), ncol=2, frameon=False,
          handletextpad=.6, columnspacing=2.2)
fig.text(.035, .025, "Bars: 95% conditional bootstrap intervals, with out-of-fold choices held fixed.",
         fontsize=10, color="#536766")
fig.savefig(args.out / "method-choice.svg", metadata={"Date": None,
            "Title": "Held-out selection differences by candidate set"})
fig.savefig(args.out / "method-choice.png", dpi=180)
plt.close(fig)
print("Created method-choice.svg and method-choice.png")
