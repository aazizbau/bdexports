from __future__ import annotations

import argparse
from pathlib import Path

from bdexports.config import BarRaceProductConfig
from bdexports.viz.bar_race import create_product_bar_race


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a bar chart race for a specific HS code.")
    parser.add_argument(
        "--input-csv",
        default="data/monthly_export_data_cleaned.csv",
        help="Cleaned CSV file (default: data/monthly_export_data_cleaned.csv).",
    )
    parser.add_argument(
        "--output-video",
        help="Path for the rendered MP4 (default: output/hs<code>_race.mp4).",
    )
    parser.add_argument("--hs-code", required=True, help="HS code to visualise.")
    parser.add_argument("--num-bars", type=int, default=12, help="Number of bars to display.")
    parser.add_argument("--portrait", action=argparse.BooleanOptionalAction, default=False, help="Render a portrait friendly layout.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.output_video:
        output_path = Path(args.output_video)
    else:
        slug = args.hs_code.zfill(2)
        output_path = Path("output") / f"hs{slug}_race.mp4"

    config = BarRaceProductConfig(
        input_csv=Path(args.input_csv),
        output_video=str(output_path),
        hs_code=args.hs_code,
        num_bars=args.num_bars,
        portrait=args.portrait,
    )
    create_product_bar_race(config)


if __name__ == "__main__":
    main()
