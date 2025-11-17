# Bangladesh Export Data Toolkit

This repository converts the ad-hoc `bd_export_data_bar_race.ipynb` notebook into a
modular Python project.  Each logical step (download, file triage, cleaning and
visualisation) now lives in a dedicated module with small CLI wrappers under
`scripts/`.

## Project layout

```
.
├─ README.md
├─ requirements.txt
├─ src/bdexports/          # Python package
│   ├─ config.py           # Dataclasses shared by the CLIs
│   ├─ constants.py        # HS code map + default annotations
│   ├─ downloader.py       # Playwright based scraper
│   ├─ sheet_filters.py    # Move files that contain certain sheets
│   ├─ renamer.py          # Rename Excel files by fiscal period
│   ├─ skipped.py          # Copy skipped files into a failure folder
│   ├─ pipeline.py         # Parse Excel dumps into a monthly CSV
│   ├─ cleaning.py         # Country cleaning, unique list, verification
│   └─ viz/bar_race.py     # Country and product level chart-race helpers
└─ scripts/                # Thin CLI wrappers for each module
```

## Installing dependencies

From a Windows terminal (PowerShell or Command Prompt):

1. Clone and enter the repo  
   `git clone https://github.com/<you>/bdexports.git`  
   `cd bdexports`
2. Create/activate a virtual environment  
   `python -m venv .venv`  
   `.venv\Scripts\activate`
3. Install dependencies and Playwright browser  
   `pip install -r requirements.txt`  
   `playwright install chromium`
4. (Optional) Install the package in editable mode if you want `bdexports` imports everywhere  
   `pip install -e .`
5. Make FFmpeg available for animations  
   - Either add `C:\ffmpeg\bin` (or your install path) to `PATH`, or  
   - Set `FFMPEG_PATH` before running the visualization scripts:  
     `setx FFMPEG_PATH "C:\ffmpeg\bin\ffmpeg.exe"` (permanent) or `$env:FFMPEG_PATH = "C:\ffmpeg\bin\ffmpeg.exe"` (current session)

## Example pipeline

All commands assume you run them from the project root (where this README lives).  
Every script defaults to the `data/` and `output/` folders inside the repo, so you
can copy‑paste the commands below right after a `git clone`.

1. **Download every Excel file**  
   `python scripts/download_exports.py`

2. **Move the relevant sheets**  
   `python scripts/move_files_by_sheet.py --source data/raw --destination data/product_2digit --sheet-name "2 Digit"`  
   `python scripts/move_files_by_sheet.py --source data/product_2digit --destination data/country_wise --sheet-name "Country Details"`

3. **Rename files using the period in their headers**  
   `python scripts/rename_product_files.py --source data/product_2digit --target data/product_wise --archive data/product_wise_source`

4. **Build the monthly dataset**  
   `python scripts/build_monthly_dataset.py --data-dir data/product_wise --output-csv data/monthly_export_data.csv`

5. **Clean countries + generate helper files**  
   `python scripts/clean_countries.py --input-csv data/monthly_export_data.csv --output-csv data/monthly_export_data_cleaned.csv`  
   `python scripts/list_countries.py --input-csv data/monthly_export_data_cleaned.csv --output-txt data/unique_countries.txt`  
   `python scripts/verify_zero_rows.py --original-csv data/monthly_export_data.csv --cleaned-csv data/monthly_export_data_cleaned.csv --report data/verification_results.csv`

6. **Copy skipped source files (optional)**  
   `python scripts/copy_skipped_files.py`

7. **Visualise the results**  
   `python scripts/bar_race_country.py --country Japan --portrait`  
   `python scripts/bar_race_product.py --hs-code 03`  
   `python scripts/hs_countries_years.py --hs 03 --countries Japan Germany Canada France India Malaysia --years 2018 2022`  
   `python scripts/top_buyers_over_time.py --hs 62 --top 5 --start-year 2018 --end-year 2024 --palette "#004c6d" "#2979a8" "#56a3d7" "#8ec5f4" "#cde6ff"`  
   `python scripts/regional_share_treemap.py --year 2023 --category leather --region-scope continent`  
   `python scripts/small_multiple_bar.py --years 2022 2023 --top 3`  
   `python scripts/top_hs_codes_heatmap.py --years 2018 2019 2020 2021 2022 2023 2024 --top 15`  
   `python scripts/hs_to_destination_sankey.py --year 2023 --top 10`

Each CLI provides `--help` for optional parameters (e.g., number of bars, portrait layout).

## Notes

- Paths in the examples are relative; feel free to adapt them to your storage layout.
- The Playwright downloader reuses the original notebook logic, including duplicate filename handling and User-Agent spoofing.
- Visualisation helpers read the cleaned CSV so they remain decoupled from the earlier steps.  Orientation, annotations, and bar counts are exposed via CLI flags.
