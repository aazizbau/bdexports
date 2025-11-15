from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable

import country_converter as coco
import matplotlib.pyplot as plt
import pandas as pd
import squarify


CCONVERTER = coco.CountryConverter()

CATEGORY_MAP = {
    "agriculture": ((1, 2), (10, 14)),
    "food": ((3, 9),),
    "textiles": ((50, 60),),
    "garments": ((61, 62),),
    "leather": ((41, 43),),
    "footwear": ((64, 67),),
    "chemicals": ((28, 38),),
    "plastics_rubber": ((39, 40),),
    "minerals": ((25, 27),),
    "metals": ((72, 83),),
    "machinery": ((84, 85),),
    "pharmaceuticals": ((30, 30),),
}


def category_help() -> str:
    lines = []
    for name, ranges in CATEGORY_MAP.items():
        label = ", ".join(
            f"HS {start:02d}-{end:02d}" if start != end else f"HS {start:02d}"
            for start, end in ranges
        )
        lines.append(f"{name}: {label}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a regional share treemap for broad HS categories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=category_help(),
    )
    parser.add_argument(
        "--input-csv",
        default="data/monthly_export_data_cleaned.csv",
        help="Cleaned CSV file (default: data/monthly_export_data_cleaned.csv).",
    )
    parser.add_argument(
        "--output",
        help="Destination PNG (default: output/regional_treemap_<category>.png).",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2023,
        help="Calendar year to aggregate (default: 2023).",
    )
    parser.add_argument(
        "--category",
        default="food",
        choices=sorted(CATEGORY_MAP.keys()),
        help="Broader HS category to aggregate (default: food).",
    )
    parser.add_argument(
        "--region-scope",
        choices=["continent", "geopolitical"],
        default="continent",
        help="Use built-in continent or geopolitical groupings (default: continent).",
    )
    parser.add_argument(
        "--region-map",
        help="Optional CSV mapping with columns country,region to override built-in mappings.",
    )
    parser.add_argument(
        "--title",
        help="Treemap title (defaults to '<Category> (HS ranges) Export by Region').",
    )
    return parser.parse_args()


def expand_codes(ranges: Iterable[tuple[int, int]]) -> set[str]:
    codes: set[str] = set()
    for start, end in ranges:
        for hs in range(start, end + 1):
            codes.add(f"{hs:02d}")
    return codes

# Hard-coded geopolitical regions for quick reference.
DEFAULT_GEO_MAP: Dict[str, str] = {}


def load_region_map(path: str | None, scope: str = "continent") -> Dict[str, str] | None:
    if path:
        return _load_csv_map(Path(path))
    if scope == "continent":
        csv_path = Path("data/regions.csv")
        if csv_path.exists():
            try:
                return _load_csv_map(csv_path)
            except Exception as exc:
                print(f"Warning: failed to read {csv_path}: {exc}. Falling back to automatic mapping.")
        return None
    return None


def _load_csv_map(csv_path: Path) -> Dict[str, str]:
    df = pd.read_csv(csv_path)
    if not {"country", "region"}.issubset(df.columns):
        raise SystemExit("Region map CSV must contain 'country' and 'region' columns.")
    return dict(zip(df["country"].str.strip(), df["region"].str.strip()))


def main() -> None:
    args = parse_args()
    mapping = load_region_map(args.region_map, args.region_scope)

    df = pd.read_csv(args.input_csv, dtype={"hs_code": str})
    df["hs_code"] = df["hs_code"].str.strip().str.zfill(2)
    df["month_dt"] = pd.to_datetime(df["month"], format="%B-%Y")
    df["year"] = df["month_dt"].dt.year

    hs_codes = expand_codes(CATEGORY_MAP[args.category])
    mask_hs = df["hs_code"].isin(hs_codes)
    mask_year = df["year"] == args.year
    subset = df[mask_hs & mask_year].copy()

    if subset.empty:
        raise SystemExit("No data found for the selected category/year.")

    normalized = subset["country"].replace(
        {
            "Columbia": "Colombia",
            "New Taiwan": "Taiwan",
            "Liberea": "Liberia",
            "Papua New Guine": "Papua New Guinea",
        }
    )

    if args.region_scope == "continent":
        if mapping is None:
            continents = normalized.apply(
                lambda name: CCONVERTER.convert(names=name, to="continent", not_found=None)
            )
            subregions = normalized.apply(
                lambda name: CCONVERTER.convert(names=name, to="UNregion", not_found=None)
            )

            def adjust_region(continent: str, subregion: str) -> str | None:
                if continent in {"Americas", "America"}:
                    if subregion:
                        if "Northern America" in subregion or "North America" in subregion:
                            return "North America"
                        if (
                            "Latin America" in subregion
                            or "Caribbean" in subregion
                            or "South America" in subregion
                        ):
                            return "South America"
                    return "South America"
                return continent

            subset["region"] = [
                adjust_region(cont, sub)
                for cont, sub in zip(continents, subregions)
            ]
        else:
            subset["region"] = subset["country"].map(mapping).fillna("Unknown")
    else:  # geopolitical
        if mapping is None:
            raw_region = normalized.apply(
                lambda name: CCONVERTER.convert(names=name, to="UNregion", not_found="Others")
            )
            subset["region"] = raw_region.map(
                {
                    "Western Asia": "Middle East",
                    "Southern Asia": "South Asia",
                    "Northern Africa": "North Africa",
                    "Eastern Asia": "East Asia",
                    "Central Asia": "Central Asia",
                    "Sub-Saharan Africa": "Sub-Saharan Africa",
                    "Western Europe": "Western Europe",
                    "Southern Europe": "Western Europe",
                    "Northern Europe": "Western Europe",
                    "Eastern Europe": "Western Europe",
                    "Caribbean": "Latin America",
                    "Central America": "Latin America",
                    "South America": "Latin America",
                    "Northern America": "Others",
                }
            ).fillna("Others")
        else:
            subset["region"] = subset["country"].map(mapping).fillna("Others")
    missing_regions = sorted(subset.loc[subset["region"].isna(), "country"].unique())
    if missing_regions:
        msg = ", ".join(missing_regions[:10])
        raise SystemExit(
            f"No region mapping for: {msg}. "
            "Update data/regions.csv or provide --region-map to cover every country."
        )
    regional = subset.groupby("region", as_index=False)["USD"].sum().sort_values("USD", ascending=False)

    colors = plt.cm.Set3(range(len(regional)))
    fig, ax = plt.subplots(figsize=(10, 6))
    squarify.plot(
        sizes=regional["USD"],
        label=[f"{row.region}\n${row.USD/1e6:.1f}M" for row in regional.itertuples()],
        alpha=0.9,
        color=colors,
        ax=ax,
    )
    ranges = CATEGORY_MAP[args.category]
    hs_text = ", ".join(
        f"HS {start:02d}-{end:02d}" if start != end else f"HS {start:02d}"
        for start, end in ranges
    )
    default_title = f"{args.category.replace('_', ' ').title()} ({hs_text}) Export by Region"
    title = args.title or default_title
    ax.set_title(f"{title} ({args.year})")
    ax.axis("off")
    plt.tight_layout()
    output_path = Path(args.output) if args.output else Path("output") / f"regional_treemap_{args.category}_{args.region_scope}_{args.year}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    print(f"Saved treemap to {output_path}")


if __name__ == "__main__":
    main()
