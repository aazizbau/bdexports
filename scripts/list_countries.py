from __future__ import annotations

import argparse
from pathlib import Path

from bdexports.cleaning import create_unique_country_list
from bdexports.config import UniqueCountryConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a sorted list of unique countries from the cleaned CSV.")
    parser.add_argument(
        "--input-csv",
        default="data/monthly_export_data_cleaned.csv",
        help="Cleaned CSV file (default: data/monthly_export_data_cleaned.csv).",
    )
    parser.add_argument(
        "--output-txt",
        default="data/unique_countries.txt",
        help="Destination text file (default: data/unique_countries.txt).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = UniqueCountryConfig(
        input_csv=Path(args.input_csv),
        output_txt=Path(args.output_txt),
    )
    create_unique_country_list(config)


if __name__ == "__main__":
    main()
