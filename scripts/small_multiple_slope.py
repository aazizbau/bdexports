from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
import numpy as np
import pandas as pd

SECTION_MAP = {
    "Textiles": [str(i).zfill(2) for i in range(50, 65)],
    "Fish & Crustaceans": ["03"],
    "Leather": ["41", "42", "43"],
    "Footwear": ["64", "65"],
    "Chemicals": [str(i).zfill(2) for i in range(28, 39)],
    "Metals": [str(i).zfill(2) for i in range(72, 84)],
}


def map_section(hs_code: str) -> str:
    for name, codes in SECTION_MAP.items():
        if hs_code in codes:
            return name
    return "Other"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create small-multiple slope charts for rank shifts across years."
    )
    parser.add_argument(
        "--input-csv",
        default="data/monthly_export_data_cleaned.csv",
        help="Cleaned CSV file (default: data/monthly_export_data_cleaned.csv).",
    )
    parser.add_argument(
        "--output",
        default="output/small_multiple_slope.png",
        help="Destination PNG (default: output/small_multiple_slope.png).",
    )
    parser.add_argument(
        "--dimension",
        choices=["country", "hs_section"],
        default="country",
        help="Display ranks for destinations or HS sections (default: country).",
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2019, 2023],
        help="Two years to compare (default: 2019 2023).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of entities to track (default: 10).",
    )
    parser.add_argument(
        "--annotation",
        default="",
        help="Optional attribution text below the chart.",
    )
    return parser.parse_args()


STYLE = {
    "background": {"figure": "#fbfffd", "axes": "#ffffff"},
    "title": {"size": 20, "color": "#123043", "halo": "#ffffff", "width": 4},
    "body": {"size": 12, "color": "#1e1e1e", "halo": "#f0dac2", "width": 3},
    "annotation": {
        "size": 11,
        "color": "#5f5f5f",
        "halo": "#ffffff",
        "width": 3,
        "position": (0.5, 0.04),
    },
    "line": {"color": "#3587A4"},
}


def halo_text(text_obj, style: dict) -> None:
    if text_obj is None:
        return
    text_obj.set_color(style["color"])
    text_obj.set_fontsize(style["size"])
    text_obj.set_path_effects(
        [pe.withStroke(linewidth=style["width"], foreground=style["halo"])]
    )


def compute_ranks(df: pd.DataFrame, years: list[int], dimension: str, top: int) -> pd.DataFrame:
    subset = df[df["year"].isin(years)].copy()
    if subset.empty:
        raise SystemExit("No data for the selected years.")

    if dimension == "country":
        subset["group"] = subset["country"].fillna("Unknown")
    else:
        subset["group"] = subset["hs_code"].apply(map_section)

    totals = (
        subset.groupby(["group", "year"])["USD"]
        .sum()
        .unstack(fill_value=0)
    )

    rank_frames = []
    for year in years:
        year_totals = totals[year].sort_values(ascending=False)
        selection = year_totals.head(top).index
        ranks = year_totals.rank(ascending=False, method="min")
        rank_frames.append(ranks[selection].to_frame(name=year))

    combined = pd.concat(rank_frames, axis=1).dropna(how="all")
    combined = combined.sort_values(years[0])
    combined = combined.head(top)
    return combined


def main() -> None:
    args = parse_args()
    if len(args.years) != 2:
        raise SystemExit("Please provide exactly two years for comparison.")
    start_year, end_year = sorted(args.years)

    df = pd.read_csv(args.input_csv, dtype={"hs_code": str})
    df["hs_code"] = df["hs_code"].str.strip().str.zfill(2)
    df["month_dt"] = pd.to_datetime(df["month"], format="%B-%Y")
    df["year"] = df["month_dt"].dt.year

    ranks = compute_ranks(df, [start_year, end_year], args.dimension, args.top)
    if ranks.empty:
        raise SystemExit("No ranks computed for the given configuration.")

    n_plots = len(ranks)
    cols = min(3, n_plots)
    rows = (n_plots + cols - 1) // cols

    bg = STYLE["background"]
    fig, axes = plt.subplots(
        rows,
        cols,
        figsize=(cols * 4, rows * 3),
        sharex=True,
        sharey=True,
        facecolor=bg["figure"],
    )
    axes = axes.flatten() if isinstance(axes, (list, tuple, np.ndarray)) else [axes]
    for ax in axes:
        ax.set_facecolor(bg["axes"])

    body_style = STYLE["body"]
    for ax, (group, row) in zip(axes, ranks.iterrows()):
        y_values = [row.get(start_year, float("nan")), row.get(end_year, float("nan"))]
        ax.plot(
            [start_year, end_year],
            y_values,
            marker="o",
            color=STYLE["line"]["color"],
            linewidth=2.5,
        )
        ax.set_title(group, fontsize=body_style["size"] + 2, color=body_style["color"])
        ax.invert_yaxis()
        ax.set_xticks([start_year, end_year])
        ax.set_ylim(0.5, max(y_values) + 0.5)
        for x, y, label in zip([start_year, end_year], y_values, y_values):
            if pd.isna(label):
                continue
            txt = ax.text(x, y, f"{int(label)}", ha="center", va="center")
            halo_text(
                txt,
                {
                    "size": body_style["size"],
                    "color": body_style["color"],
                    "halo": body_style["halo"],
                    "width": body_style["width"],
                },
            )
        ax.tick_params(labelsize=body_style["size"])

    for ax in axes[n_plots:]:
        ax.axis("off")

    fig.suptitle(
        f"{args.dimension.title()} Rank Shifts: {start_year} vs {end_year}",
        fontsize=STYLE["title"]["size"],
        color=STYLE["title"]["color"],
        y=0.98,
        path_effects=[
            pe.withStroke(
                linewidth=STYLE["title"]["width"],
                foreground=STYLE["title"]["halo"],
            )
        ],
    )

    if args.annotation:
        ann = fig.text(
            STYLE["annotation"]["position"][0],
            STYLE["annotation"]["position"][1],
            args.annotation,
            ha="center",
            va="center",
            fontsize=STYLE["annotation"]["size"],
            color=STYLE["annotation"]["color"],
        )
        ann.set_path_effects(
            [
                pe.withStroke(
                    linewidth=STYLE["annotation"]["width"],
                    foreground=STYLE["annotation"]["halo"],
                )
            ]
        )

    for ax in axes:
        ax.set_xlabel("")
        ax.set_ylabel("Rank (1 = highest)")

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"Saved slope chart to {output_path}")


if __name__ == "__main__":
    main()
