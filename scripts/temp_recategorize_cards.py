"""Reclassify prepped cards to the shared study-category allowlist.

Usage:
  uv run scripts/temp_recategorize_cards.py --limit 20
  uv run scripts/temp_recategorize_cards.py --workers 12
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from hsk_categories import STUDY_CATEGORIES

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IN = ROOT / "data" / "hsk" / "prepped_cards.json"
MODEL = "openai/gpt-6-luna"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

CATEGORY_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "card_category",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": STUDY_CATEGORIES,
                }
            },
            "required": ["category"],
            "additionalProperties": False,
        },
    },
}

SYSTEM_PROMPT = """
You are assigning a Chinese vocabulary card to one shared study category.
Choose the single best-fitting category from the allowed enum. Categories are
shared across HSK levels, so choose by the word's meaning and practical use,
not by its HSK level. Use the English meaning and example sentence as context.
""".strip()


def categorize_card(card: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Return the selected category and request metrics for one card."""
    context = {
        "traditional": card.get("chinese"),
        "meaning": card.get("english_basic"),
        "example_sentence": card.get("example_sentence_simplified"),
    }
    started = time.perf_counter()
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
            ],
            "response_format": CATEGORY_SCHEMA,
            "reasoning": {"effort": "low", "exclude": True},
            "usage": {"include": True},
        },
        timeout=(10, 120),
    )
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    response.raise_for_status()
    payload = response.json()
    try:
        result = json.loads(payload["choices"][0]["message"]["content"])
        category = result["category"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unexpected OpenRouter response: {payload}") from exc

    if category not in STUDY_CATEGORIES:
        raise ValueError(f"Model returned an invalid category: {category!r}")

    usage = payload.get("usage") or {}
    metrics = {
        "latency_ms": latency_ms,
        "cost": usage.get("cost"),
    }
    return category, metrics


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    """Atomically save the current card data."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(path)


def process_cards(
    cards: list[dict[str, Any]],
    all_rows: list[dict[str, Any]],
    out_path: Path,
    workers: int,
) -> tuple[float, float]:
    """Reclassify cards concurrently; checkpoint each successful result."""
    total_cost = 0.0
    total_latency_ms = 0.0
    failed_card: dict[str, Any] | None = None
    failure: Exception | None = None
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(categorize_card, card): card for card in cards}
        for future in as_completed(futures):
            card = futures[future]
            if future.cancelled():
                continue

            try:
                category, metrics = future.result()
            except Exception as exc:
                if failure is None:
                    failed_card = card
                    failure = exc
                    for other in futures:
                        if other is not future:
                            other.cancel()
                continue

            card["categories"] = category
            write_rows(out_path, all_rows)

            cost = metrics.get("cost")
            if isinstance(cost, (int, float)):
                total_cost += float(cost)
            total_latency_ms += float(metrics["latency_ms"])
            completed += 1
            print(
                f"[{completed}/{len(cards)}] {card['simplified']} ({card['pinyin']}) "
                f"{category} {metrics['latency_ms']}ms cost={cost}"
            )

    if failure is not None and failed_card is not None:
        raise SystemExit(
            f"Failed to categorize {failed_card.get('simplified')} "
            f"({failed_card.get('pinyin')}, HSK {failed_card.get('hsk_level')}): {failure}. "
            "Successful in-flight results were saved; rerun to retry unfinished cards."
        )

    return total_cost, total_latency_ms


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="in_path", type=Path, default=DEFAULT_IN)
    parser.add_argument("--out", type=Path, default=None, help="Defaults to updating the input file")
    parser.add_argument("--limit", type=int, default=None, help="Only recategorize the first N cards")
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args(argv)

    if args.workers < 1:
        raise SystemExit("--workers must be at least 1")
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be at least 1")
    if not OPENROUTER_API_KEY:
        raise SystemExit("OPENROUTER_API_KEY is not set")

    in_path = args.in_path.expanduser().resolve()
    out_path = (args.out or in_path).expanduser().resolve()
    if not in_path.is_file():
        raise SystemExit(f"Input not found: {in_path}")

    all_rows = json.loads(in_path.read_text(encoding="utf-8"))
    if not isinstance(all_rows, list):
        raise SystemExit(f"Input file must be a JSON array: {in_path}")

    pending: list[dict[str, Any]] = []
    normalized = 0
    for row in all_rows:
        current = row.get("categories")
        if isinstance(current, str) and current in STUDY_CATEGORIES:
            continue
        if isinstance(current, list) and len(current) == 1 and current[0] in STUDY_CATEGORIES:
            row["categories"] = current[0]
            normalized += 1
        else:
            pending.append(row)

    if args.limit is not None:
        pending = pending[: args.limit]

    if normalized:
        write_rows(out_path, all_rows)
    if not pending:
        print(f"No cards need recategorization; normalized {normalized} category values.")
        return 0

    if out_path == in_path and not normalized:
        backup = in_path.with_suffix(in_path.suffix + ".bak")
        if not backup.exists():
            shutil.copy2(in_path, backup)
            print(f"Created backup: {backup}")

    print(f"Recategorizing {len(pending)} cards with {args.workers} workers.")
    total_cost, total_latency_ms = process_cards(pending, all_rows, out_path, args.workers)
    print(
        f"Recategorized {len(pending)} cards; spend=${total_cost:.6f}; "
        f"avg_latency={total_latency_ms / len(pending):.1f}ms; output={out_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
