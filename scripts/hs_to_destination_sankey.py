from __future__ import annotations

import argparse
from pathlib import Path as FilePath

import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MplPath
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

SECTION_ORDER = list(SECTION_MAP.keys()) + ["Other"]

LAYOUT_CONFIG = {
    "figure_size": (20, 13),
    "section_x": 0.12,
    "country_x": 0.68,
    "node_width": 0.025,
    "curve_offset": 0.22,
    "section_gap": 0.019,
    "country_gap": 0.02,
    "value_column_x": 0.83,
    "percent_column_x": 0.93,
    "value_column_y_offset": 0.0,
    "percent_column_y_offset": 0.0,
    "header_y": 0.999,
    "title_y": 1.02,
    "title_color": "#1B7066",
    "title_halo_color": "#f5d6ad",
    "annotation_xy": (0.8, 0.10),
    "background_color": "#F7F6F2",
    "axes_background_color": "#ffffff",
    "halo_color": "#cad8d7",
    "grid": {
        "show": True,
        "color": "#EDEFF3",
        "alpha": 0.4,
        "linewidth": 0.6,
        "step": 0.1,
    },
}

SECTION_COLORS = {
    "Textiles": "#f46d43",
    "Fish & Crustaceans": "#fdae61",
    "Leather": "#d53e4f",
    "Footwear": "#547598",
    "Chemicals": "#66c2a5",
    "Metals": "#fee08b",
    "Other": "#bdbdbd",
}

COUNTRY_COLORS = [
    "#607D8B",
    "#00ACC1",
    "#FF7043",
    "#26A69A",
    "#8D6E63",
    "#BA68C8",
    "#4DB6AC",
    "#F06292",
    "#7CB342",
    "#FFD54F",
    "#5C6BC0",
    "#90A4AE",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Sankey diagram from HS sections to top destinations."
    )
    parser.add_argument(
        "--input-csv",
        default="data/monthly_export_data_cleaned.csv",
        help="Cleaned CSV file (default: data/monthly_export_data_cleaned.csv).",
    )
    parser.add_argument(
        "--html",
        default="output/hs_to_destination_sankey.html",
        help="Output HTML file (default: output/hs_to_destination_sankey.html).",
    )
    parser.add_argument(
        "--png",
        default="output/hs_to_destination_sankey.png",
        help="Output PNG file (default: output/hs_to_destination_sankey.png).",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2023,
        help="Calendar year to analyze (default: 2023).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top destinations to include (default: 10).",
    )
    parser.add_argument(
        "--annotation",
        default="",
        help="Optional attribution text shown below the chart (default: empty).",
    )
    return parser.parse_args()


def map_section(hs_code: str) -> str:
    for name, codes in SECTION_MAP.items():
        if hs_code in codes:
            return name
    return "Other"


def compute_positions(
    items: list[str],
    totals: dict[str, float],
    gap: float,
    scale: float,
) -> dict[str, tuple[float, float]]:
    heights = [max(totals.get(item, 0.0) * scale, 0.0) for item in items]
    total_used = sum(heights) + gap * max(len(items) - 1, 0)
    start_y = max(0.0, (1 - total_used) / 2)
    positions: dict[str, tuple[float, float]] = {}
    current = start_y
    for item, height in zip(items, heights):
        positions[item] = (current, height)
        current += height + gap
    return positions


def bezier_path(
    x0: float,
    x1: float,
    y0_top: float,
    y0_bottom: float,
    y1_top: float,
    y1_bottom: float,
    color: str,
    curve_offset: float,
    alpha: float = 0.7,
) -> PathPatch:
    offset = curve_offset
    verts = [
        (x0, y0_bottom),
        (x0 + offset, y0_bottom),
        (x1 - offset, y1_bottom),
        (x1, y1_bottom),
        (x1, y1_top),
        (x1 - offset, y1_top),
        (x0 + offset, y0_top),
        (x0, y0_top),
        (x0, y0_bottom),
    ]
    codes = [
        MplPath.MOVETO,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.LINETO,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CLOSEPOLY,
    ]
    path = MplPath(verts, codes)
    return PathPatch(path, facecolor=color, edgecolor="none", alpha=alpha)


def halo_text(
    ax: plt.Axes,
    x: float,
    y: float,
    text: str,
    *,
    ha: str,
    va: str,
    fontsize: int,
    color: str,
    weight: str | None = None,
    alpha: float | None = None,
) -> None:
    halo = pe.withStroke(
        linewidth=5, foreground=LAYOUT_CONFIG.get("halo_color", "#ffffff")
    )
    ax.text(
        x,
        y,
        text,
        ha=ha,
        va=va,
        fontsize=fontsize,
        color=color,
        weight=weight,
        alpha=alpha,
        path_effects=[halo],
    )


def halo_fig_text(
    fig: plt.Figure,
    x: float,
    y: float,
    text: str,
    *,
    ha: str,
    va: str,
    fontsize: int,
    color: str,
) -> None:
    halo = pe.withStroke(
        linewidth=5, foreground=LAYOUT_CONFIG.get("halo_color", "#ffffff")
    )
    fig.text(
        x,
        y,
        text,
        ha=ha,
        va=va,
        fontsize=fontsize,
        color=color,
        path_effects=[halo],
    )


def main() -> None:
    args = parse_args()

    df = pd.read_csv(args.input_csv, dtype={"hs_code": str})
    df["hs_code"] = df["hs_code"].str.strip().str.zfill(2)
    df["month_dt"] = pd.to_datetime(df["month"], format="%B-%Y")
    df["year"] = df["month_dt"].dt.year

    year_df = df[df["year"] == args.year].copy()
    if year_df.empty:
        raise SystemExit("No data for the selected year.")

    year_total_usd = year_df["USD"].sum()

    year_df["section"] = year_df["hs_code"].apply(map_section)
    grouped = (
        year_df.groupby(["section", "country"])["USD"].sum().reset_index()
    )

    country_totals = (
        grouped.groupby("country")["USD"]
        .sum()
        .sort_values(ascending=False)
    )
    top_countries = country_totals.head(args.top).index.tolist()

    filtered = grouped[grouped["country"].isin(top_countries)].copy()
    sections = filtered["section"].dropna().unique().tolist()
    section_rank = {name: idx for idx, name in enumerate(SECTION_ORDER)}
    sections.sort(key=lambda name: section_rank.get(name, len(section_rank)))
    countries = sorted(
        top_countries, key=lambda c: country_totals.get(c, 0.0), reverse=True
    )

    section_totals = (
        filtered.groupby("section")["USD"].sum().reindex(sections, fill_value=0.0)
    )
    total_value = section_totals.sum()
    if total_value <= 0:
        raise SystemExit("Total exports for the selected year are zero.")

    section_gap_total = LAYOUT_CONFIG["section_gap"] * max(len(sections) - 1, 0)
    country_gap_total = LAYOUT_CONFIG["country_gap"] * max(len(countries) - 1, 0)
    available_left = 1 - section_gap_total
    available_right = 1 - country_gap_total
    value_scale = min(available_left, available_right) / total_value

    section_positions = compute_positions(
        sections, section_totals.to_dict(), LAYOUT_CONFIG["section_gap"], value_scale
    )
    country_positions = compute_positions(
        countries,
        country_totals.to_dict(),
        LAYOUT_CONFIG["country_gap"],
        value_scale,
    )

    fig, ax = plt.subplots(
        figsize=LAYOUT_CONFIG["figure_size"],
        facecolor=LAYOUT_CONFIG.get("background_color", "white"),
    )
    ax.set_facecolor(LAYOUT_CONFIG.get("axes_background_color", "white"))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    grid_cfg = LAYOUT_CONFIG.get("grid", {})
    if grid_cfg.get("show"):
        step = max(grid_cfg.get("step", 0.1), 0.02)
        xs = np.arange(0, 1 + step, step)
        for x in xs:
            ax.axvline(
                x,
                color=grid_cfg.get("color", "#d0d0d0"),
                linewidth=grid_cfg.get("linewidth", 0.5),
                alpha=grid_cfg.get("alpha", 0.3),
                zorder=0,
            )
        ys = np.arange(0, 1 + step, step)
        for y in ys:
            ax.axhline(
                y,
                color=grid_cfg.get("color", "#d0d0d0"),
                linewidth=grid_cfg.get("linewidth", 0.5),
                alpha=grid_cfg.get("alpha", 0.3),
                zorder=0,
            )
    ax.axis("off")

    section_cursors = {sec: section_positions[sec][0] for sec in sections}
    country_cursors = {cty: country_positions[cty][0] for cty in countries}

    node_width = LAYOUT_CONFIG["node_width"]
    curve_offset = LAYOUT_CONFIG["curve_offset"]

    for section in sections:
        bottom, height = section_positions[section]
        ax.add_patch(
            Rectangle(
                (LAYOUT_CONFIG["section_x"] - node_width, bottom),
                node_width,
                height,
                color=SECTION_COLORS.get(section, "#999999"),
                zorder=2,
            )
        )
        halo_text(
            ax,
            LAYOUT_CONFIG["section_x"] - node_width - 0.01,
            bottom + height / 2,
            section,
            va="center",
            ha="right",
            fontsize=14,
            color="#2b2b2b",
        )

    for idx, country in enumerate(countries):
        bottom, height = country_positions[country]
        color = COUNTRY_COLORS[idx % len(COUNTRY_COLORS)]
        ax.add_patch(
            Rectangle(
                (LAYOUT_CONFIG["country_x"], bottom),
                node_width,
                height,
                color=color,
                zorder=2,
            )
        )
        halo_text(
            ax,
            LAYOUT_CONFIG["country_x"] + node_width + 0.01,
            bottom + height / 2,
            country,
            va="center",
            ha="left",
            fontsize=14,
            color="#2b2b2b",
        )

    for _, row in filtered.sort_values("USD", ascending=False).iterrows():
        section = row["section"]
        country = row["country"]
        value = row["USD"]
        if value <= 0:
            continue
        height = value * value_scale
        src_bottom = section_cursors[section]
        src_top = src_bottom + height
        section_cursors[section] += height

        dst_bottom = country_cursors[country]
        dst_top = dst_bottom + height
        country_cursors[country] += height

        color = SECTION_COLORS.get(section, "#bdbdbd")
        patch = bezier_path(
            LAYOUT_CONFIG["section_x"],
            LAYOUT_CONFIG["country_x"],
            src_top,
            src_bottom,
            dst_top,
            dst_bottom,
            color=color,
            curve_offset=curve_offset,
        )
        ax.add_patch(patch)

    value_col_x = LAYOUT_CONFIG["value_column_x"]
    percent_col_x = LAYOUT_CONFIG["percent_column_x"]
    value_y_offset = LAYOUT_CONFIG["value_column_y_offset"]
    percent_y_offset = LAYOUT_CONFIG["percent_column_y_offset"]

    for idx, country in enumerate(countries):
        bottom, height = country_positions[country]
        center_y = bottom + height / 2
        value_text = f"{country_totals.get(country, 0.0) / 1e6:,.1f} M"
        percent = (
            (country_totals.get(country, 0.0) / year_total_usd) * 100
            if year_total_usd
            else 0.0
        )
        percent_text = f"{percent:.0f} %"
        halo_text(
            ax,
            value_col_x,
            center_y + value_y_offset,
            value_text,
            ha="left",
            va="center",
            fontsize=14,
            color="#424242",
        )
        halo_text(
            ax,
            percent_col_x,
            center_y + percent_y_offset,
            percent_text,
            ha="left",
            va="center",
            fontsize=14,
            color="#424242",
        )

    halo_text(
        ax,
        value_col_x,
        LAYOUT_CONFIG["header_y"],
        "Millions (USD)",
        fontsize=15,
        ha="left",
        va="bottom",
        color="#424242",
    )
    halo_text(
        ax,
        percent_col_x,
        LAYOUT_CONFIG["header_y"],
        "Percentage",
        fontsize=15,
        ha="left",
        va="bottom",
        color="#424242",
    )

    title = ax.set_title(
        f"Bangladesh Exports to Top {args.top} Destinations ({args.year})",
        fontsize=20,
        y=LAYOUT_CONFIG["title_y"],
        color=LAYOUT_CONFIG.get("title_color", "#1e3350"),
    )
    title.set_path_effects(
        [
            pe.withStroke(
                linewidth=LAYOUT_CONFIG.get("title_halo_width", 4),
                foreground=LAYOUT_CONFIG.get("title_halo_color", "#ffffff"),
            )
        ]
    )

    if args.annotation:
        ann_x, ann_y = LAYOUT_CONFIG["annotation_xy"]
        halo_fig_text(
            fig,
            ann_x,
            ann_y,
            args.annotation,
            ha="center",
            va="center",
            fontsize=12,
            color="#6d6d6d",
        )

    output_dir = FilePath(args.png).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = FilePath(args.png).with_name(
        f"{FilePath(args.png).stem}_{args.year}_{args.top}{FilePath(args.png).suffix}"
    )
    fig.savefig(png_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    html_path = FilePath(args.html).with_name(
        f"{FilePath(args.html).stem}_{args.year}_{args.top}{FilePath(args.html).suffix}"
    )
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Sankey Diagram</title>
</head>
<body style="font-family: Arial, sans-serif;">
  <img src="{png_path.name}" alt="Sankey diagram" style="max-width: 100%;">
</body>
</html>
"""
    html_path.write_text(html_content, encoding="utf-8")

    print(f"Saved Sankey diagram to {png_path} and {html_path}")


if __name__ == "__main__":
    main()
