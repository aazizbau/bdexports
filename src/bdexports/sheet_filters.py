from __future__ import annotations

from pathlib import Path

import pandas as pd
from tqdm import tqdm

from .config import SheetFilterConfig


def move_files_with_sheet(config: SheetFilterConfig) -> None:
    """
    Move every Excel file from ``config.source_dir`` to ``config.destination_dir`` if
    it contains ``config.sheet_name`` (case insensitive).
    """

    source = Path(config.source_dir)
    destination = Path(config.destination_dir)
    destination.mkdir(parents=True, exist_ok=True)

    files = [path for path in source.glob("*") if path.suffix.lower() in {".xls", ".xlsx"}]
    if not files:
        print(f"No Excel files found in {source}")
        return

    moved = 0
    skipped = 0

    for path in tqdm(files, desc=f"Searching for '{config.sheet_name}'"):
        try:
            with pd.ExcelFile(path) as workbook:
                has_sheet = any(
                    config.sheet_name.lower() == sheet.lower()
                    for sheet in workbook.sheet_names
                )
        except Exception as exc:
            tqdm.write(f"✖ Unable to read {path.name}: {exc}")
            skipped += 1
            continue

        if has_sheet:
            target = destination / path.name
            path.replace(target)
            tqdm.write(f"✔ Moved {path.name}")
            moved += 1
        else:
            skipped += 1

    print(f"Completed. Moved {moved} files, skipped {skipped}.")
