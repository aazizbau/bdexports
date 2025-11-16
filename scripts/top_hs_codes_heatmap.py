from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
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
    return parser.parse_args()


def format_label(code: str) -> str:
    name = HS_CODE_MAP.get(code, f"HS {code}")
    return f"{name} ({code})"


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

    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(
        data_values,
        ax=ax,
        cmap=args.palette,
        linewidths=0.3,
        linecolor="gray",
        cbar_kws={"label": cbar_label},
        mask=data_values.isna(),
    )
    ax.set_yticklabels([format_label(code) for code in pivot.index], rotation=0)
    ax.set_xticklabels(years, rotation=0)
    ax.set_ylabel("Products with HS code")
    ax.set_title(f"Top {args.top} Exports vs Years")
    plt.tight_layout()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    print(f"Saved chart to {output_path}")


if __name__ == "__main__":
    main()
