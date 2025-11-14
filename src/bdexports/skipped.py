from __future__ import annotations

from pathlib import Path
import shutil


def copy_skipped_files(data_dir: Path, skipped_file: Path, failed_dir: Path) -> None:
    """
    Copy all file names listed in ``skipped_file`` from ``data_dir`` to ``failed_dir``.
    """

    if not skipped_file.exists():
        raise FileNotFoundError(f"Skipped list not found: {skipped_file}")

    failed_dir.mkdir(parents=True, exist_ok=True)
    names = [line.strip() for line in skipped_file.read_text().splitlines() if line.strip()]

    if not names:
        print("No skipped files listed.")
        return

    copied = 0
    missing = 0

    for name in names:
        src = data_dir / name
        dst = failed_dir / name
        if src.exists():
            shutil.copy2(src, dst)
            copied += 1
        else:
            print(f"✖ Missing file mentioned in log: {name}")
            missing += 1

    print(f"Copied {copied} files to {failed_dir}. Missing: {missing}.")
