"""Builds all five manuscript figures (vector PDF + 300-dpi PNG).

  fig_rival_ceiling  analytical, from src/pkb_math.py
  fig_scalability    outputs/dec008_scalability/scalability_summary.csv (committed)
  fig_finetuning     values logged in Evidence log.md (EVID-034/037/040); the
                     5-epoch adapters were not committed, see FT_* below

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


# Categorical slots 1-3 of the dataviz reference palette (validated as an
# all-pairs set); each series also gets its own marker and dash so the
# figures stay legible in grayscale print.
SERIES = [("#2a78d6", "o", "-"), ("#eb6834", "s", "--"), ("#1baf7a", "^", ":")]


def save(fig, name):
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(FIG_DIR / f"{name}.{ext}", dpi=300)
    plt.close(fig)


def rival_ceiling() -> None:
    """Analytical: C(t) = A(t)/(m+1), A(t) = 1 - (1 - lambda*c)^n, from
    src/pkb_math.py, with lambda=0.75 and every observation c=0.90."""
    from src.pkb_math import conservative_noisy_or

    ns = list(range(1, 9))
    fig, ax = plt.subplots(figsize=(4.6, 3.3))
    ax.axhline(0.88, color=MUTED, lw=0.9, ls="--")
    ax.text(2.6, 0.845, r"threshold $\tau=0.88$", va="top", fontsize=7.5, color=MUTED)
    ax.axhline(0.5, color=MUTED, lw=0.9, ls=":")
    ax.text(3.2, 0.535, r"$1/(m+1)$ bound for $m=1$", va="bottom", fontsize=7.5, color=MUTED)
    for m, (col, mk, ls) in zip((0, 1, 2), SERIES):
        ys = [conservative_noisy_or([0.9] * n, shrinkage=0.75) / (m + 1) for n in ns]
        ax.plot(ns, ys, color=col, marker=mk, ms=4, lw=1.6, ls=ls)
        ax.text(ns[-1] + 0.15, ys[-1] - 0.035, f"m = {m}", fontsize=7.5, color=TEXT)
    ax.set_xlim(0.7, 9.2)
    ax.set_ylim(0, 1.02)
    ax.set_xticks(ns)
    ax.set_xlabel("Agreeing observations of the candidate")
    ax.set_ylabel("Final score $C(t)$")
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    save(fig, "fig_rival_ceiling")


def scalability() -> None:
    """From the committed outputs/dec008_scalability/scalability_summary.csv.
    Runtime and latency are separate panels (no second y-axis); knowledge-
    base size is labelled on the runtime points."""
    d = pd.read_csv("outputs/dec008_scalability/scalability_summary.csv")
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 2.8))
    a.plot(d.n_products, d.total_runtime_s, color=INK, marker="o", ms=4, lw=1.6)
    for _, r in d.iterrows():
        a.text(r.n_products + 6, r.total_runtime_s - 25, f"KB {int(r.kb_size):,}", ha="left",
               va="top", fontsize=6.8, color=MUTED)
    a.set_xlabel("Products (N)")
    a.set_ylabel("Total runtime (s)")
    a.set_ylim(0, 900)
    a.set_title("(a) Runtime and KB size", fontsize=8.5, loc="left", color=TEXT)
    for (col, mk, ls), key, lab in zip(SERIES, ("mean_latency_s_per_doc", "max_latency_s"),
                                       ("mean", "max")):
        b.plot(d.n_products, d[key], color=col, marker=mk, ms=4, lw=1.6, ls=ls)
        b.text(d.n_products.iloc[-1] + 6, d[key].iloc[-1], lab, va="center", fontsize=7.5, color=TEXT)
    b.set_xlabel("Products (N)")
    b.set_ylabel("Latency per document (s)")
    b.set_ylim(0, 22)
    b.set_xlim(0, 235)
    b.set_title("(b) Per-document latency", fontsize=8.5, loc="left", color=TEXT)
    for ax in (a, b):
        ax.set_xticks(list(d.n_products))
        ax.yaxis.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    save(fig, "fig_scalability")


# Values for the superseded 8-product fine-tuning exploration, as logged in
# Evidence log.md (EVID-037 epoch sweep; EVID-034 3-epoch seeds; EVID-040
# 5-epoch seeds). The 5-epoch adapters and their evaluation files were run
# on a rented pod and are not in this repository, so these numbers are the
# logged values, not recomputed here.
FT_BASE = 0.1373
FT_EPOCHS = {0: (0.1522, 0.1250, 0.1373), 2: (0.2121, 0.1250, 0.1573), 3: (0.5385, 0.1250, 0.2029),
             5: (1.0000, 0.1250, 0.2222), 8: (1.0000, 0.1250, 0.2222)}
FT_SEEDS = {"3 epochs": [0.2029, 0.2090, 0.1124, 0.1935, 0.1892],
            "5 epochs": [0.2222, 0.1972, 0.2222, 0.1935, 0.1707]}


def finetuning() -> None:
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 2.8))
    eps = sorted(FT_EPOCHS)
    for i, ((col, mk, ls), lab) in enumerate(zip(SERIES, ("precision", "recall", "$F_1$"))):
        ys = [FT_EPOCHS[e][i] for e in eps]
        a.plot(eps, ys, color=col, marker=mk, ms=4, lw=1.6, ls=ls)
        a.text(eps[-1] + 0.3, ys[-1] + (0.03 if i == 1 else 0), lab, va="center", fontsize=7.5,
               color=TEXT)
    a.set_xticks(eps)
    a.set_xticklabels(["base"] + [str(e) for e in eps[1:]])
    a.set_xlim(-0.4, 10)
    a.set_ylim(0, 1.05)
    a.set_xlabel("Training epochs (seed 42)")
    a.set_title("(a) Epoch sweep", fontsize=8.5, loc="left", color=TEXT)
    seeds = [42, 43, 44, 45, 46]
    # seeds are categories, not a sequence: dots, no joining lines
    for k, ((col, mk, _), (lab, vals)) in enumerate(zip(SERIES, FT_SEEDS.items())):
        xs = [s + (-0.12 if k == 0 else 0.12) for s in seeds]
        b.plot(xs, vals, color=col, marker=mk, ms=5.5, lw=0, label=lab)
    b.legend(frameon=False, fontsize=7.5, loc="lower left", ncol=2)
    b.axhline(FT_BASE, color=MUTED, lw=0.9, ls="--")
    b.text(46.9, FT_BASE + 0.004, "base model", fontsize=7, color=MUTED, va="bottom", ha="right")
    b.set_xticks(seeds)
    b.set_xlim(41.7, 47.3)
    b.set_ylim(0.08, 0.25)
    b.set_xlabel("Seed")
    b.set_ylabel("Test $F_1$")
    b.set_title("(b) Test $F_1$ per seed", fontsize=8.5, loc="left", color=TEXT)
    for ax in (a, b):
        ax.yaxis.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    save(fig, "fig_finetuning")


if __name__ == "__main__":
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    reliability()
    architecture()
    rival_ceiling()
    scalability()
    finetuning()
    print("wrote", sorted(p.name for p in FIG_DIR.glob("fig_*")))
