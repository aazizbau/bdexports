from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterable

import requests
from playwright.async_api import Browser, Page, async_playwright
from tqdm.asyncio import tqdm_asyncio

from .config import DownloadConfig


async def _gather_excel_links(page: Page) -> list[str]:
    links = await page.query_selector_all("a")
    excel_urls: list[str] = []

    for link in links:
        href = await link.get_attribute("href")
        if not href:
            continue

        href_lower = href.lower()
        if not (href_lower.endswith(".xls") or href_lower.endswith(".xlsx")):
            continue

        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = "https://epb.gov.bd" + href

        excel_urls.append(href)

    return excel_urls


def _unique_path(output_dir: Path, original_name: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate = output_dir / original_name
    base = candidate.stem
    suffix = candidate.suffix
    counter = 1

    while candidate.exists():
        candidate = output_dir / f"{base}_{counter}{suffix}"
        counter += 1

    return candidate


def _download_file(url: str, destination: Path, headers: dict[str, str]) -> str:
    response = requests.get(url, timeout=120, headers=headers)
    response.raise_for_status()
    destination.write_bytes(response.content)
    return destination.name


async def _download_all(urls: Iterable[str], output_dir: Path, headers: dict[str, str]) -> None:
    async def _task(url: str) -> None:
        final_path = _unique_path(output_dir, Path(url.split("?")[0]).name)
        try:
            name = await asyncio.to_thread(_download_file, url, final_path, headers)
            tqdm_asyncio.write(f"✔ Downloaded {name}")
        except Exception as exc:  # pragma: no cover - network issues
            tqdm_asyncio.write(f"✖ Failed to download {url}: {exc}")

    await tqdm_asyncio.gather(*(_task(url) for url in urls), desc="Downloading Excel files")


async def download_exports(config: DownloadConfig) -> None:
    """
    Crawl the EPB export page, find every Excel link, and download it to ``config.output_dir``.
    """

    async with async_playwright() as playwright:
        browser: Browser = await playwright.chromium.launch(headless=config.headless)
        page: Page = await browser.new_page()

        try:
            await page.goto(config.export_page, wait_until="networkidle", timeout=180_000)
            await page.wait_for_selector("table.bordered tbody tr", timeout=180_000)
        except Exception as exc:  # pragma: no cover - site/network issues
            raise RuntimeError(f"Failed to load export page '{config.export_page}': {exc}") from exc

        links = await _gather_excel_links(page)
        await browser.close()

    if not links:
        raise RuntimeError("No Excel links found on the export page.")

    await _download_all(links, config.output_dir, headers={"User-Agent": config.user_agent})


def run_download(config: DownloadConfig) -> None:
    """Convenience helper for CLI scripts."""

    asyncio.run(download_exports(config))
