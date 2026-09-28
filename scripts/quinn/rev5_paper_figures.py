#!/usr/bin/env python3
"""Build the data-bound Revision 5 paper figures.

The script is intentionally independent of model checkpoints and GPU state.  It
reads the copied Revision 5 CSV/JSON sources and writes only under
``docs/papers/rev5/figures``.  It also emits a small manifest with the exact
inputs and summary statistics used by the figures.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DOMAIN_ORDER = [
    "en", "es", "pl", "fr", "de", "cs", "da", "pt", "fi", "hu",
    "bg", "it", "et", "el", "sk", "sv", "ro", "nl", "sl", "lt",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_retention_data(data_dir: Path) -> dict[str, dict[str, float]]:
    routed_rows = read_csv(data_dir / "a4_routed_cost.csv")
    matrix_rows = read_csv(data_dir / "ra2b_matrix.csv")
    routed = {row["lang"]: row for row in routed_rows}
    joint = {row["eval_lang"]: float(row["ppl"]) for row in matrix_rows if row["checkpoint"] == "lt"}
    missing = set(DOMAIN_ORDER) - set(routed) - set(joint)
    if missing:
        raise ValueError(f"missing retention domains: {sorted(missing)}")
    result = {}
    for domain in DOMAIN_ORDER:
        if domain not in routed or domain not in joint:
            raise ValueError(f"missing domain {domain}")
        result[domain] = {
            "acquisition": float(routed[domain]["acquisition_exit"]),
            "routed": float(routed[domain]["routed_p20"]),
            "joint": joint[domain],
        }
    return result


def make_retention_figure(data: dict[str, dict[str, float]], output: Path) -> dict[str, float]:
    x = np.arange(len(DOMAIN_ORDER))
    acq = np.array([data[d]["acquisition"] for d in DOMAIN_ORDER])
    routed = np.array([data[d]["routed"] for d in DOMAIN_ORDER])
    joint = np.array([data[d]["joint"] for d in DOMAIN_ORDER])
    routed_ratio = routed / acq
    joint_ratio = joint / acq
    summary = {
        "routed_median_ratio": float(np.median(routed_ratio)),
        "routed_min_ratio": float(np.min(routed_ratio)),
        "routed_max_ratio": float(np.max(routed_ratio)),
        "joint_median_ratio": float(np.median(joint_ratio)),
        "joint_max_ratio": float(np.max(joint_ratio)),
    }

    fig, ax = plt.subplots(figsize=(11.0, 4.2), constrained_layout=True)
    width = 0.34
    ax.bar(x - width / 2, routed, width, label="Routed", color="#3b78d8")
    ax.bar(x + width / 2, joint, width, label="Joint", color="#e69f00")
    ax.scatter(x, acq, marker="_", s=420, linewidths=2.5, color="black",
               label="Acquisition exit", zorder=5, clip_on=False)
    ax.set_yscale("log")
    ax.set_xticks(x, DOMAIN_ORDER, rotation=45, ha="right")
    ax.set_ylabel("Perplexity (log scale)")
    ax.set_title("RA2b final checkpoint: routed serving tracks acquisition; joint serving remains elevated")
    ax.grid(axis="y", which="both", alpha=0.25)
    ax.set_ylim(1.8, max(joint) * 1.35)
    ax.legend(loc="upper left", frameon=True)
    ax.text(
        0.99, 0.98,
        f"Routed median: {100 * (summary['routed_median_ratio'] - 1):+.1f}%\n"
        f"Joint median: {summary['joint_median_ratio']:.1f}× acquisition",
        transform=ax.transAxes, ha="right", va="top", fontsize=9,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.85},
    )
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    return summary


def make_expansion_figure(output: Path) -> dict[str, float]:
    labels = ["Base", "Random\n(+2048)", "Random\nto full", "Inert\nzeros", "Real ladder\n(lt)"]
    free = np.array([2.33, 9.57, 20.16, 2.33, 31.07])
    masked = np.array([2.33, 2.33, 2.33, 2.33, 2.31])
    x = np.arange(len(labels))
    width = 0.62
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.0), sharey=True, constrained_layout=True)
    for ax, values, title, color in (
        (axes[0], free, "Free-width joint PPL", "#d95f5f"),
        (axes[1], masked, "Masked@8192 PPL", "#2ca25f"),
    ):
        bars = ax.bar(x, values, width, color=color, alpha=0.9)
        ax.set_yscale("log")
        ax.set_ylim(1.8, 42)
        ax.set_xticks(x, labels)
        ax.set_title(title)
        ax.grid(axis="y", which="both", alpha=0.25)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value * 1.08, f"{value:.2f}",
                    ha="center", va="bottom", fontsize=8)
    axes[0].set_ylabel("English PPL (log scale)")
    fig.suptitle("Expansion control: free-width damage vs. masked storage preservation", fontsize=12)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    return {"base": 2.33, "random_one_block": 9.57, "random_full_width": 20.16,
            "inert_zeros": 2.33, "real_ladder_free": 31.07, "real_ladder_masked": 2.31}


def make_legacy_pareto_figure(output: Path) -> None:
    """Recreate the historical consolidation comparison from its source table."""
    systems = ["Sequential\nendpoint", "Merged\n×3", "Merged +\nprune 1/3", "+ replay\nfinetune", "Joint\nreference"]
    en = np.array([11.08, 5.08, 6.37, 2.58, 2.33])
    de = np.array([18.28, 3.51, 5.38, 2.575, 2.23])
    es = np.array([2.13, 2.67, 4.09, 2.41, 2.23])
    x = np.arange(len(systems))
    width = 0.23
    fig, ax = plt.subplots(figsize=(8.2, 4.2), constrained_layout=True)
    ax.bar(x - width, en, width, label="EN", color="#4c78a8")
    ax.bar(x, de, width, label="DE", color="#f58518")
    ax.bar(x + width, es, width, label="ES", color="#54a24b")
    ax.set_yscale("log")
    ax.set_ylim(1.7, 24)
    ax.set_xticks(x, systems)
    ax.set_ylabel("Held-out PPL (log scale)")
    ax.set_title("Legacy consolidation readout (not a K20 gate)")
    ax.grid(axis="y", which="both", alpha=0.25)
    ax.legend(frameon=True, ncol=3, loc="upper right")
    ax.text(0.01, 0.02, "Source: 2026-08-25 three-phase consolidation report; single-seed except replay row.",
            transform=ax.transAxes, fontsize=7, color="#444444")
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def make_architecture_figure(output: Path) -> None:
    fig, ax = plt.subplots(figsize=(11.0, 4.8), constrained_layout=True)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.96, "BDH: shared depth-recurrent cell with append-only growth",
            ha="center", va="top", fontsize=14, weight="bold")

    # Main cell panel.
    ax.add_patch(plt.Rectangle((0.03, 0.20), 0.62, 0.62, fill=False, linewidth=1.8,
                               edgecolor="#333333"))
    ax.text(0.34, 0.78, "one shared level  (repeat × L)", ha="center", va="center",
            fontsize=10, weight="bold")
    boxes = [
        (0.07, 0.48, 0.10, 0.14, "$x$\nresidual"),
        (0.21, 0.48, 0.10, 0.14, "$E$\nencoder"),
        (0.35, 0.48, 0.11, 0.14, "$a(u)$\nper-neuron\nattention"),
        (0.50, 0.48, 0.10, 0.14, "$E_v$\nvalue\nencoder"),
    ]
    for x, y, w, h, label in boxes:
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor="#eaf2f8", edgecolor="#3465a4", linewidth=1.2))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=8)
    for x0, x1 in ((0.17, 0.21), (0.31, 0.35), (0.46, 0.50)):
        ax.annotate("", xy=(x1, 0.55), xytext=(x0, 0.55),
                    arrowprops={"arrowstyle": "->", "lw": 1.4, "color": "#333333"})
    ax.add_patch(plt.Rectangle((0.21, 0.28), 0.19, 0.11, facecolor="#f5f0e6", edgecolor="#9b6b00"))
    ax.text(0.305, 0.335, "$u\\odot v$", ha="center", va="center", fontsize=10)
    ax.add_patch(plt.Rectangle((0.44, 0.28), 0.14, 0.11, facecolor="#fce4d6", edgecolor="#c65911"))
    ax.text(0.51, 0.335, "$D_c$\ndecoder", ha="center", va="center", fontsize=8)
    ax.annotate("", xy=(0.51, 0.40), xytext=(0.55, 0.48), arrowprops={"arrowstyle": "->", "lw": 1.2})
    ax.annotate("", xy=(0.44, 0.335), xytext=(0.40, 0.39), arrowprops={"arrowstyle": "->", "lw": 1.2})
    ax.add_patch(plt.Rectangle((0.07, 0.25), 0.10, 0.11, facecolor="#e6f2e6", edgecolor="#38761d"))
    ax.text(0.12, 0.305, "$x +$ LN", ha="center", va="center", fontsize=8)
    ax.annotate("", xy=(0.17, 0.305), xytext=(0.21, 0.335), arrowprops={"arrowstyle": "->", "lw": 1.2})
    ax.annotate("", xy=(0.12, 0.48), xytext=(0.12, 0.36), arrowprops={"arrowstyle": "->", "lw": 1.2})
    ax.annotate("", xy=(0.17, 0.305), xytext=(0.28, 0.20), arrowprops={"arrowstyle": "->", "lw": 1.2})
    ax.text(0.34, 0.235, "all levels reuse the same $(E,E_v,D_c)$", ha="center", va="center", fontsize=8, color="#444444")

    # Growth and routing panel.
    ax.add_patch(plt.Rectangle((0.70, 0.20), 0.27, 0.62, fill=False, linewidth=1.8, edgecolor="#333333"))
    ax.text(0.835, 0.78, "append-only growth", ha="center", va="center", fontsize=10, weight="bold")
    for i, (label, color) in enumerate((("old\nprefix", "#9fc5e8"), ("new\nterritory", "#f6b26b"))):
        y = 0.54 - i * 0.15
        ax.add_patch(plt.Rectangle((0.75, y), 0.16, 0.10, facecolor=color, edgecolor="#555555"))
        ax.text(0.83, y + 0.05, label, ha="center", va="center", fontsize=8)
    ax.annotate("append + zero-init\nweights", xy=(0.83, 0.49), xytext=(0.835, 0.68),
                ha="center", arrowprops={"arrowstyle": "->", "lw": 1.2})
    ax.add_patch(plt.Rectangle((0.75, 0.26), 0.16, 0.08, facecolor="#eee6f5", edgecolor="#674ea7"))
    ax.text(0.83, 0.30, "route mask\nold prefix / full", ha="center", va="center", fontsize=7)
    ax.annotate("", xy=(0.75, 0.30), xytext=(0.83, 0.24), arrowprops={"arrowstyle": "->", "lw": 1.2})
    ax.text(0.835, 0.235, "old path frozen", ha="center", va="center", fontsize=8, color="#38761d")
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.root.resolve()
    rev5 = root / "docs" / "papers" / "rev5"
    data_dir = rev5 / "data"
    figures_dir = rev5 / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    retention = load_retention_data(data_dir)
    retention_summary = make_retention_figure(retention, figures_dir / "f3_retention_bars.pdf")
    expansion_summary = make_expansion_figure(figures_dir / "f6_expansion_control.pdf")
    make_architecture_figure(figures_dir / "f_architecture.pdf")
    make_legacy_pareto_figure(figures_dir / "pareto_legacy_rev5.pdf")
    manifest = {
        "domain_order": DOMAIN_ORDER,
        "retention_summary": retention_summary,
        "expansion_summary": expansion_summary,
        "inputs": {
            str(path.relative_to(root)): sha256(path)
            for path in sorted(data_dir.iterdir())
            if path.is_file()
        },
    }
    (rev5 / "figure_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
