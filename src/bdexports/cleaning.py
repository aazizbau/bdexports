from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import CountryCleaningConfig, UniqueCountryConfig, VerificationConfig

COUNTRY_MAP = {
    "AFGHANISTAN": "Afghanistan",
    "ALBANIA": "Albania",
    "ALGERIA": "Algeria",
    "AMERICAN SAMOA": "American Samoa",
    "ANDORRA": "Andorra",
    "ANGOLA": "Angola",
    "ARGENTINA": "Argentina",
    "ARMENIA": "Armenia",
    "ARUBA": "Aruba",
    "AUSTRALIA": "Australia",
    "AUSTRIA": "Austria",
    "AZERBAIJAN": "Azerbaijan",
    "TIMOR": "Timor",
    "CONGO": "Congo",
    "GREAT BRITAIN": "United Kingdom",
    "UNITED KINGDOM": "United Kingdom",
    "KAMPUCHEA DEMOCRATIC": "Cambodia",
    "CAMBODIA": "Cambodia",
    "KOREAN REPUBLIC OF": "South Korea",
    "KOREA, REPUBLIC OF": "South Korea",
    "NORTH KOREA": "North Korea",
    "KOREA, DEMOCRATIC PEOPLE'S REPUBLIC OF": "North Korea",
    "RUSSIA": "Russian Federation",
    "RUSSIAN FEDERATION": "Russian Federation",
    "VIETNAM": "Vietnam",
    "VIET NAM": "Vietnam",
    "WESTERN SAMOA": "Samoa",
    "SAMOA": "Samoa",
    "BOLIVIA, PLURINATIONAL STATE OF": "Bolivia",
    "CONGO, THE DEMOCRATIC REPUBLIC OF THE": "Congo, The Democratic Republic of",
    "IRAN, ISLAMIC REPUBLIC OF": "Iran",
    "LAO PEOPLE'S DEMOCRATIC REPUBLIC": "Laos",
    "MOLDOVA, REPUBLIC OF": "Moldova",
    "PALESTINIAN TERRITORY, OCCUPIED": "Palestinian Territory",
    "TAIWAN, PROVINCE OF CHINA": "Taiwan",
    "TANZANIA, UNITED REPUBLIC OF": "Tanzania",
    "VENEZUELA, BOLIVARIAN REPUBLIC OF": "Venezuela",
    "DEMOCRATIC YEMEN": "Yemen",
    "YEMEN": "Yemen",
    "LIBYAN ARAB JAMAHIRIYA": "Libya",
    "MACEDONIA": "North Macedonia",
    "MACEDONIA, THE FORMER YUGOSLAV REPUBLIC OF": "North Macedonia",
    "MICRONESIA, FEDERATED STATES OF": "Micronesia",
    "SYRIAN ARAB REPUBLIC": "Syria",
    "TIMOR LESTE": "Timor-Leste",
    "TIMOR-LESTE": "Timor-Leste",
    "VIRGIN ISLANDS, US": "Virgin Islands, U.S.",
    "VIRGIN ISLANDS, U.S.": "Virgin Islands, U.S.",
    "XK": "Kosovo",
    "KOSOVO": "Kosovo",
    "BRUNEI DARUSSALAM": "Brunei Darussalam",
    "BURKINA FASO": "Burkina Faso",
    "COLOMBIA": "Colombia",
    "COTE D'IVOIRE": "Cote d'Ivoire",
    "CÔTE D'IVOIRE": "Cote d'Ivoire",
    "GUINEA-BISSAU": "Guinea-Bissau",
    "KAZAKHSTAN": "Kazakhstan",
    "LIBERIA": "Liberia",
    "MACAO": "Macao",
    "PAPUA NEW GUINEA": "Papua New Guinea",
    "SAO TOME AND PRINCIPE": "Sao Tome and Principe",
    "URUGUAY": "Uruguay",
    "NEW ISRAEL": "Israel",
    "NEW TAIWAN": "Taiwan",
    "BOSNIA &AMP": "Bosnia and Herzegovina",
    "BOSNIA AND HERZEGOVINA": "Bosnia and Herzegovina",
    "RÉUNION": "Reunion",
    "REUNION": "Reunion",
    "Kampuchea Democratic": "Cambodia",
    "Korean Republic of": "South Korea",
    "Russia": "Russian Federation",
    "Western Samoa": "Samoa",
    "Congo, The Democratic Republic of": "Congo, The Democratic Republic of",
    "Democratic Yemen": "Yemen",
    "Libyan Arab Jamahiriya": "Libya",
    "Micronesia, Federated State": "Micronesia",
    "Sao Tome and Principle": "Sao Tome and Principe",
    "Uruguayo": "Uruguay",
}

JUNK_VALUES = {
    "Bangladesh Local Export",
    "Bangladesh local export code",
    "European Union",
    "Not Defined",
    "Unknown",
    "Various Countries",
    "TP",
    "Tp",
    "Bangladesh Local Export Code",
}


def clean_and_combine_countries(config: CountryCleaningConfig) -> pd.DataFrame:
    df = pd.read_csv(config.input_csv)
    for column in ("country", "hs_code", "month"):
        if column not in df.columns:
            raise ValueError(f"Column '{column}' missing from {config.input_csv}")

    df["country"] = df["country"].astype(str).str.strip()
    df["hs_code"] = df["hs_code"].astype(str).str.strip()
    df["month"] = df["month"].astype(str).str.strip()

    df["country"] = df["country"].replace(COUNTRY_MAP)
    df["country"] = df["country"].str.title()
    df["country"] = df["country"].replace({"Virgin Islands, Us": "Virgin Islands, U.S."})

    junk = set(config.junk_values) if config.junk_values else JUNK_VALUES
    filtered = df[~df["country"].isin(junk)].copy()

    aggregated = (
        filtered.groupby(["hs_code", "country", "month"], as_index=False)["USD"].sum().round(2)
    )
    aggregated.to_csv(config.output_csv, index=False)
    return aggregated


def create_unique_country_list(config: UniqueCountryConfig) -> None:
    df = pd.read_csv(config.input_csv)
    if "country" not in df.columns:
        raise ValueError("The CSV must contain a 'country' column.")

    unique = sorted(df["country"].dropna().unique().tolist())
    Path(config.output_txt).write_text("\n".join(unique), encoding="utf-8")


def verify_zero_values(config: VerificationConfig) -> pd.DataFrame:
    df_original = pd.read_csv(config.original_csv, dtype={"hs_code": str})
    df_original["USD"] = (
        pd.to_numeric(df_original["USD"].astype(str).str.replace(",", ""), errors="coerce")
        .fillna(0)
        .astype(float)
    )
    df_original["hs_code"] = df_original["hs_code"].str.strip()
    df_original["month"] = df_original["month"].str.strip()
    df_original["country"] = df_original["country"].str.strip().str.title()

    original_sums = (
        df_original.groupby(["hs_code", "country", "month"], as_index=False)["USD"].sum()
    )
    original_sums = original_sums.rename(columns={"USD": "Original_USD_Sum"})

    df_cleaned = pd.read_csv(config.cleaned_csv, dtype={"hs_code": str})
    zeros = df_cleaned[df_cleaned["USD"] == 0].copy()

    verification = zeros.merge(
        original_sums, on=["hs_code", "country", "month"], how="left"
    ).fillna({"Original_USD_Sum": 0})

    verification["Verified"] = verification["Original_USD_Sum"].apply(
        lambda val: "Yes" if abs(val) < 0.001 else "No"
    )
    verification.to_csv(config.report_csv, index=False)
    return verification
