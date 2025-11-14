from __future__ import annotations

import argparse
from pathlib import Path

from bdexports.cleaning import clean_and_combine_countries
from bdexports.config import CountryCleaningConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean the combined monthly export CSV.")
    parser.add_argument(
        "--input-csv",
        default="data/monthly_export_data.csv",
        help="Raw CSV produced by build_monthly_dataset.py (default: data/monthly_export_data.csv).",
    )
    parser.add_argument(
        "--output-csv",
        default="data/monthly_export_data_cleaned.csv",
        help="Destination for the cleaned CSV (default: data/monthly_export_data_cleaned.csv).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = CountryCleaningConfig(
        input_csv=Path(args.input_csv),
        output_csv=Path(args.output_csv),
    )
    clean_and_combine_countries(config)


if __name__ == "__main__":
    main()
