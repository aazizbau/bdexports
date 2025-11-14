from __future__ import annotations

import argparse
from pathlib import Path

from bdexports.config import RenameConfig
from bdexports.renamer import process_and_rename


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rename Excel files based on the period specified in their headers.")
    parser.add_argument(
        "--source",
        default="data/product_2digit",
        help="Directory containing the sorted product files (default: data/product_2digit).",
    )
    parser.add_argument(
        "--target",
        default="data/product_wise",
        help="Where the renamed files should be written (default: data/product_wise).",
    )
    parser.add_argument(
        "--archive",
        default="data/product_wise_source",
        help="Directory that stores the original files after renaming (default: data/product_wise_source).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = RenameConfig(
        source_dir=Path(args.source),
        target_dir=Path(args.target),
        archive_dir=Path(args.archive),
    )
    process_and_rename(config)


if __name__ == "__main__":
    main()
