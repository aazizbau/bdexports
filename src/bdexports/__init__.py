"""
Utilities for downloading, cleaning, and visualising Bangladesh export data.
"""

from importlib import metadata


def __getattr__(name: str) -> str:
    if name == "__version__":
        try:
            return metadata.version("bdexports")
        except metadata.PackageNotFoundError:  # pragma: no cover - fallback for editable installs
            return "0.0.0"
    raise AttributeError(name)


__all__ = ["__version__"]
