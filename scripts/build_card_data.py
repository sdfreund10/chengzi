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
_ALWAYS_JUNK_MEANING_RE = re.compile(r"\b(archaic|variant of)\b|\(old\)", re.I)
_SURNAME_MEANING_RE = re.compile(r"\bsurname\b", re.I)


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


def is_junk_meaning(meaning: str, *, pinyin_capitalized: bool) -> bool:
    if _ALWAYS_JUNK_MEANING_RE.search(meaning):
        return True
    # "surname Bai" is a reading label; "surname" as a gloss (姓) is useful.
    if pinyin_capitalized and _SURNAME_MEANING_RE.search(meaning):
        return True
    return False


def useful_meanings(meanings: list[str], pinyin: str) -> list[str]:
    capitalized = bool(pinyin.strip()[:1].isupper())
    return [m for m in meanings if not is_junk_meaning(m, pinyin_capitalized=capitalized)]


_ENGLISH_BASIC_MAX = 255


def choose_english_basic(meanings: list[str]) -> str:
    """Join useful meanings until the field length limit."""
    parts: list[str] = []
    size = 0
    for meaning in meanings:
        piece = meaning.strip()
        if not piece:
            continue
        # "; " between senses (2 chars) once we already have content.
        sep = 2 if parts else 0
        if size + sep + len(piece) <= _ENGLISH_BASIC_MAX:
            parts.append(piece)
            size += sep + len(piece)
            continue
        if not parts:
            return piece[:_ENGLISH_BASIC_MAX]
        break
    return "; ".join(parts)


def card_from_form(
    entry: Entry,
    form: Form,
    level: int,
    meanings: list[str],
) -> dict[str, Any]:
    return {
        "hsk_level": level,
        "simplified": entry["simplified"].strip(),
        "chinese": form["traditional"].strip(),
        "pinyin": form["transcriptions"]["pinyin"].strip(),
        "english_basic": choose_english_basic(meanings),
    }


def build_cards_from_entries(entries: list[Entry], level: int) -> tuple[list[dict], int]:
    cards: list[dict[str, Any]] = []
    dropped = 0
    for entry in entries:
        for form in entry["forms"]:
            pinyin = form["transcriptions"]["pinyin"]
            meanings = useful_meanings(form["meanings"], pinyin)
            if not meanings:
                dropped += 1
                continue
            cards.append(card_from_form(entry, form, level, meanings))
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
