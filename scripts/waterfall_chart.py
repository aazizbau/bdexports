from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
import pandas as pd

from bdexports.constants import HS_CODE_MAP


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a waterfall chart showing contributions to annual export growth "
            "by HS section or destination."
        )
    )
    parser.add_argument(
        "--input-csv",
        default="data/monthly_export_data_cleaned.csv",
        help="Cleaned CSV file (default: data/monthly_export_data_cleaned.csv).",
    )
    parser.add_argument(
        "--output",
        default="output/waterfall_chart.png",
        help="Destination PNG (default: output/waterfall_chart.png).",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2022,
        help="Baseline year (default: 2022).",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2023,
        help="Comparison year (default: 2023).",
    )
    parser.add_argument(
        "--dimension",
        choices=["section", "country"],
        default="section",
        help="Break contributions by HS section or destination country (default: section).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of contributors to display (default: 10). Remaining contributors are grouped as 'Other'.",
    )
    parser.add_argument(
        "--annotation",
        default="",
        help="Optional attribution text displayed below the chart.",
    )
    return parser.parse_args()


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


def apply_halo(text, *, size: int, color: str, halo_color: str, halo_width: int) -> None:
    if text is None:
        return
    text.set_fontsize(size)
    text.set_color(color)
    text.set_path_effects(
        [pe.withStroke(linewidth=halo_width, foreground=halo_color)]
    )


def build_contributions(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
    dimension: str,
    top_n: int,
) -> pd.DataFrame:
    if dimension == "section":
        df["group"] = df["hs_code"].apply(map_section)
    else:
        df["group"] = df["country"].fillna("Unknown")

    yearly = (
        df[df["year"].isin([start_year, end_year])]
        .groupby(["group", "year"])["USD"]
        .sum()
        .unstack(fill_value=0.0)
    )

    if start_year not in yearly.columns or end_year not in yearly.columns:
        raise SystemExit("Selected years are not available in the dataset.")

    yearly["delta"] = yearly[end_year] - yearly[start_year]
    yearly = yearly.sort_values("delta", key=lambda s: s.abs(), ascending=False)

    top = yearly.head(top_n)
    remainder = yearly.iloc[top_n:]
    if not remainder.empty:
        other = remainder.sum().to_frame().T
        other.index = ["Other"]
        top = pd.concat([top, other], axis=0)

    total_start = yearly[start_year].sum()
    total_end = yearly[end_year].sum()
    total_delta = total_end - total_start

    chart_data = top.reset_index()
    chart_data["running_start"] = total_start
    chart_data["running_end"] = 0.0

    running = total_start
    starts = []
    for delta in chart_data["delta"]:
        starts.append(running)
        running += delta
    chart_data["running_start"] = starts
    chart_data["running_end"] = chart_data["running_start"] + chart_data["delta"]

    chart_data = pd.concat(
        [
            pd.DataFrame(
                {
                    "group": [f"{start_year} total"],
                    "delta": [total_start],
                    "running_start": [0.0],
                    "running_end": [total_start],
                    "type": ["total"],
                }
            ),
            chart_data.assign(type="delta"),
            pd.DataFrame(
                {
                    "group": [f"{end_year} total"],
                    "delta": [total_end],
                    "running_start": [0.0],
                    "running_end": [total_end],
                    "type": ["total"],
                }
            ),
        ],
        ignore_index=True,
    )

    return chart_data, total_delta


def main() -> None:
    args = parse_args()

    df = pd.read_csv(args.input_csv, dtype={"hs_code": str})
    df["hs_code"] = df["hs_code"].str.strip().str.zfill(2)
    df["month_dt"] = pd.to_datetime(df["month"], format="%B-%Y")
    df["year"] = df["month_dt"].dt.year

    chart_data, total_delta = build_contributions(
        df,
        start_year=args.start_year,
        end_year=args.end_year,
        dimension=args.dimension,
        top_n=args.top,
    )

    bg_cfg = TEXT_CONFIG["background"]
    fig, ax = plt.subplots(
        figsize=(14, 8), facecolor=bg_cfg.get("figure", "#ffffff")
    )
    ax.set_facecolor(bg_cfg.get("axes", "#ffffff"))
    colors = []
    for _, row in chart_data.iterrows():
        if row["type"] == "total":
            colors.append("#4a6572")
        elif row["delta"] >= 0:
            colors.append("#2ca25f")
        else:
            colors.append("#de425b")

    bars = ax.bar(
        chart_data["group"],
        chart_data["delta"] / 1e6,
        bottom=chart_data["running_start"] / 1e6,
        color=colors,
    )

    body_cfg = TEXT_CONFIG["body"]
    for rect, (_, row) in zip(bars, chart_data.iterrows()):
        height = rect.get_height()
        ypos = rect.get_y() + height / 2
        label = f"{row['delta'] / 1e6:,.1f} M"
        text = ax.text(
            rect.get_x() + rect.get_width() / 2,
            ypos,
            label,
            ha="center",
            va="center",
        )
        apply_halo(
            text,
            size=body_cfg["size"],
            color=body_cfg["color"],
            halo_color=body_cfg["halo_color"],
            halo_width=body_cfg["halo_width"],
        )

    ylabel = ax.set_ylabel("USD (Millions)")
    apply_halo(
        ylabel,
        size=body_cfg["size"] + 1,
        color=body_cfg["color"],
        halo_color=body_cfg["halo_color"],
        halo_width=body_cfg["halo_width"],
    )
    for label in ax.get_yticklabels():
        apply_halo(
            label,
            size=body_cfg["size"],
            color=body_cfg["color"],
            halo_color=body_cfg["halo_color"],
            halo_width=body_cfg["halo_width"],
        )
    tick_positions = range(len(chart_data))
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(chart_data["group"], rotation=45, ha="right")
    for label in ax.get_xticklabels():
        apply_halo(
            label,
            size=body_cfg["size"],
            color=body_cfg["color"],
            halo_color=body_cfg["halo_color"],
            halo_width=body_cfg["halo_width"],
        )

    title_cfg = TEXT_CONFIG["title"]
    title = ax.set_title(
        f"Export Growth {args.start_year}→{args.end_year} "
        f"({args.dimension.title()} contributions)",
        pad=20,
    )
    apply_halo(
        title,
        size=title_cfg["size"],
        color=title_cfg["color"],
        halo_color=title_cfg["halo_color"],
        halo_width=title_cfg["halo_width"],
    )

    ax.axhline(
        chart_data.loc[chart_data["type"] == "total", "running_end"].iloc[0] / 1e6,
        color="#4a6572",
        linewidth=1.2,
        linestyle="--",
        alpha=0.6,
    )
    ax.axhline(
        chart_data.loc[chart_data["type"] == "total", "running_end"].iloc[-1] / 1e6,
        color="#4a6572",
        linewidth=1.2,
        linestyle="--",
        alpha=0.6,
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
            size=ann_cfg["size"],
            color=ann_cfg["color"],
            halo_color=ann_cfg["halo_color"],
            halo_width=ann_cfg["halo_width"],
        )

    plt.tight_layout()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"Saved waterfall chart to {output_path}")


if __name__ == "__main__":
    main()
