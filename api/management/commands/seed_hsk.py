from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from api.models import Category, Word, WordCategory

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CARDS = ROOT / "data" / "hsk" / "prepped_cards.json"
REMOTE_CARDS_URL = "https://juzi-data.sfo3.digitaloceanspaces.com/prepped_cards.json"


def category_name_for_level(level: int) -> str:
    if level == 7:
        return "HSK 7-9"
    return f"HSK {level}"


def parse_cards(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, list):
        raise CommandError("Cards data must be a JSON array")

    parsed: list[dict[str, Any]] = []
    for index, row in enumerate(data):
        if not isinstance(row, dict):
            raise CommandError(f"cards[{index}] must be an object")

        try:
            level = int(row["hsk_level"])
            chinese = str(row["chinese"]).strip()
            simplified = str(row["simplified"]).strip()
            pinyin = str(row["pinyin"]).strip()
            english_basic = str(row["english_basic"]).strip()[:255]
        except (KeyError, TypeError, ValueError) as exc:
            raise CommandError(f"cards[{index}] missing/invalid fields: {exc}") from exc

        if level < 1 or not chinese or not simplified or not pinyin or not english_basic:
            raise CommandError(f"cards[{index}] has an empty or invalid required field")

        raw_categories = row.get("categories", [])
        if isinstance(raw_categories, str):
            raw_categories = [raw_categories]
        if not isinstance(raw_categories, list):
            raise CommandError(f"cards[{index}].categories must be a string or array of strings")

        categories: list[str] = []
        for name in raw_categories:
            if not isinstance(name, str) or not name.strip():
                raise CommandError(f"cards[{index}].categories contains an invalid category")
            normalized_name = name.strip()
            if len(normalized_name) > 100:
                raise CommandError(f"cards[{index}] category name exceeds 100 characters")
            if normalized_name not in categories:
                categories.append(normalized_name)

        excluded = row.get("exclude", False)
        if not isinstance(excluded, bool):
            raise CommandError(f"cards[{index}].exclude must be a boolean")

        parsed.append(
            {
                "hsk_level": level,
                "chinese": chinese,
                "simplified": simplified,
                "pinyin": pinyin,
                "english_basic": english_basic,
                "categories": categories,
                "exclude": excluded,
            }
        )
    return parsed


def load_cards(path: Path, url: str | None) -> tuple[list[dict[str, Any]], str]:
    """Prefer the local data file, falling back to the configured remote URL."""
    if path.is_file():
        source = str(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in {path}: {exc}") from exc
        return parse_cards(data), source

    if not url:
        raise CommandError(
            f"Cards file not found: {path}. Set {REMOTE_CARDS_URL} or pass --url to use a remote file."
        )

    try:
        response = requests.get(url, timeout=(10, 60))
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise CommandError(f"Could not download cards from {url}: {exc}") from exc
    except requests.exceptions.JSONDecodeError as exc:
        raise CommandError(f"Remote cards file from {url} is not valid JSON: {exc}") from exc

    return parse_cards(data), url


class Command(BaseCommand):
    help = "Seed words and HSK/study categories from prepped HSK card data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=Path,
            default=DEFAULT_CARDS,
            help=f"Local prepped cards JSON (default: {DEFAULT_CARDS})",
        )
        parser.add_argument(
            "--url",
            default=None,
            help=f"Remote JSON URL fallback (default: ${REMOTE_CARDS_URL})",
        )

    def handle(self, *args, **options):
        path: Path = options["file"].expanduser().resolve()
        url = options["url"] or os.getenv(REMOTE_CARDS_URL)
        cards, source = load_cards(path, url)

        created_words = 0
        updated_words = 0
        created_links = 0
        categories: dict[str, Category] = {}
        used_category_names: set[str] = set()

        with transaction.atomic():
            for row in cards:
                level = row["hsk_level"]
                expected_categories = list(row["categories"])
                if not row["exclude"]:
                    expected_categories.insert(0, category_name_for_level(level))

                word, created = Word.objects.get_or_create(
                    chinese=row["chinese"],
                    pinyin=row["pinyin"],
                    defaults={
                        "simplified": row["simplified"],
                        "english_basic": row["english_basic"],
                    },
                )
                if created:
                    created_words += 1
                else:
                    fields: list[str] = []
                    if word.simplified != row["simplified"]:
                        word.simplified = row["simplified"]
                        fields.append("simplified")
                    if word.english_basic != row["english_basic"]:
                        word.english_basic = row["english_basic"]
                        fields.append("english_basic")
                    if fields:
                        word.save(update_fields=fields)
                        updated_words += 1

                for name in expected_categories:
                    used_category_names.add(name)
                    if name not in categories:
                        category, _ = Category.objects.get_or_create(name=name)
                        categories[name] = category
                    _, link_created = WordCategory.objects.get_or_create(
                        word=word,
                        category=categories[name],
                    )
                    if link_created:
                        created_links += 1

        self.stdout.write(
            f"Seeded {len(cards)} cards from {source} across {len(used_category_names)} categories: "
            f"created {created_words} words, updated {updated_words}, linked {created_links}."
        )
        self.stdout.write(self.style.SUCCESS("Done."))
