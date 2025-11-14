from __future__ import annotations

import argparse
from pathlib import Path

from bdexports.config import DownloadConfig
from bdexports.downloader import run_download


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download every Excel link from the EPB export page.")
    parser.add_argument("--url", default="https://epb.gov.bd/site/view/epb_export_data/-", help="Export listing page.")
    parser.add_argument("--output-dir", default="data/raw", help="Directory to store downloaded files.")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True, help="Run the browser headless.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = DownloadConfig(
        export_page=args.url,
        output_dir=Path(args.output_dir),
        headless=args.headless,
    )
    run_download(config)


if __name__ == "__main__":
    main()
