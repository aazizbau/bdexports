from __future__ import annotations

import argparse
from pathlib import Path

from bdexports.config import ExportProcessingConfig
from bdexports.pipeline import process_export_directory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert cumulative Excel files into a monthly CSV.")
    parser.add_argument(
        "--data-dir",
        default="data/product_wise",
        help="Directory containing renamed Excel files (default: data/product_wise).",
    )
    parser.add_argument(
        "--output-csv",
        default="data/monthly_export_data.csv",
        help="Destination CSV path (default: data/monthly_export_data.csv).",
    )
    parser.add_argument(
        "--processed-log",
        default="data/processed_files.txt",
        help="Optional log for successful files (default: data/processed_files.txt).",
    )
    parser.add_argument(
        "--failed-log",
        default="data/failed_files.txt",
        help="Optional log for failures (default: data/failed_files.txt).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = ExportProcessingConfig(
        data_dir=Path(args.data_dir),
        processed_log=Path(args.processed_log) if args.processed_log else None,
        failed_log=Path(args.failed_log) if args.failed_log else None,
    )
    df = process_export_directory(config)
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False)


if __name__ == "__main__":
    main()
