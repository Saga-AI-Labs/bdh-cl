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


# Pooled joint perplexity on the same 20-domain evaluation crops, measured in the
# closed-set probe (2026-09-11_a3-closed-set-probe.md, section V4). The trained
# routing-advantage convention in the manuscript (5.7x-15.6x) is reference / routed.
OOD_JOINT_REFERENCE = 36.76
OOD_UNSEEN_ORDER = ["lv", "ga", "zh", "ja", "hi", "iu_clean"]


def make_ood_scatter_figure(data_dir: Path, output: Path) -> dict[str, float]:
    """Two-axis OOD separation (regenerated: the rev4 PDF plotted the ra2b_matrix
    lt-row joint values on the y axis; trained languages must sit at their routed
    ppl 2.36-6.47 with advantage = pooled joint reference / routed)."""
    retention = load_retention_data(data_dir)
    unseen = {row["language"]: row for row in read_csv(data_dir / "ood_axes.csv")}
    missing = [lang for lang in OOD_UNSEEN_ORDER if lang not in unseen]
    if missing:
        raise ValueError(f"missing unseen languages in ood_axes.csv: {missing}")

    trained_x = {d: OOD_JOINT_REFERENCE / retention[d]["routed"] for d in DOMAIN_ORDER}
    trained_y = {d: retention[d]["routed"] for d in DOMAIN_ORDER}
    unseen_x = [float(unseen[lang]["ratio"]) for lang in OOD_UNSEEN_ORDER]
    unseen_y = [float(unseen[lang]["best_route_ppl"]) for lang in OOD_UNSEEN_ORDER]
    summary = {
        "trained_ratio_min": min(trained_x.values()),
        "trained_ratio_max": max(trained_x.values()),
        "trained_ppl_min": min(trained_y.values()),
        "trained_ppl_max": max(trained_y.values()),
    }

    fig, ax = plt.subplots(figsize=(8.6, 6.0), constrained_layout=True)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.7, 30)
    ax.set_ylim(1.8, 1600)

    # Reject regions and threshold guides: relative axis < 5x, absolute axis > ~10x
    # the trained acquisition ceiling (6.5 * 10).
    ax.axvspan(0.7, 5.0, color="#f5cccc", alpha=0.30, zorder=0)
    ax.axhspan(65.0, 1600, color="#f5cccc", alpha=0.30, zorder=0)
    ax.axvline(5.0, color="#b04a4a", linestyle="--", linewidth=1.3, zorder=1)
    ax.axhline(65.0, color="#b04a4a", linestyle=":", linewidth=1.3, zorder=1)
    ax.text(5.15, 2.1, "trained floor (5x)", fontsize=8, color="#b04a4a", rotation=90,
            va="bottom")
    ax.text(0.75, 72.0, "~10x acquisition ceiling", fontsize=8, color="#b04a4a", va="bottom")

    ax.scatter(list(trained_x.values()), list(trained_y.values()), s=55, marker="o",
               color="#2b6cb0", label="trained (20)", zorder=3)
    # The 20 trained points form one tight blob (routed ppl 2.36-6.47): label
    # only the extremes and annotate the cluster (review: 20 labels unreadable).
    for d, dx, dy in (("en", 6, -9), ("el", 5, 4), ("bg", 5, -11), ("lt", 2, -12)):
        ax.annotate(d, (trained_x[d], trained_y[d]), textcoords="offset points",
                    xytext=(dx, dy), fontsize=7, color="#2b6cb0")
    ax.text(7.0, 10.0, "20 trained languages\n(routed ppl 2.36–6.47)",
            fontsize=8.5, color="#2b6cb0", va="center")
    ax.scatter(unseen_x, unseen_y, s=65, marker="D", color="#2f8f4e",
               label="unseen (6)", zorder=4)
    for i, lang in enumerate(OOD_UNSEEN_ORDER):
        dx, dy = (6, 3) if i % 2 == 0 else (6, -10)
        ax.annotate(lang, (unseen_x[i], unseen_y[i]), textcoords="offset points",
                    xytext=(dx, dy), fontsize=7.5, color="#1e6b34")

    ax.set_xlabel("Routing advantage (joint / best-route ppl)")
    ax.set_ylabel("Best-route ppl (absolute)")
    ax.set_title("Two-axis OOD separation: 20 trained (blue) vs 6 unseen (diamonds)",
                 fontsize=11)
    ax.grid(which="both", alpha=0.2)
    ax.legend(loc="upper left", frameon=True, fontsize=9)
    # Convention note in the empty lower-left quadrant (the lower-right corner
    # collides with the trained blob). lv shares the pooled reference (a3 V4);
    # ga and the cross-script probes use own-corpus joints (a3 V5, X3).
    ax.text(
        0.02, 0.02,
        "trained + lv: pooled joint ref 36.76 / routed (a3 V4)\n"
        "ga + cross-script: own-corpus joint / routed (a3 V5, X3)\n"
        "lt: own prefix = full width (per-domain 1x; 9.1x pooled)",
        transform=ax.transAxes, ha="left", va="bottom", fontsize=7, color="#444444",
    )
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    return summary


# Closed-form f64 schedule products (2026-09-04_decay-family report, appendix B.1):
# G/GR/G2 defaults schedule 0.892752 (f32 realization 0.892636); RA2 cosine 0.579775.
DECAY_CLOSED_FORM = {"G": 0.892752, "RA2": 0.579775}


def make_decay_figure(data_dir: Path, output: Path) -> dict[str, float]:
    """Decay regimes with measured per-segment c-fits (labels corrected: legend
    quotes the manuscript's c values and the es -> en_best target)."""
    rows = read_csv(data_dir / "decay_cfits.csv")
    k = np.arange(0, 21)
    g_curve = DECAY_CLOSED_FORM["G"] ** k
    ra_curve = DECAY_CLOSED_FORM["RA2"] ** k

    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.4), sharey=True,
                             constrained_layout=True)
    for ax in axes:
        ax.set_yscale("log")
        ax.set_ylim(1e-6, 200)
        ax.set_xlim(-0.5, 20.5)
        ax.set_xlabel("Phases after segment creation (k)")
        ax.grid(which="both", alpha=0.25)
    axes[0].set_ylabel("Segment amplitude (relative)")
    axes[0].set_title("Closed-form decay: $c^k$", fontsize=11)
    axes[1].set_title("Prediction vs measurement", fontsize=11)

    axes[0].plot(k, g_curve, color="#2b6cb0", label="G-family (defaults 30/300)")
    axes[0].plot(k, ra_curve, color="#d95f5f", label="RA2 (cosine 1000/10000)")
    axes[0].legend(fontsize=8, loc="lower left")

    for ax in axes:
        ax.plot(k, g_curve, color="#2b6cb0",
                label="G schedule product c=0.8927 (exact 0.892752)")
        ax.plot(k, ra_curve, color="#d95f5f",
                label="RA2 schedule product c=0.5798 (exact 0.579775)")
    g_fits = [(int(r["k"]), float(r["amplitude"])) for r in rows if r["family"] != "RA2"]
    ra_fits = [(int(r["k"]), float(r["amplitude"])) for r in rows if r["family"] == "RA2"]
    axes[1].scatter([p[0] for p in g_fits], [p[1] for p in g_fits], s=45, marker="o",
                    color="#333333", zorder=5, label="Measured (c-fits, resid 1e-5)")
    axes[1].scatter([p[0] for p in ra_fits], [p[1] for p in ra_fits], s=55, marker="s",
                    color="#c0392b", zorder=6,
                    label="Measured (es $\\to$ en_best, sd 2.2e-7)")
    axes[1].legend(fontsize=7.5, loc="lower left")

    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    return {"g_closed_form": DECAY_CLOSED_FORM["G"], "ra2_closed_form": DECAY_CLOSED_FORM["RA2"],
            "g_fits": {r["segment"] + ":" + r["family"]: r["amplitude"] for r in rows if r["family"] != "RA2"}}


def make_cross_script_figure(data_dir: Path, output: Path) -> dict[str, int]:
    """Cross-script routing confusion (iu-clean split from the pi-50 likelihood
    router census: el 28 / bg 12 -- replaces the unreported 20/20 placeholder)."""
    rows = read_csv(data_dir / "xscript_confusion.csv")
    langs = [r["lang"] for r in rows]
    to_el = np.array([int(r["to_el"]) for r in rows])
    to_bg = np.array([int(r["to_bg"]) for r in rows])
    to_other = np.array([int(r["to_other"]) for r in rows])
    totals = to_el + to_bg + to_other
    if not (totals == 40).all():
        raise ValueError("cross-script rows must sum to 40 crops")

    x = np.arange(len(langs))
    width = 0.55
    fig, ax = plt.subplots(figsize=(7.6, 4.4), constrained_layout=True)
    ax.bar(x, to_el, width, label="to el (Greek)", color="#e69f00")
    ax.bar(x, to_bg, width, bottom=to_el, label="to bg (Cyrillic)", color="#9467bd")
    ax.bar(x, to_other, width, bottom=to_el + to_bg, label="other routes", color="#aaaaaa")
    for i, lang in enumerate(langs):
        high_byte = int(to_el[i] + to_bg[i])
        ax.text(x[i], int(totals[i]) + 0.9, f"{high_byte}/40 bg+el",
                ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x, langs)
    ax.set_ylim(0, 47)
    ax.set_ylabel("Crops (of 40)")
    ax.set_title("Cross-script routing concentrates on high-byte territories", fontsize=11)
    ax.legend(frameon=True, fontsize=8, loc="center left", bbox_to_anchor=(1.02, 0.5))
    ax.grid(axis="y", alpha=0.25)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    return {lang: int(to_el[i] + to_bg[i]) for i, lang in enumerate(langs)}


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
    # Source note moved into the LaTeX caption (review: it overlapped the bars).
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
    ax.text(0.33, 0.585, "ReLU", ha="center", va="bottom", fontsize=6, color="#555555")
    ax.text(0.48, 0.585, "LN", ha="center", va="bottom", fontsize=6, color="#555555")
    ax.add_patch(plt.Rectangle((0.21, 0.28), 0.19, 0.11, facecolor="#f5f0e6", edgecolor="#9b6b00"))
    ax.text(0.305, 0.335, "$u\\odot v$", ha="center", va="center", fontsize=10)
    ax.add_patch(plt.Rectangle((0.44, 0.28), 0.14, 0.11, facecolor="#fce4d6", edgecolor="#c65911"))
    ax.text(0.51, 0.335, "$D_c$\ndecoder", ha="center", va="center", fontsize=8)
    ax.annotate("", xy=(0.385, 0.39), xytext=(0.545, 0.48),
                arrowprops={"arrowstyle": "->", "lw": 1.2})
    ax.text(0.47, 0.452, "ReLU", ha="center", va="center", fontsize=6, color="#555555")
    ax.annotate("", xy=(0.44, 0.335), xytext=(0.40, 0.39), arrowprops={"arrowstyle": "->", "lw": 1.2})
    ax.annotate("", xy=(0.27, 0.39), xytext=(0.26, 0.48), arrowprops={"arrowstyle": "->", "lw": 1.2})
    ax.text(0.245, 0.437, "ReLU", ha="right", va="center", fontsize=6, color="#555555")
    ax.add_patch(plt.Rectangle((0.05, 0.25), 0.13, 0.11, facecolor="#e6f2e6", edgecolor="#38761d"))
    ax.text(0.115, 0.305, "$x \\leftarrow$ LN\n$(x{+}$LN$(\\cdot))$", ha="center", va="center", fontsize=6.5)
    # Write-back from the decoder, routed below the boxes (the old u(x)v -> box
    # arrow bypassed D_c; the old E_v -> D_c arrow pointed at the wrong target).
    ax.plot([0.51, 0.51, 0.115], [0.28, 0.235, 0.235], color="#333333", lw=1.2)
    ax.annotate("", xy=(0.115, 0.25), xytext=(0.115, 0.235),
                arrowprops={"arrowstyle": "->", "lw": 1.2, "color": "#333333"})
    ax.annotate("", xy=(0.115, 0.48), xytext=(0.115, 0.36), arrowprops={"arrowstyle": "->", "lw": 1.2})
    ax.text(0.34, 0.71, "all levels reuse the same $(E,E_v,D_c)$", ha="center", va="center", fontsize=8, color="#444444")

    # Growth and routing panel.
    ax.add_patch(plt.Rectangle((0.70, 0.20), 0.27, 0.62, fill=False, linewidth=1.8, edgecolor="#333333"))
    ax.text(0.835, 0.78, "append-only growth", ha="center", va="center", fontsize=10, weight="bold")
    for i, (label, color) in enumerate((("old\nprefix", "#9fc5e8"), ("new\nterritory", "#f6b26b"))):
        y = 0.54 - i * 0.15
        ax.add_patch(plt.Rectangle((0.75, y), 0.16, 0.10, facecolor=color, edgecolor="#555555"))
        ax.text(0.83, y + 0.05, label, ha="center", va="center", fontsize=8)
    ax.text(0.72, 0.70, "append + zero-init\nweights", ha="left", va="center", fontsize=6.5)
    ax.plot([0.72, 0.72], [0.655, 0.44], color="#333333", lw=1.2)
    ax.annotate("", xy=(0.75, 0.44), xytext=(0.72, 0.44),
                arrowprops={"arrowstyle": "->", "lw": 1.2, "color": "#333333"})
    ax.add_patch(plt.Rectangle((0.75, 0.26), 0.16, 0.08, facecolor="#eee6f5", edgecolor="#674ea7"))
    ax.text(0.83, 0.30, "route mask\nold prefix / full", ha="center", va="center", fontsize=7)
    ax.annotate("", xy=(0.91, 0.59), xytext=(0.923, 0.59), arrowprops={"arrowstyle": "->", "lw": 1.0})
    ax.text(0.928, 0.59, "old path\nfrozen", ha="left", va="center", fontsize=6.5, color="#38761d")
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
    ood_summary = make_ood_scatter_figure(data_dir, figures_dir / "f4_ood_scatter.pdf")
    decay_summary = make_decay_figure(data_dir, figures_dir / "decay_regimes.pdf")
    xscript_summary = make_cross_script_figure(data_dir, figures_dir / "f5_cross_script.pdf")
    manifest = {
        "domain_order": DOMAIN_ORDER,
        "retention_summary": retention_summary,
        "expansion_summary": expansion_summary,
        "ood_summary": ood_summary,
        "decay_summary": decay_summary,
        "cross_script_summary": xscript_summary,
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
