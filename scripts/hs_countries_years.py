from __future__ import annotations

import argparse
from itertools import cycle
from pathlib import Path
from typing import Sequence
import warnings

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.colors import is_color_like
import pandas as pd

from bdexports.constants import HS_CODE_MAP


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a static bar chart for a single HS code across selected countries and calendar years."
    )
    parser.add_argument(
        "--input-csv",
        default="data/monthly_export_data_cleaned.csv",
        help="Cleaned monthly export CSV (default: data/monthly_export_data_cleaned.csv).",
    )
    parser.add_argument(
        "--output",
        help="Optional PNG output path. Defaults to output/hs_<code>_<countries>_<years>.png",
    )
    parser.add_argument(
        "--countries",
        "--country",
        nargs="+",
        required=True,
        help="Space separated list of countries (max 10).",
    )
    parser.add_argument(
        "--years",
        "--year",
        nargs="+",
        type=int,
        required=True,
        help="Space separated list of years (max 5, e.g. --years 2018 2022).",
    )
    parser.add_argument(
        "--hs",
        required=True,
        help="HS code to visualise (2 digits).",
    )
    parser.add_argument(
        "--colors",
        "--color",
        nargs="+",
        help='Optional custom colors for the year series (e.g. --colors "tomato" "forestgreen").',
    )
    return parser.parse_args()


def ensure_limits(countries: Sequence[str], years: Sequence[int]) -> None:
    if len(countries) > 10:
        raise SystemExit("Please provide no more than 10 countries.")
    if len(years) > 5:
        raise SystemExit("Please provide no more than 5 years.")


def format_tick(value: float, _pos: int | None = None) -> str:
    return f"{value / 1_000_000:.0f} M"


def select_colors(num_series: int, palette: list[str] | None) -> list[str] | None:
    if not palette:
        return None
    valid = [color for color in palette if is_color_like(color)]
    if not valid:
        warnings.warn("All provided colors were invalid; falling back to default palette.")
        return None
    if len(valid) >= num_series:
        return valid[:num_series]
    return [next_color for _, next_color in zip(range(num_series), cycle(valid))]


def main() -> None:
    args = parse_args()
    ensure_limits(args.countries, args.years)

    data = pd.read_csv(args.input_csv, dtype={"hs_code": str})
    data["hs_code"] = data["hs_code"].str.strip().str.zfill(2)
    data["country"] = data["country"].str.strip()
    data["month_dt"] = pd.to_datetime(data["month"], format="%B-%Y")
    data["year"] = data["month_dt"].dt.year

    hs_code = args.hs.zfill(2)
    filtered = data[
        (data["hs_code"] == hs_code)
        & (data["country"].isin(args.countries))
        & (data["year"].isin(args.years))
    ]

    if filtered.empty:
        raise SystemExit("No rows matched the chosen HS code, countries, or years.")

    summary = (
        filtered.groupby(["country", "year"], as_index=False)["USD"]
        .sum()
        .pivot(index="country", columns="year", values="USD")
        .reindex(args.countries)
        .fillna(0)
    )
    ordered_years = [year for year in args.years if year in summary.columns]
    if not ordered_years:
        raise SystemExit("None of the requested years exist in the dataset.")
    summary = summary.reindex(columns=ordered_years)

    output_path = Path(args.output) if args.output else Path("output") / _default_filename(hs_code, args.countries, ordered_years)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    colors = select_colors(len(ordered_years), args.colors)
    ax = summary.plot(kind="bar", figsize=(12, 7), color=colors)

    product_name = HS_CODE_MAP.get(hs_code, f"HS {hs_code}")
    countries_text = ", ".join(args.countries)
    years_text = ", ".join(str(year) for year in ordered_years)
    ax.set_title(f"{product_name} (HS {hs_code}) Exports to {countries_text} ({years_text})")
    ax.set_xlabel("Country")
    ax.set_ylabel("USD (Millions)")
    ax.legend(title="Year")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_tick))
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    print(f"Saved chart to {output_path}")


def _default_filename(hs_code: str, countries: Sequence[str], years: Sequence[int]) -> str:
    country_slug = "_".join(country.replace(" ", "_") for country in countries)
    year_slug = "_".join(str(year) for year in years)
    return f"hs_{hs_code}_{country_slug}_{year_slug}.png"


if __name__ == "__main__":
    main()
