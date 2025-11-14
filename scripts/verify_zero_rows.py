from __future__ import annotations

import argparse
from pathlib import Path

from bdexports.cleaning import verify_zero_values
from bdexports.config import VerificationConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify rows with 0 USD values in the cleaned CSV.")
    parser.add_argument(
        "--original-csv",
        default="data/monthly_export_data.csv",
        help="Original monthly_export_data CSV (default: data/monthly_export_data.csv).",
    )
    parser.add_argument(
        "--cleaned-csv",
        default="data/monthly_export_data_cleaned.csv",
        help="Cleaned CSV file (default: data/monthly_export_data_cleaned.csv).",
    )
    parser.add_argument(
        "--report",
        default="data/verification_results.csv",
        help="Verification report path (default: data/verification_results.csv).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = VerificationConfig(
        original_csv=Path(args.original_csv),
        cleaned_csv=Path(args.cleaned_csv),
        report_csv=Path(args.report),
    )
    verify_zero_values(config)


if __name__ == "__main__":
    main()
