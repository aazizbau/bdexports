from __future__ import annotations

import argparse
from pathlib import Path

from bdexports.config import SheetFilterConfig
from bdexports.sheet_filters import move_files_with_sheet


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Move Excel files that contain a specific sheet.")
    parser.add_argument(
        "--source",
        default="data/raw",
        help="Directory to scan (default: data/raw).",
    )
    parser.add_argument(
        "--destination",
        default="data/product_2digit",
        help="Where matching files should be moved (default: data/product_2digit).",
    )
    parser.add_argument(
        "--sheet-name",
        default="2 Digit",
        help='Sheet name to search for (case insensitive, default: "2 Digit").',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = SheetFilterConfig(
        source_dir=Path(args.source),
        destination_dir=Path(args.destination),
        sheet_name=args.sheet_name,
    )
    move_files_with_sheet(config)


if __name__ == "__main__":
    main()
