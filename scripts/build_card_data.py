#!/usr/bin/env python3
"""Build data/hsk/cards.json from downloaded HSK raw level files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, TypedDict

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / "data" / "hsk" / "raw"
DEFAULT_OUT = ROOT / "data" / "hsk" / "cards.json"
LEVELS = (1, 2, 3, 4, 5, 6, 7)

# Pretty exclusive/newest JSON only (not *.min.json abbreviated keys).
_JUNK_RE = re.compile(r"\b(archaic|variant of)\b|\(old\)", re.I)


class Form(TypedDict):
    traditional: str
    transcriptions: dict[str, str]
    meanings: list[str]
    classifiers: list[str]


class Entry(TypedDict):
    simplified: str
    radical: str
    frequency: int
    pos: list[str]
    forms: list[Form]

# TODO: Implement filter on meanings to throw out less useful meanings
def choose_english_basic(meanings: list[str]) -> str:
    if not meanings:
        return ""
    gloss = meanings[0].split(";")[0].strip()
    return gloss[:255]


# TODO: Switch up how this is done. Filter junk meanings, then reject if no valid meanings left.
def is_junk_form(form: Form) -> bool:
    pinyin = form["transcriptions"]["pinyin"].strip()
    # Capitalized pinyin is a surname reading in this dataset.
    # TODO: Some proper nouns are capitalized, so we need to also search for a surname meaning
    if pinyin[:1].isupper():
        return True
    blob = " ".join(form["meanings"])
    return bool(_JUNK_RE.search(blob))


def card_from_form(entry: Entry, form: Form, level: int) -> dict[str, Any]:
    return {
        "hsk_level": level,
        "simplified": entry["simplified"].strip(),
        "chinese": form["traditional"].strip(),
        "pinyin": form["transcriptions"]["pinyin"].strip(),
        "english_basic": choose_english_basic(form["meanings"]),
    }


def build_cards_from_entries(entries: list[Entry], level: int) -> tuple[list[dict], int]:
    cards: list[dict[str, Any]] = []
    dropped = 0
    for entry in entries:
        for form in entry["forms"]:
            if is_junk_form(form):
                dropped += 1
                continue
            cards.append(card_from_form(entry, form, level))
    return cards, dropped


def build_cards(raw_dir: Path, levels: tuple[int, ...]) -> tuple[list[dict], int]:
    all_cards: list[dict[str, Any]] = []
    dropped_total = 0
    for level in levels:
        path = raw_dir / f"{level}.json"
        if not path.is_file():
            raise FileNotFoundError(f"Missing raw level file: {path}")
        entries = json.loads(path.read_text(encoding="utf-8"))
        cards, dropped = build_cards_from_entries(entries, level)
        all_cards.extend(cards)
        dropped_total += dropped
    return all_cards, dropped_total


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=DEFAULT_RAW,
        help=f"Directory with {{1-7}}.json (default: {DEFAULT_RAW})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output cards.json path (default: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--levels",
        default=",".join(str(level) for level in LEVELS),
        help="Comma-separated levels to include (default: 1-7)",
    )
    args = parser.parse_args(argv)

    try:
        levels = tuple(int(part.strip()) for part in args.levels.split(",") if part.strip())
    except ValueError as exc:
        raise SystemExit("--levels must be comma-separated integers") from exc
    if not levels:
        raise SystemExit("--levels must include at least one level")

    raw_dir = args.raw_dir.expanduser().resolve()
    out_path = args.out.expanduser().resolve()

    try:
        cards, dropped = build_cards(raw_dir, levels)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(cards)} cards to {out_path} (dropped {dropped} junk forms)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
