#!/usr/bin/env python3
"""
Download HSK 3.0 exclusive newest wordlists into data/hsk/raw/ (gitignored).
Usage: uv run scripts/download_hsk.py
"""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path

LEVELS = (1, 2, 3, 4, 5, 6, 7)
BASE_URL = (
    "https://raw.githubusercontent.com/drkameleon/complete-hsk-vocabulary/"
    "main/wordlists/exclusive/newest"
)
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "hsk" / "raw"


def download_level(level: int, out_dir: Path, *, force: bool) -> Path:
    dest = out_dir / f"{level}.json"
    if dest.is_file() and not force:
        print(f"skip {dest} (exists; use --force to overwrite)")
        return dest

    url = f"{BASE_URL}/{level}.json"
    try:
        with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310
            data = response.read()
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to download {url}: {exc}") from exc

    out_dir.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"wrote {dest} ({len(data)} bytes)")
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output directory (default: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing level files",
    )
    args = parser.parse_args(argv)

    out_dir = args.out_dir.expanduser().resolve()
    for level in LEVELS:
        download_level(level, out_dir, force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
