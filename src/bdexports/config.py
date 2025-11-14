from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass(slots=True)
class DownloadConfig:
    """Configuration for scraping and downloading Excel files."""

    export_page: str
    output_dir: Path
    headless: bool = True
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/127.0 Safari/537.36"
    )


@dataclass(slots=True)
class SheetFilterConfig:
    """Move files that contain a specific sheet."""

    source_dir: Path
    destination_dir: Path
    sheet_name: str


@dataclass(slots=True)
class RenameConfig:
    """Rename files after extracting the fiscal period from headers."""

    source_dir: Path
    target_dir: Path
    archive_dir: Path


@dataclass(slots=True)
class ExportProcessingConfig:
    """Process product-wise Excel dumps into a single CSV."""

    data_dir: Path
    processed_log: Path | None = None
    failed_log: Path | None = None


@dataclass(slots=True)
class CountryCleaningConfig:
    """Clean aggregated CSV output."""

    input_csv: Path
    output_csv: Path
    junk_values: List[str] = field(default_factory=list)


@dataclass(slots=True)
class UniqueCountryConfig:
    """Generate a sorted list of unique country names."""

    input_csv: Path
    output_txt: Path


@dataclass(slots=True)
class VerificationConfig:
    """Verify zero rows in the cleaned CSV."""

    original_csv: Path
    cleaned_csv: Path
    report_csv: Path


@dataclass(slots=True)
class BarRaceCountryConfig:
    """Render a country-level HS-code bar chart race."""

    input_csv: Path
    output_video: Path
    target_country: str
    num_bars: int = 15
    annotation: Optional[str] = None
    portrait: bool = False


@dataclass(slots=True)
class BarRaceProductConfig:
    """Render a product level chart where each bar is a country."""

    input_csv: Path
    output_video: Path
    hs_code: str
    num_bars: int = 12
    portrait: bool = False
