from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence
import warnings

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.colors import is_color_like
import pandas as pd

from bdexports.constants import HS_CODE_MAP


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stacked area chart showing top buyers for a specific HS code over time.")
    parser.add_argument(
        "--input-csv",
        default="data/monthly_export_data_cleaned.csv",
        help="Cleaned CSV file (default: data/monthly_export_data_cleaned.csv).",
    )
    parser.add_argument(
        "--output",
        help="Output PNG path (default: output/top_buyers_hs_<code>.png).",
    )
    parser.add_argument(
        "--hs",
        required=True,
        help="HS code to analyze (e.g., 62).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of top countries to include (default: 5).",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        help="Optional start year filter.",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        help="Optional end year filter.",
    )
    parser.add_argument(
        "--palette",
        nargs="+",
        help="Optional custom colors for the stacked areas (supply at least as many as --top).",
    )
    parser.add_argument(
        "--figsize",
        nargs=2,
        type=float,
        metavar=("WIDTH", "HEIGHT"),
        default=[12.0, 7.0],
        help="Figure size in inches (default: 12 7).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="Output DPI (default: 200).",
    )
    parser.add_argument(
        "--title",
        help="Custom chart title (defaults to HS <code> Top <N> Buyers Over Time).",
    )
    parser.add_argument(
        "--ylabel",
        default="USD (Millions)",
        help="Y-axis label (default: USD (Millions)).",
    )
    parser.add_argument(
        "--legend-loc",
        default="upper left",
        help="Matplotlib legend location (default: upper left).",
    )
    return parser.parse_args()


def filter_by_year(df: pd.DataFrame, start: int | None, end: int | None) -> pd.DataFrame:
    if start:
        df = df[df["year"] >= start]
    if end:
        df = df[df["year"] <= end]
    return df


def _validate_palette(palette: list[str] | None, size: int) -> list[str] | None:
    if not palette:
        return None
    valid = [color for color in palette if is_color_like(color)]
    if not valid:
        warnings.warn("Palette contained no valid color names. Using default colors.")
        return None
    if len(valid) >= size:
        return valid[:size]
    warnings.warn("Not enough colors supplied. Reusing colors cyclically.")
    expanded: list[str] = []
    while len(expanded) < size:
        for color in valid:
            expanded.append(color)
            if len(expanded) == size:
                break
    return expanded


def main() -> None:
    args = parse_args()

    df = pd.read_csv(args.input_csv, dtype={"hs_code": str})
    df["hs_code"] = df["hs_code"].str.strip().str.zfill(2)
    df["month_dt"] = pd.to_datetime(df["month"], format="%B-%Y")
    df["year"] = df["month_dt"].dt.year

    filtered = df[df["hs_code"] == args.hs.zfill(2)]
    filtered = filter_by_year(filtered, args.start_year, args.end_year)

    if filtered.empty:
        raise SystemExit("No rows matched the given filters.")

    country_totals = (
        filtered.groupby("country")["USD"]
        .sum()
        .sort_values(ascending=False)
        .head(args.top)
        .index
    )
    top_countries = filtered[filtered["country"].isin(country_totals)]

    pivot = (
        top_countries.pivot_table(
            index="month_dt",
            columns="country",
            values="USD",
            aggfunc="sum",
        )
        .fillna(0)
        .sort_index()
    )

    output = Path(args.output) if args.output else Path("output") / f"top_buyers_hs_{args.hs}.png"
    output.parent.mkdir(parents=True, exist_ok=True)

    colors = _validate_palette(args.palette, len(pivot.columns)) if args.palette else None

    fig, ax = plt.subplots(figsize=tuple(args.figsize))
    ax.stackplot(pivot.index, pivot.T, labels=pivot.columns, colors=colors)
    product_name = HS_CODE_MAP.get(args.hs.zfill(2), f"HS {args.hs.zfill(2)}")
    title = args.title or f"{product_name} (HS {args.hs.zfill(2)}) Top {args.top} Buyers Over Time"
    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel(args.ylabel)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _pos=None: f"{x/1e6:.1f} M"))
    ax.legend(loc=args.legend_loc)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    plt.tight_layout()
    plt.savefig(output, dpi=args.dpi)
    print(f"Saved chart to {output}")


if __name__ == "__main__":
    main()
