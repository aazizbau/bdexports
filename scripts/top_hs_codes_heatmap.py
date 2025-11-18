from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
import numpy as np
import pandas as pd
import seaborn as sns

from bdexports.constants import HS_CODE_MAP


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot a heatmap of top HS codes vs. years."
    )
    parser.add_argument(
        "--input-csv",
        default="data/monthly_export_data_cleaned.csv",
        help="Cleaned CSV file (default: data/monthly_export_data_cleaned.csv).",
    )
    parser.add_argument(
        "--output",
        default="output/top_hs_codes_heatmap.png",
        help="Destination PNG (default: output/top_hs_codes_heatmap.png).",
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=list(range(2018, 2025)),
        help="Years to include (default: 2018-2024).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=15,
        help="Number of HS codes to show (default: 15).",
    )
    parser.add_argument(
        "--scale",
        choices=["log", "value"],
        default="log",
        help="Use logarithmic (log10) or raw values (default: log).",
    )
    parser.add_argument(
        "--palette",
        default="YlGnBu",
        help=(
            "Matplotlib/Seaborn colormap (default: YlGnBu). "
            "Examples: viridis, plasma, inferno, magma_r, rocket, Blues, Greens."
        ),
    )
    parser.add_argument(
        "--annotation",
        default="",
        help="Optional attribution text shown below the heatmap (default: empty).",
    )
    return parser.parse_args()


TEXT_CONFIG = {
    "title": {"size": 20, "color": "#1b3a4b", "halo_color": "#bde5f9", "halo_width": 4},
    "body": {"size": 12, "color": "#1f1f1f", "halo_color": "#f0cdb7", "halo_width": 3},
    "annotation": {
        "size": 11,
        "color": "#5f5f5f",
        "halo_color": "#ffffff",
        "halo_width": 3,
        "position": (0.8, 0.02),
    },
    "background": {"figure": "#fbfffd", "axes": "#ffffff"},
}


def format_label(code: str) -> str:
    name = HS_CODE_MAP.get(code, f"HS {code}")
    return f"{name} ({code})"


def apply_halo(text_obj, *, color: str, size: int, halo_color: str, halo_width: int) -> None:
    if text_obj is None:
        return
    text_obj.set_color(color)
    text_obj.set_fontsize(size)
    text_obj.set_path_effects(
        [pe.withStroke(linewidth=halo_width, foreground=halo_color)]
    )


def main() -> None:
    args = parse_args()
    years = sorted(set(args.years))

    df = pd.read_csv(args.input_csv, dtype={"hs_code": str})
    df["hs_code"] = df["hs_code"].str.strip().str.zfill(2)
    df["month_dt"] = pd.to_datetime(df["month"], format="%B-%Y")
    df["year"] = df["month_dt"].dt.year
    subset = df[df["year"].isin(years)]

    if subset.empty:
        raise SystemExit("No data found for the selected years.")

    totals = subset.groupby("hs_code")["USD"].sum().sort_values(ascending=False)
    top_codes = totals.head(args.top).index.tolist()
    if not top_codes:
        raise SystemExit("No HS codes found.")

    pivot = (
        subset[subset["hs_code"].isin(top_codes)]
        .groupby(["hs_code", "year"])["USD"]
        .sum()
        .unstack(fill_value=0)
        .reindex(index=top_codes, columns=years, fill_value=0)
    )

    data = pivot.replace(0, np.nan)
    if args.scale == "log":
        data_values = np.log10(data)
        cbar_label = "log10(USD)"
    else:
        data_values = data / 1e6
        cbar_label = "USD (Millions)"

    bg_cfg = TEXT_CONFIG["background"]
    fig, ax = plt.subplots(
        figsize=(12, 8), facecolor=bg_cfg.get("figure", "#ffffff")
    )
    ax.set_facecolor(bg_cfg.get("axes", "#ffffff"))
    heatmap_ax = sns.heatmap(
        data_values,
        ax=ax,
        cmap=args.palette,
        linewidths=0.3,
        linecolor="gray",
        cbar_kws={"label": cbar_label},
        mask=data_values.isna(),
    )
    y_labels = ax.set_yticklabels([format_label(code) for code in pivot.index], rotation=0)
    x_labels = ax.set_xticklabels(years, rotation=0)

    body_cfg = TEXT_CONFIG["body"]
    for label in list(y_labels) + list(x_labels):
        apply_halo(
            label,
            color=body_cfg["color"],
            size=body_cfg["size"],
            halo_color=body_cfg["halo_color"],
            halo_width=body_cfg["halo_width"],
        )

    ylabel = ax.set_ylabel("Products with HS code")
    apply_halo(
        ylabel,
        color=body_cfg["color"],
        size=body_cfg["size"] + 1,
        halo_color=body_cfg["halo_color"],
        halo_width=body_cfg["halo_width"],
    )
    xlabel = ax.set_xlabel("Year")
    apply_halo(
        xlabel,
        color=body_cfg["color"],
        size=body_cfg["size"] + 1,
        halo_color=body_cfg["halo_color"],
        halo_width=body_cfg["halo_width"],
    )

    title_cfg = TEXT_CONFIG["title"]
    title = ax.set_title(f"Top {args.top} Exports across Years")
    apply_halo(
        title,
        color=title_cfg["color"],
        size=title_cfg["size"],
        halo_color=title_cfg["halo_color"],
        halo_width=title_cfg["halo_width"],
    )

    if heatmap_ax.collections:
        cbar = heatmap_ax.collections[0].colorbar
        if cbar:
            cbar_label = cbar.ax.yaxis.label
            apply_halo(
                cbar_label,
                color=body_cfg["color"],
                size=body_cfg["size"],
                halo_color=body_cfg["halo_color"],
                halo_width=body_cfg["halo_width"],
            )
            for tick_label in cbar.ax.get_yticklabels():
                apply_halo(
                    tick_label,
                    color=body_cfg["color"],
                    size=body_cfg["size"],
                    halo_color=body_cfg["halo_color"],
                    halo_width=body_cfg["halo_width"],
                )

    if args.annotation:
        ann_cfg = TEXT_CONFIG["annotation"]
        ann = fig.text(
            ann_cfg["position"][0],
            ann_cfg["position"][1],
            args.annotation,
            ha="center",
            va="center",
        )
        apply_halo(
            ann,
            color=ann_cfg["color"],
            size=ann_cfg["size"],
            halo_color=ann_cfg["halo_color"],
            halo_width=ann_cfg["halo_width"],
        )

    plt.tight_layout()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    print(f"Saved chart to {output_path}")


if __name__ == "__main__":
    main()
