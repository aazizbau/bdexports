from __future__ import annotations

import re
import textwrap
from pathlib import Path

import bar_chart_race as bcr
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

from ..config import BarRaceCountryConfig, BarRaceProductConfig
from ..constants import DEFAULT_ANNOTATION, HS_CODE_MAP


def _format_value(value: float) -> str:
    if value >= 1e9:
        return f"$ {value / 1e9:.2f} B"
    if value >= 1e6:
        return f"$ {value / 1e6:.2f} M"
    if value >= 1e3:
        return f"$ {value / 1e3:.0f} K"
    return f"$ {value:,.0f}"


def _wrap_label(name: str, code: str, width: int = 24) -> str:
    wrapped = textwrap.fill(name, width=width)
    return f"{wrapped}\n(HS {code})"


def _common_ax_setup(ax: plt.Axes, portrait: bool) -> None:
    ax.set_xlabel("Cumulative Exports (USD)", fontsize=14, labelpad=12)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _pos=None: _format_value(float(x))))
    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=6))
    if portrait:
        ax.tick_params(axis="x", labelsize=14)
        ax.tick_params(axis="y", labelsize=14)
    else:
        ax.tick_params(axis="x", labelsize=12)
        ax.tick_params(axis="y", labelsize=11)
    ax.grid(axis="x", linestyle=":", linewidth=0.6, color="#bcbcbc")
    ax.set_axisbelow(True)


def _load_dataframe(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"hs_code": str})


def create_country_bar_race(config: BarRaceCountryConfig) -> None:
    df = _load_dataframe(config.input_csv)
    df["hs_code"] = df["hs_code"].str.strip().str.zfill(2)
    config.output_video.parent.mkdir(parents=True, exist_ok=True)

    filtered = df[df["country"] == config.target_country].copy()
    if filtered.empty:
        raise ValueError(f"No data found for country '{config.target_country}'.")

    filtered["month_dt"] = pd.to_datetime(filtered["month"], format="%B-%Y")
    pivoted = filtered.pivot_table(values="USD", index="month_dt", columns="hs_code", aggfunc="sum").fillna(0)
    pivoted = pivoted.apply(lambda col: col.cumsum())

    pivoted.columns = [
        _wrap_label(HS_CODE_MAP.get(code, "Unknown"), code)
        for code in pivoted.columns
    ]

    figsize = (9, 16) if config.portrait else (12, 8)
    fig, ax = plt.subplots(figsize=figsize, dpi=144)
    fig.subplots_adjust(left=0.22 if config.portrait else 0.18, right=0.96, top=0.9, bottom=0.08)
    ax.set_title(
        f"Top {config.num_bars} Exported Products\nfrom Bangladesh to {config.target_country}",
        fontsize=20 if config.portrait else 16,
        pad=18,
        weight="bold",
    )
    _common_ax_setup(ax, portrait=config.portrait)

    annotation = config.annotation or DEFAULT_ANNOTATION

    bcr.bar_chart_race(
        df=pivoted,
        filename=config.output_video,
        n_bars=config.num_bars,
        sort="desc",
        bar_size=0.9,
        dpi=300,
        cmap="Dark2",
        fig=fig,
        title="",
        bar_label_size=12 if config.portrait else 10,
        period_label={"x": 0.95, "y": 0.15 if config.portrait else 0.25, "ha": "right", "va": "center", "size": 26 if config.portrait else 20},
        period_fmt="%B-%Y",
        period_summary_func=lambda values, ranks: {
            "x": 0.5,
            "y": 0.03,
            "s": annotation,
            "ha": "center",
            "size": 12,
        },
    )


def create_product_bar_race(config: BarRaceProductConfig) -> None:
    df = _load_dataframe(config.input_csv)
    df["hs_code"] = df["hs_code"].str.strip().str.zfill(2)
    product_name = HS_CODE_MAP.get(config.hs_code.zfill(2), f"HS {config.hs_code}")
    config.output_video.parent.mkdir(parents=True, exist_ok=True)

    filtered = df[df["hs_code"] == config.hs_code.zfill(2)].copy()
    if filtered.empty:
        raise ValueError(f"No rows found for HS code '{config.hs_code}'.")

    filtered["month_dt"] = pd.to_datetime(filtered["month"], format="%B-%Y")
    pivoted = filtered.pivot_table(values="USD", index="month_dt", columns="country", aggfunc="sum").fillna(0)
    pivoted.columns = [re.sub(r"[^A-Za-z0-9\s-]", "", col).strip() for col in pivoted.columns]
    pivoted = pivoted.apply(lambda col: col.cumsum())

    figsize = (12, 16) if config.portrait else (14, 8)
    fig, ax = plt.subplots(figsize=figsize, dpi=144)
    fig.subplots_adjust(left=0.2 if config.portrait else 0.16, right=0.95, top=0.9, bottom=0.08)
    ax.set_title(
        f"Top {config.num_bars} Importing Countries\nfor {product_name}",
        fontsize=22 if config.portrait else 18,
        pad=18,
        weight="bold",
    )
    ax.yaxis.set_ticks([])
    _common_ax_setup(ax, portrait=config.portrait)

    bcr.bar_chart_race(
        df=pivoted,
        filename=config.output_video,
        n_bars=config.num_bars,
        sort="desc",
        bar_size=0.88,
        bar_label_size=12 if config.portrait else 10,
        tick_label_size=12 if config.portrait else 10,
        dpi=300,
        cmap="tab20",
        fig=fig,
        title="",
        period_label={"x": 0.95, "y": 0.15 if config.portrait else 0.2, "ha": "right", "va": "center", "size": 28 if config.portrait else 22},
        period_fmt="%B, %Y",
        period_summary_func=lambda values, ranks: {
            "x": 0.95 if config.portrait else 0.5,
            "y": 0.07 if config.portrait else 0.1,
            "s": f"Total exports: {_format_value(values.sum())}",
            "ha": "right" if config.portrait else "center",
            "size": 16 if config.portrait else 14,
        },
    )
