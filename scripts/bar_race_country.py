from __future__ import annotations

import argparse
from pathlib import Path

from bdexports.config import BarRaceCountryConfig
from bdexports.viz.bar_race import create_country_bar_race


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a bar chart race for a specific destination country.")
    parser.add_argument(
        "--input-csv",
        default="data/monthly_export_data_cleaned.csv",
        help="Cleaned CSV file (default: data/monthly_export_data_cleaned.csv).",
    )
    parser.add_argument(
        "--output-video",
        help="Path for the rendered MP4 (default: output/<country>_race.mp4).",
    )
    parser.add_argument("--country", required=True, help="Country to visualise.")
    parser.add_argument("--num-bars", type=int, default=15, help="Number of bars to display.")
    parser.add_argument("--portrait", action=argparse.BooleanOptionalAction, default=False, help="Render a portrait friendly layout.")
    parser.add_argument("--annotation", help="Custom annotation text.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.output_video:
        output_path = Path(args.output_video)
    else:
        slug = args.country.lower().replace(" ", "_")
        output_path = Path("output") / f"{slug}_race.mp4"

    config = BarRaceCountryConfig(
        input_csv=Path(args.input_csv),
        output_video=str(output_path),
        target_country=args.country,
        num_bars=args.num_bars,
        portrait=args.portrait,
        annotation=args.annotation,
    )
    create_country_bar_race(config)


if __name__ == "__main__":
    main()
