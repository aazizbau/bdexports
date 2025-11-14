from __future__ import annotations

import argparse
from pathlib import Path

from bdexports.skipped import copy_skipped_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy skipped Excel files into a failed_files folder.")
    parser.add_argument(
        "--data-dir",
        default="data/product_wise",
        help="Directory that contains the Excel files (default: data/product_wise).",
    )
    parser.add_argument(
        "--skipped-list",
        default="data/failed_files.txt",
        help="Text file listing skipped filenames (default: data/failed_files.txt).",
    )
    parser.add_argument(
        "--failed-dir",
        default="data/failed_files",
        help="Destination directory for the copies (default: data/failed_files).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    copy_skipped_files(
        data_dir=Path(args.data_dir),
        skipped_file=Path(args.skipped_list),
        failed_dir=Path(args.failed_dir),
    )


if __name__ == "__main__":
    main()
