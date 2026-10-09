"""
Take data from data/hsk/cards.json and prep it for use in the app.
Filter out less useful cards, recategorize some cards, and add supporting data.

Usage:
  uv run scripts/prep_cards.py --limit 7
  uv run scripts/prep_cards.py
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

import dotenv
import requests

from hsk_categories import HSK_CATEGORIES

dotenv.load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IN = ROOT / "data" / "hsk" / "cards.json"
DEFAULT_OUT = ROOT / "data" / "hsk" / "prepped_cards.json"
DEFAULT_LOG_DIR = ROOT / "data" / "hsk" / "logs"


class Card(TypedDict):
    hsk_level: int
    simplified: str
    chinese: str
    pinyin: str
    english_basic: str


ANALYSIS_PROMPT = """
You are a Chinese tutor helping prepare flash cards for a student learning Chinese in Taiwan.
You will be given a Chinese word with basic information from the HSK curriculum.

Your goal is to analyze the word and provide information to help the student learn words and what to
what is most important for achieving proficiency.

## GUIDELINES
**Meaning**
Meaning should be as concise as possible to convery the meaning of a word.
Favor the provided HSK meaning and only add details if necesssary.

**Example Sentence**
The example sentence should use words at the same level or easier than the given word.
Try to use the provided HSK level as a guide for what words to use.
All varients of the example sentence should be equivalent.

**should_exclude**
Some words are given an alternative definition by the HSK curriculum that are not actually useful for
a learner trying to achieve proficiency. Slang or archaic uses of a word should be excluded from the deck.
Consider the provided HSK level and decide if the word is actually useful for a learner at that stage.
They may still be included in other categories.
"""

OUTPUT_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "card_data",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "meaning": {
                    "type": "string",
                    "description": "Meaning of the word or phrase in English",
                },
                "example_sentence": {
                    "type": "object",
                    "description": "An example sentence using the word",
                    "properties": {
                        "traditional": {
                            "type": "string",
                            "description": "The example sentence in traditional Chinese.",
                        },
                        "simplified": {
                            "type": "string",
                            "description": "The example sentence in simplified Chinese.",
                        },
                        "pinyin": {
                            "type": "string",
                            "description": "The example sentence in pinyin.",
                        },
                        "english": {
                            "type": "string",
                            "description": "The translation of the example sentence in English.",
                        },
                    },
                    "additionalProperties": False,
                    "required": ["traditional", "simplified", "pinyin", "english"],
                },
                "category": {
                    "type": "string",
                    "description": "The primary study category for this card.",
                },
                "exclude": {
                    "type": "boolean",
                    "description": (
                        "Whether the word should be excluded or recategorized from the "
                        "provided HSK category."
                    ),
                },
            },
            "required": ["meaning", "example_sentence", "category", "exclude"],
            "additionalProperties": False,
        },
    },
}

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "openai/gpt-6-luna"


def analyze_card(card: Card) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (analysis, metrics) for one card."""
    level = int(card["hsk_level"])

    formatted_word = f"""
        Simplified: {card["simplified"]}
        Traditional: {card["chinese"]}
        Pinyin: {card["pinyin"]}
        English: {card["english_basic"]}
        HSK Level: {card["hsk_level"]}
    """
    started = time.perf_counter()
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        },
        data=json.dumps(
            {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": ANALYSIS_PROMPT},
                    {"role": "user", "content": formatted_word},
                ],
                "response_format": category_output_schema(level),
                "reasoning": {
                    "effort": "low",
                    "exclude": True,
                },
                "usage": {"include": True},
            }
        ),
    )
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    response.raise_for_status()
    payload = response.json()
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected OpenRouter response: {payload}") from exc

    usage = payload.get("usage") or {}
    metrics = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "hsk_level": card["hsk_level"],
        "simplified": card["simplified"],
        "chinese": card["chinese"],
        "pinyin": card["pinyin"],
        "model": payload.get("model") or MODEL,
        "generation_id": payload.get("id"),
        "latency_ms": latency_ms,
        "cost": usage.get("cost"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }
    analysis = json.loads(content)
    return analysis, metrics


def category_output_schema(level: int) -> dict[str, Any]:
    """Build the strict response schema with the card level's category allowlist."""
    schema = copy.deepcopy(OUTPUT_SCHEMA)
    category = schema["json_schema"]["schema"]["properties"]["category"]

    categories = HSK_CATEGORIES.get(level)
    if categories:
        category["enum"] = categories
    else:
        category["type"] = "string"
        category["description"] = "The primary semantic category the word belogs to for grouping related words. ex: 'food', 'family', 'basics'."

    return schema


def append_log(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def prep_row(card: Card, analysis: dict[str, Any]) -> dict[str, Any]:
    """Merge source card + LLM analysis into a ready-to-import row.

    Import hints:
    - exclude: skip linking this word to its HSK level category (may still use categories)
    - categories: extra semantic decks to attach beyond HSK level
    """
    example = analysis["example_sentence"]
    return {
        "hsk_level": card["hsk_level"],
        "simplified": card["simplified"],
        "chinese": card["chinese"],
        "pinyin": card["pinyin"],
        "english_basic": str(analysis["meaning"]).strip()[:255],
        "example_sentence_traditional": example["traditional"],
        "example_sentence_simplified": example["simplified"],
        "example_sentence_pinyin": example["pinyin"],
        "example_sentence_english": example["english"],
        "categories": analysis["category"],
        "exclude": bool(analysis["exclude"]),
    }


def card_key(row: dict[str, Any]) -> tuple[int, str, str, str]:
    """Identity used to resume without re-calling the LLM."""
    return (
        int(row["hsk_level"]),
        str(row["simplified"]),
        str(row["chinese"]),
        str(row["pinyin"]),
    )


def load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"Output file must be a JSON array: {path}")
    return data


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--in",
        dest="in_path",
        type=Path,
        default=DEFAULT_IN,
        help=f"Input cards.json (default: {DEFAULT_IN})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output prepped JSON (default: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N cards (useful for smoke tests)",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=DEFAULT_LOG_DIR,
        help=f"Directory for per-run JSONL logs (default: {DEFAULT_LOG_DIR})",
    )
    args = parser.parse_args(argv)

    if not OPENROUTER_API_KEY:
        raise SystemExit("OPENROUTER_API_KEY is not set")

    in_path = args.in_path.expanduser().resolve()
    out_path = args.out.expanduser().resolve()
    log_dir = args.log_dir.expanduser().resolve()
    if not in_path.is_file():
        raise SystemExit(f"Input not found: {in_path}")

    cards: list[Card] = json.loads(in_path.read_text(encoding="utf-8"))
    if args.limit is not None:
        cards = cards[: args.limit]

    rows = load_rows(out_path)
    done = {card_key(row) for row in rows}
    if done:
        print(f"resuming with {len(done)} cards already in {out_path}")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = log_dir / f"prep_cards_{run_id}.jsonl"
    pending = [card for card in cards if card_key(card) not in done]
    total_cost = 0.0
    total_latency_ms = 0.0

    for index, card in enumerate(pending, start=1):
        analysis, metrics = analyze_card(card)
        rows.append(prep_row(card, analysis))
        # Rewrite after each card so a mid-run failure still leaves usable output.
        write_rows(out_path, rows)
        append_log(log_path, metrics)

        cost = metrics.get("cost")
        if isinstance(cost, (int, float)):
            total_cost += float(cost)
        total_latency_ms += float(metrics["latency_ms"])
        print(
            f"[{index}/{len(pending)}] {card['simplified']} ({card['pinyin']}) "
            f"{metrics['latency_ms']}ms cost={cost}"
        )

    print(
        f"wrote {len(rows)} cards to {out_path} ({len(pending)} newly analyzed); "
        f"run spend=${total_cost:.6f} avg_latency={total_latency_ms / max(len(pending), 1):.1f}ms; "
        f"log={log_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
