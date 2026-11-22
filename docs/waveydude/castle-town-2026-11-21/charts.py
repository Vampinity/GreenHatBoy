"""Render the report's figures from the published CSVs. Requires Matplotlib."""

from csv import DictReader
from decimal import Decimal
from pathlib import Path
from statistics import median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
COLORS = {"off": "#6b7c91", "on": "#087f73", "off repeat": "#475b73"}
INK = "#172638"
MUTED = "#48596d"
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "text.color": INK,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.titlecolor": INK,
    "figure.facecolor": "#f7f9fc",
    "axes.facecolor": "#ffffff",
    "font.size": 10,
})


def read(name):
    with (ROOT / name).open(newline="") as f:
        return list(DictReader(f))


def canvas(title, subtitle, rows, cols, height):
    fig, axes = plt.subplots(rows, cols, figsize=(11, height), squeeze=False)
    fig.subplots_adjust(top=0.72 if rows == 1 else 0.79, left=0.09, right=0.97,
                        bottom=0.16 if rows == 1 else 0.11, hspace=0.72, wspace=0.39)
    fig.text(0.075, 0.945, title, fontsize=22, fontweight="bold", va="top")
    fig.text(0.077, 0.884 if rows == 2 else 0.865, subtitle, fontsize=10, color=MUTED, va="top")
    return fig, axes


def style(ax, title, ylabel):
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", pad=11)
    ax.set_ylabel(ylabel)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#e3e9ef", linewidth=0.9)
    ax.spines[:].set_visible(False)
    ax.tick_params(axis="both", length=0)


def bars(ax, rows, field, title, unit, labels=None, fmt=".0f"):
    style(ax, title, unit)
    values = [float(row[field]) for row in rows]
    colors = [COLORS[row["arm"]] for row in rows]
    patches = ax.bar(range(len(rows)), values, color=colors, width=0.57)
    ax.set_xticks(range(len(rows)), labels or [row["arm"].title() for row in rows])
    ax.set_ylim(0, max(values) * 1.26)
    ax.bar_label(patches, [format(value, fmt) for value in values], padding=4, fontsize=10)


def points(ax, rows, field, title, unit, fmt):
    style(ax, title, unit)
    values = [float(row[field]) for row in rows]
    ax.set_ylim(0, max(values) * 1.22)
    for i, arm in enumerate(("off", "on")):
        exact = [Decimal(row[field]) for row in rows if row["cleanup"] == arm]
        sample = [float(value) for value in exact]
        positions = [i + (j - (len(sample) - 1) / 2) * 0.12 for j in range(len(sample))]
        ax.scatter(positions, sample, s=39, color=COLORS[arm], alpha=0.8, zorder=3)
        mid = median(exact)
        ax.hlines(mid, i - 0.26, i + 0.26, color=COLORS[arm], lw=2.8, zorder=4)
        ax.text(i + 0.29, float(mid), format(mid, fmt), va="center", fontsize=9, fontweight="bold")
    ax.set_xlim(-0.45, 1.56)
    ax.set_xticks((0, 1), ("Off · 3 starts", "On · 4 starts"))


def save(fig, filename):
    fig.savefig(ROOT / filename, dpi=155)
    plt.close(fig)


textures = read("town-texture-runs.csv")
depth = read("depth-recheck.csv")
fig, ax = canvas("What improved inside Castle Town",
                 "Base PS5 9.40  •  Handheld 1× / FSR  •  Same warm shader store within each comparison",
                 2, 2, 7.8)
points(ax[0, 0], textures, "fps", "Drop old Field texture copies", "Presented FPS", ".2f")
points(ax[0, 1], textures, "worst_frame_ms", "Worst frame in each texture-cleanup run", "Milliseconds", ".0f")
bars(ax[1, 0], depth, "town_fps", "Depth recheck · one start per arm", "Presented FPS", fmt=".2f")
bars(ax[1, 1], depth, "mean_fence_ms_per_frame", "Depth recheck · graphics wait per frame",
     "Milliseconds", fmt=".1f")
fig.text(0.09, 0.041, "Dots are individual starts. Horizontal marks show the median. "
         "Depth recheck is a separate A/B pair.", color=MUTED, fontsize=9)
save(fig, "town-movement.png")

pairs = read("depth-recheck-five-pairs.csv")
fig, ax = canvas("Castle Town depth-feedback recheck",
                 "Base PS5 9.40  •  Handheld 1× / FSR  •  Same executable and warm shaders in all ten runs",
                 1, 2, 5.2)
for target, field, label, unit, fmt in (
    (ax[0, 0], "town_fps", "Presented frame rate", "FPS", ".2f"),
    (ax[0, 1], "worst_frame_ms", "Worst frame in each run", "Milliseconds", ".0f"),
):
    style(target, label, unit)
    for arm, shift in (("off", -0.21), ("on", 0.21)):
        rows = [row for row in pairs if row["arm"] == arm]
        values = [float(row[field]) for row in rows]
        patch = target.bar([int(row["pair"]) + shift for row in rows], values, width=0.32,
                           color=COLORS[arm], label=arm.title())
        target.bar_label(patch, [format(value, fmt) for value in values], padding=3, fontsize=8)
    target.set_ylim(0, max(float(row[field]) for row in pairs) * 1.3)
    target.set_xticks(range(1, 6), [f"Pair {number}" for number in range(1, 6)])
    target.legend(loc="upper right", frameon=False, fontsize=9, ncols=2)
fig.text(0.09, 0.045, "Median FPS 11.26 → 12.67. Median worst frame 132 → 117 ms. "
         "Link reached the final checkpoint sooner in four of five pairs.", color=MUTED, fontsize=9)
save(fig, "depth-recheck-five-pairs.png")

holds = read("fountain-runs.csv")
fig, ax = canvas("Scratch reserve at the fountain",
                 "Base PS5 9.40  •  All ten holds completed  •  Each bar counts driver requests for memory back",
                 1, 2, 4.9)
for i, seconds in enumerate((60, 120)):
    target = ax[0, i]
    subset = [row for row in holds if int(row["planned_hold_s"]) == seconds]
    pairs = sorted({int(row["pair"]) for row in subset})
    style(target, f"{seconds}-second hold", "Requests for memory back")
    for arm, shift in (("off", -0.17), ("on", 0.17)):
        values = [int(row["allocation_pressure_callbacks"]) for row in subset if row["reserve"] == arm]
        patch = target.bar([p + shift for p in pairs], values, width=0.32,
                           color=COLORS[arm], label=f"Reserve {arm}")
        target.bar_label(patch, padding=3)
    target.set_xticks(pairs, [f"Pair {p}" for p in pairs])
    target.set_ylim(0, 66 if seconds == 60 else 23)
    target.legend(loc="upper right", frameon=False, fontsize=9)
fig.text(0.09, 0.039, "Reported events can recur for the same request. These bars count log events, "
         "and every run still hit critical memory pressure.", color=MUTED, fontsize=9)
save(fig, "fountain-memory.png")

entry = read("entry-comparisons.csv")
cpu = [row for row in entry if row["firmware"] == "9.40"]
drain = [row for row in entry if row["firmware"] == "13.60"]
fig, ax = canvas("The entrance still has a long frame",
                 "Two separate experiments  •  Each result compares only runs on the same console and build",
                 2, 2, 7.8)
labels = ("Off", "On", "Off repeat")
bars(ax[0, 0], cpu, "first_frame_image_upload_ms", "9.40 · CPU texture conversion helper",
     "Image upload work (ms)", labels, ".1f")
bars(ax[0, 1], cpu, "worst_entrance_frame_ms", "9.40 · worst displayed entrance frame",
     "Milliseconds", labels)
bars(ax[1, 0], drain, "worst_entrance_frame_ms", "13.60 · drain-to-pool entrance frame",
     "Milliseconds")
bars(ax[1, 1], drain, "min_town_largest_block_mib", "13.60 · smallest free block sample",
     "Largest free block (MiB)")
fig.text(0.09, 0.039, "The 13.60 pair held about 16 FPS in aligned Town windows. "
         "A smaller free block leaves less space for a single allocation.", color=MUTED, fontsize=9)
save(fig, "town-entrance.png")
