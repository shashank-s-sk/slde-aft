"""Builds two manuscript figures from committed sources only.

  paper/figures/fig_reliability.{pdf,png}
      Reliability diagram from outputs/dec003_real_calibration/
      calibration_bins_real.csv, which scripts/dec003_real_data_calibration.py
      regenerates from the committed snapshot
      outputs/dec003_product_probkb_v2/train_kb/pkb_snapshot_iteration_4.csv.

  paper/figures/fig_architecture.{pdf,png}
      Figure 1: the evaluated (as-built) pipeline, drawn from the module
      list verified against src/ and scripts/ in the manuscript's
      "Evaluated Framework" section. Only implemented components appear.

Static print figures: one ink colour plus greys, legible in grayscale.

Usage: python -m scripts.make_paper_figures
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

FIG_DIR = Path("paper/figures")
INK = "#1f4e79"      # single data hue (dark blue; reads as dark grey in print)
TEXT = "#1a1a1a"
MUTED = "#6b6b6b"
GRID = "#d9d9d9"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED,
    "axes.labelcolor": TEXT, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False,
})


def reliability() -> None:
    bins = pd.read_csv("outputs/dec003_real_calibration/calibration_bins_real.csv")
    fig, ax = plt.subplots(figsize=(4.6, 3.6))
    ax.plot([0, 1], [0, 1], ls="--", lw=1, color=MUTED, zorder=1)
    ax.text(0.47, 0.56, "perfect calibration", rotation=38, color=MUTED, fontsize=7.5,
            ha="center", va="center")
    for _, r in bins.iterrows():
        centre = (r.bin_lower + r.bin_upper) / 2
        if r.n == 0:
            ax.text(centre, 0.02, "empty", ha="center", va="bottom", fontsize=7, color=MUTED,
                    bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"), zorder=3)
            continue
        h = r.empirical_positive_rate
        # a measured rate of 0 gets a visible stub so it is not mistaken for an empty bin
        ax.bar(centre, max(h, 0.008), width=0.1 - 0.012, color=INK, zorder=2, linewidth=0)
        ax.text(centre, h + 0.015, f"n={int(r.n)}", ha="center", va="bottom", fontsize=7, color=TEXT)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.set_xticks([i / 10 for i in range(11)])
    ax.set_xlabel("Conflict-adjusted score (bin)")
    ax.set_ylabel("Fraction of triples correct")
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(FIG_DIR / f"fig_reliability.{ext}", dpi=300)
    plt.close(fig)


def box(ax, x, y, w, h, title, detail, style="solid", fill="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                linewidth=1.1, edgecolor=INK if style == "solid" else MUTED,
                                linestyle="-" if style == "solid" else "--", facecolor=fill, zorder=2))
    ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center", fontsize=8.2,
            fontweight="bold", color=TEXT, zorder=3)
    ax.text(x + w / 2, y + h * 0.3, detail, ha="center", va="center", fontsize=6.6,
            color=MUTED, zorder=3, linespacing=1.15)


def arrow(ax, p, q, label=None, style="solid", rad=0.0, lpos=0.5, loff=(0, 0.12)):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=9, lw=1.0, shrinkA=0,
                                 color=INK if style == "solid" else MUTED,
                                 linestyle="-" if style == "solid" else (0, (4, 3)),
                                 connectionstyle=f"arc3,rad={rad}", zorder=1))
    if label:
        mx = p[0] + (q[0] - p[0]) * lpos + loff[0]
        my = p[1] + (q[1] - p[1]) * lpos + loff[1]
        ax.text(mx, my, label, ha="center", va="center", fontsize=6.6, color=TEXT,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"), zorder=4)


def architecture() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7.2)
    ax.axis("off")
    W, H = 2.9, 1.05
    # inputs
    box(ax, 0.1, 5.6, 2.6, 0.95, "Structured records", "CSV / JSON", fill="#f4f6f8")
    box(ax, 0.1, 3.5, 2.6, 0.95, "Unstructured text", "plain text", fill="#f4f6f8")
    # extractors
    box(ax, 3.4, 5.55, W, H, "Structured extractor",
        "deterministic schema mapping\nfixed high confidence")
    box(ax, 3.4, 3.45, W, H, "LLM extractor",
        "Llama-3.1-8B-Instruct (OpenRouter)\nself-reported confidence 0.80-0.96")
    # PKB
    box(ax, 7.3, 4.45, 3.3, 1.35, "Probabilistic knowledge base",
        "conservative Noisy-OR + conflict penalty\n(DySECT Eqs. 1-2; $\\lambda$=0.75, $\\tau$=0.88)\nper-observation provenance")
    # feedback
    box(ax, 7.3, 2.2, 3.3, 1.2, "Feedback controller",
        "missing facts / false patterns /\nunder-covered predicates")
    box(ax, 10.8, 2.3, 0.8, 1.0, "Gold", "labels,\ntraining\nsplit only", fill="#f4f6f8")
    # fine-tuning path
    box(ax, 7.3, 0.2, 3.3, 1.2, "Provenance filter",
        "keeps admitted triples with structured\ncorroboration; builds synthetic examples")
    box(ax, 3.4, 0.2, W, 1.2, "QLoRA fine-tuning",
        "Mistral-7B-Instruct-v0.3\nrun manually on a rented GPU")

    arrow(ax, (2.7, 6.07), (3.4, 6.07))
    arrow(ax, (2.7, 3.97), (3.4, 3.97))
    arrow(ax, (6.3, 6.07), (7.3, 5.35))
    arrow(ax, (6.3, 3.97), (7.3, 4.8))
    ax.text(6.8, 5.02, "observations", ha="center", va="center", fontsize=6.6, color=TEXT,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"), zorder=4)
    arrow(ax, (8.95, 4.45), (8.95, 3.4))
    arrow(ax, (10.8, 2.8), (10.6, 2.8))
    arrow(ax, (7.3, 2.8), (4.85, 3.45), "feedback hint\n+ locked context", lpos=0.45, loff=(0, 0.05))
    ax.plot([10.6, 11.85, 11.85, 10.75], [5.1, 5.1, 0.8, 0.8], color=INK, lw=1.0, zorder=1)
    arrow(ax, (10.8, 0.8), (10.6, 0.8))
    arrow(ax, (7.3, 0.8), (6.3, 0.8))
    ax.text(6.8, 1.12, "training\ndata", ha="center", va="bottom", fontsize=6.6, color=TEXT)
    arrow(ax, (4.85, 1.4), (4.85, 3.45), "adapter (closed-loop\ntest only)", style="dashed",
          lpos=0.5, loff=(-0.95, 0))
    fig.tight_layout(pad=0.2)
    for ext in ("pdf", "png"):
        fig.savefig(FIG_DIR / f"fig_architecture.{ext}", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    reliability()
    architecture()
    print("wrote", sorted(p.name for p in FIG_DIR.glob("fig_*")))
