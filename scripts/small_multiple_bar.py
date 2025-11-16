from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

from bdexports.constants import HS_CODE_MAP

REGION_GROUPS = {
    "g20": [
        "Argentina",
        "Australia",
        "Brazil",
        "Canada",
        "China",
        "France",
        "Germany",
        "India",
        "Indonesia",
        "Italy",
        "Japan",
        "Mexico",
        "Republic of Korea",
        "Saudi Arabia",
        "South Africa",
        "Turkiye",
        "United Kingdom",
        "United States",
        "European Union",
        "African Union",
    ],
    "oecd": [
        "Australia",
        "Austria",
        "Belgium",
        "Canada",
        "Chile",
        "Colombia",
        "Czech Republic",
        "Denmark",
        "Estonia",
        "Finland",
        "France",
        "Germany",
        "Greece",
        "Hungary",
        "Iceland",
        "Ireland",
        "Israel",
        "Italy",
        "Japan",
        "Republic of Korea",
        "Latvia",
        "Lithuania",
        "Luxembourg",
        "Mexico",
        "Netherlands",
        "New Zealand",
        "Norway",
        "Poland",
        "Portugal",
        "Slovak Republic",
        "Slovenia",
        "Spain",
        "Sweden",
        "Switzerland",
        "Turkiye",
        "United Kingdom",
        "United States",
    ],
    "eu": [
        "Austria",
        "Belgium",
        "Bulgaria",
        "Croatia",
        "Cyprus",
        "Czech Republic",
        "Denmark",
        "Estonia",
        "Finland",
        "France",
        "Germany",
        "Greece",
        "Hungary",
        "Ireland",
        "Italy",
        "Latvia",
        "Lithuania",
        "Luxembourg",
        "Malta",
        "Netherlands",
        "Poland",
        "Portugal",
        "Romania",
        "Slovakia",
        "Slovenia",
        "Spain",
        "Sweden",
    ],
    "asean": [
        "Brunei Darussalam",
        "Cambodia",
        "Indonesia",
        "Laos",
        "Malaysia",
        "Myanmar",
        "Philippines",
        "Singapore",
        "Thailand",
        "Vietnam",
    ],
    "saarc": [
        "Afghanistan",
        "Bangladesh",
        "Bhutan",
        "India",
        "Maldives",
        "Nepal",
        "Pakistan",
        "Sri Lanka",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot small-multiples comparing exports by HS code to each market."
    )
    parser.add_argument(
        "--input-csv",
        default="data/monthly_export_data_cleaned.csv",
        help="Cleaned CSV file (default: data/monthly_export_data_cleaned.csv).",
    )
    parser.add_argument(
        "--output",
        default="output/small_multiple_g20.png",
        help="Destination PNG (default: output/small_multiple_g20.png).",
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2022, 2023],
        help="Years to compare (default: 2022 2023).",
    )
    parser.add_argument(
        "--region",
        choices=sorted(REGION_GROUPS.keys()),
        default="g20",
        help="Market grouping to use (default: g20).",
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        help="Override markets manually (takes precedence over --region).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="Number of HS codes per market (default: 3).",
    )
    return parser.parse_args()


def hs_label(code: str) -> str:
    name = HS_CODE_MAP.get(code, f"HS {code}")
    return f"{name} ({code})"


def main() -> None:
    args = parse_args()
    years = sorted(set(args.years))
    if len(years) < 2:
        raise SystemExit("Please provide at least two years for comparison.")

    df = pd.read_csv(args.input_csv, dtype={"hs_code": str})
    df["hs_code"] = df["hs_code"].str.strip().str.zfill(2)
    df["country"] = df["country"].str.strip()
    df["month_dt"] = pd.to_datetime(df["month"], format="%B-%Y")
    df["year"] = df["month_dt"].dt.year
    subset = df[df["year"].isin(years)]
    if subset.empty:
        raise SystemExit("No data found for the requested years.")

    markets = args.countries if args.countries else REGION_GROUPS[args.region]
    normalized_markets = [
        name.strip().title() if name.lower() != "uk" else "Great Britain"
        for name in markets
    ]

    available_countries = subset["country"].str.title().unique()

    plots: list[tuple[str, pd.DataFrame]] = []
    missing = []

    for country in normalized_markets:
        match = available_countries[available_countries == country]
        if match.size == 0:
            missing.append(country)
            continue
        country_df = subset[subset["country"].str.title() == country]
        if country_df.empty:
            missing.append(country)
            continue
        grouped = (
            country_df.groupby(["hs_code", "year"])["USD"]
            .sum()
            .reset_index()
        )
        totals = grouped.groupby("hs_code")["USD"].sum().sort_values(ascending=False)
        top_codes = totals.head(args.top).index.tolist()
        if not top_codes:
            continue
        pivot = (
            grouped[grouped["hs_code"].isin(top_codes)]
            .pivot(index="hs_code", columns="year", values="USD")
            .reindex(index=top_codes, columns=years, fill_value=0)
        )
        plots.append((country, pivot))

    if not plots:
        missing_str = ", ".join(missing) if missing else "provided selection"
        raise SystemExit(
            f"No markets had matching data. "
            f"The following countries were not found: {missing_str}."
        )

    cols = 4
    rows = math.ceil(len(plots) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 3), sharey=True)
    axes = axes.flatten()

    colors = plt.cm.Set2(range(len(years)))

    for ax in axes[len(plots):]:
        ax.axis("off")

    for ax, (country, pivot) in zip(axes, plots):
        width = 0.35
        x = range(len(pivot.index))
        for idx, year in enumerate(years):
            heights = pivot[year].values
            ax.bar(
                [xi + (idx - (len(years) - 1) / 2) * width for xi in x],
                heights,
                width=width,
                color=colors[idx],
                label=str(year) if country == plots[0][0] else "",
            )
        ax.set_title(country, fontsize=10)
        ax.set_xticks(list(x))
        ax.set_xticklabels(
            [hs_label(code) for code in pivot.index],
            rotation=35,
            ha="right",
            fontsize=7,
        )
        ax.yaxis.set_major_formatter(
            ticker.FuncFormatter(lambda val, _pos: f"{val/1e6:.0f} M")
        )
        if ax in axes[::cols]:
            ax.set_ylabel("USD (Millions)")
        ax.grid(axis="y", linestyle=":", alpha=0.4)

    axes[0].legend(title="Year", fontsize=8)
    if args.countries:
        group_name = ", ".join(normalized_markets)
    else:
        group_name = args.region.upper()
    fig.suptitle(
        f"Top {args.top} HS categories by market ({group_name})\nBangladesh exports ({', '.join(str(y) for y in years)})",
        fontsize=14,
        y=1.02,
    )
    plt.tight_layout()
    default_name = f"small_multiple_{args.region}.png" if not args.countries else "small_multiple_custom.png"
    output_path = Path(args.output if args.output != "output/small_multiple_g20.png" else f"output/{default_name}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    print(f"Saved chart to {output_path}")


if __name__ == "__main__":
    main()
