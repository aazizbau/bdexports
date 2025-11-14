from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from .config import RenameConfig

MONTH_MAP = {
    "january": "Jan",
    "jan": "Jan",
    "february": "Feb",
    "feb": "Feb",
    "march": "Mar",
    "mar": "Mar",
    "april": "Apr",
    "apr": "Apr",
    "may": "May",
    "june": "Jun",
    "jun": "Jun",
    "july": "Jul",
    "jul": "Jul",
    "august": "Aug",
    "aug": "Aug",
    "september": "Sep",
    "sept": "Sep",
    "sep": "Sep",
    "october": "Oct",
    "oct": "Oct",
    "november": "Nov",
    "nov": "Nov",
    "december": "Dec",
    "dec": "Dec",
}


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def _header_matches_any(text: str) -> bool:
    candidates = [
        "report: product-wise 2 digit",
        "report: commodity-wise data of countries",
    ]
    normalized = _normalize_text(text)
    if any(cand in normalized for cand in candidates):
        return True

    if (
        "product" in normalized
        and "wise" in normalized
        and "2" in normalized
        and "digit" in normalized
    ):
        return True

    if "commodity" in normalized and "data of countries" in normalized:
        return True

    return bool(re.search(r"hs\s*code.*\d+\s*digit.*wise\s*export\s*report", normalized))


def _extract_period(rows: list[str]) -> str | None:
    for row in rows:
        if row and re.search(r"(?i)\bperiod\b", row):
            match = re.search(r"(?i)\bperiod\b[:\s]*(.*)", row)
            if match:
                return match.group(1).strip()
    return None


def _expand_two_digit_year(start_year: str, two_digit: str) -> str:
    if len(two_digit) == 2:
        return start_year[:2] + two_digit
    return two_digit


def _sanitize_period(period: str) -> str | None:
    text = re.sub(r"\s+", " ", period.replace("–", "-").replace("—", "-").strip())
    if not text:
        return None

    month_keys = sorted(MONTH_MAP.keys(), key=len, reverse=True)
    month_regex = r"\b(" + "|".join(re.escape(k) for k in month_keys) + r")\b"
    month_hits = re.findall(month_regex, text, flags=re.IGNORECASE)
    months = [MONTH_MAP[key.lower()] for key in month_hits if key.lower() in MONTH_MAP]

    years = None
    range_match = re.search(r"(\d{4})\s*[-/]\s*(\d{2,4})", text)
    if range_match:
        start = range_match.group(1)
        end = _expand_two_digit_year(start, range_match.group(2))
        years = f"{start}_{end}"
    else:
        single = re.search(r"\b(19|20)\d{2}\b", text)
        if single:
            years = single.group(0)

    parts: list[str] = []
    if months:
        parts.extend(months)
    if years:
        parts.append(years)

    if not parts:
        cleaned = re.sub(r"[^\w]+", "_", text).strip("_")
        return cleaned or None

    return "_".join(parts)


def process_and_rename(config: RenameConfig) -> None:
    source = Path(config.source_dir)
    destination = Path(config.target_dir)
    archive = Path(config.archive_dir)

    destination.mkdir(parents=True, exist_ok=True)
    archive.mkdir(parents=True, exist_ok=True)

    files = [path for path in source.glob("*") if path.suffix.lower() in {".xls", ".xlsx"}]
    renamed = 0
    skipped = 0

    for path in tqdm(files, desc="Renaming product files"):
        try:
            workbook = pd.ExcelFile(path)
        except Exception as exc:
            tqdm.write(f"✖ Failed to read {path.name}: {exc}")
            skipped += 1
            continue

        sheet = next((name for name in workbook.sheet_names if "2 digit" in name.lower()), None)
        if not sheet:
            skipped += 1
            continue

        df = pd.read_excel(path, sheet_name=sheet, header=None, nrows=10)
        rows: list[str] = []
        for i in range(min(8, len(df))):
            row = df.iloc[i]
            joined = " ".join(str(cell) for cell in row if pd.notna(cell)).strip()
            rows.append(joined)

        if not any(_header_matches_any(row) for row in rows):
            skipped += 1
            continue

        period_raw = _extract_period(rows)
        sanitized = _sanitize_period(period_raw) if period_raw else None
        if not sanitized:
            skipped += 1
            continue

        stem = f"Product_wise_export_2Digit_{sanitized}"
        target = destination / f"{stem}{path.suffix}"
        counter = 1
        while target.exists():
            target = destination / f"{stem}_v{counter}{path.suffix}"
            counter += 1

        target.write_bytes(path.read_bytes())
        path.replace(archive / path.name)
        tqdm.write(f"✔ {path.name} -> {target.name}")
        renamed += 1

    print(f"Renamed {renamed} files. Skipped {skipped}.")
