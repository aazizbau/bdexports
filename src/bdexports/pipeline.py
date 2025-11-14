from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from .config import ExportProcessingConfig

MONTH_MAP = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def _parse_filename(filename: str) -> tuple[int, pd.Timestamp] | None:
    match_range = re.search(r"_Jul_([A-Za-z]+)_(\d{4})_(\d{4})", filename)
    match_single_range = re.search(r"_Jul_([A-Za-z]+)_(\d{4})", filename)
    match_single = re.search(r"_Jul_(\d{4})", filename)

    if match_range:
        end_month = match_range.group(1).title()
        start_year = int(match_range.group(3))
    elif match_single_range:
        end_month = match_single_range.group(1).title()
        start_year = int(match_single_range.group(2))
    elif match_single:
        end_month = "Jul"
        start_year = int(match_single.group(1))
    else:
        return None

    month_number = MONTH_MAP.get(end_month)
    if not month_number:
        return None

    calendar_year = start_year if month_number >= 7 else start_year + 1
    end_date = pd.Timestamp(calendar_year, month_number, 1)
    return start_year, end_date


def _read_product_sheet(path: Path) -> pd.DataFrame | str:
    try:
        with pd.ExcelFile(path) as workbook:
            if "2 Digit" not in workbook.sheet_names:
                return "Sheet '2 Digit' not found"
    except Exception as exc:
        return f"Failed to read workbook: {exc}"

    df = pd.read_excel(path, sheet_name="2 Digit", header=None)
    extracted: list[dict[str, object]] = []
    current_hs = None

    for _, row in df.iterrows():
        row_list = row.tolist()
        for cell in row_list[:3]:
            match = re.match(r"^(\d{2}):", str(cell).strip())
            if match:
                current_hs = match.group(1)
                break
        else:
            if not current_hs:
                continue

            country_match = None
            for cell in row_list[:3]:
                match = re.search(r"([A-Z]{2}):\s?([\w\s.&,'-]+)", str(cell).strip())
                if match:
                    country_match = match
                    break

            if not country_match:
                continue

            value = None
            for cell in reversed(row_list):
                if pd.api.types.is_number(cell) and pd.notna(cell):
                    value = cell
                    break

            if value is not None:
                extracted.append(
                    {
                        "hs_code": current_hs,
                        "country": country_match.group(2).strip(),
                        "usd_cumulative": float(value),
                    }
                )

    if not extracted:
        return "No HS/country rows found"

    return pd.DataFrame(extracted)


def process_export_directory(config: ExportProcessingConfig) -> pd.DataFrame:
    """
    Parse every Excel file inside ``config.data_dir`` and convert cumulative values into monthly USD figures.
    """

    data_dir = Path(config.data_dir)
    files = [path for path in data_dir.glob("*") if path.suffix.lower() in {".xls", ".xlsx"}]

    processed_log = config.processed_log or data_dir / "processed_files.txt"
    failed_log = config.failed_log or data_dir / "failed_files.txt"

    processed: list[str] = []
    failed: list[str] = []
    frames: list[pd.DataFrame] = []

    for path in tqdm(files, desc="Parsing monthly exports"):
        parsed = _parse_filename(path.name)
        if not parsed:
            failed.append(f"{path.name} (unrecognised filename)")
            continue

        fiscal_year, end_date = parsed
        result = _read_product_sheet(path)
        if isinstance(result, str):
            failed.append(f"{path.name} ({result})")
            continue

        result["fiscal_year"] = fiscal_year
        result["end_date"] = end_date
        frames.append(result)
        processed.append(path.name)

    processed_log.write_text("\n".join(processed))
    failed_log.write_text("\n".join(failed))

    if not frames:
        raise RuntimeError("No valid Excel files were parsed.")

    mastering = pd.concat(frames, ignore_index=True).sort_values(
        by=["fiscal_year", "hs_code", "country", "end_date"]
    )
    mastering["USD"] = mastering.groupby(["fiscal_year", "hs_code", "country"])["usd_cumulative"].diff()
    mastering["USD"] = mastering["USD"].fillna(mastering["usd_cumulative"]).clip(lower=0).round(2)
    mastering["month"] = mastering["end_date"].dt.strftime("%B-%Y")

    return mastering[["hs_code", "country", "month", "USD"]].reset_index(drop=True)
