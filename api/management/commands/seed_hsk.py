from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from api.models import Category, Word, WordCategory

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CARDS = ROOT / "data" / "hsk" / "cards.json"


def category_name_for_level(level: int) -> str:
    if level == 7:
        return "HSK 7-9"
    return f"HSK {level}"


class Command(BaseCommand):
    help = "Seed Category and Word rows from data/hsk/cards.json"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=Path,
            default=DEFAULT_CARDS,
            help=f"Path to cards.json (default: {DEFAULT_CARDS})",
        )

    def handle(self, *args, **options):
        path: Path = options["file"].expanduser().resolve()
        if not path.is_file():
            raise CommandError(f"Cards file not found: {path}")

        try:
            cards = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in {path}: {exc}") from exc

        if not isinstance(cards, list):
            raise CommandError("cards.json must be a JSON array")

        created_words = 0
        updated_words = 0
        created_links = 0
        categories: dict[int, Category] = {}

        for index, row in enumerate(cards):
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

            if level not in categories:
                category, _ = Category.objects.get_or_create(name=category_name_for_level(level))
                categories[level] = category

            word, created = Word.objects.get_or_create(
                chinese=chinese,
                pinyin=pinyin,
                defaults={
                    "simplified": simplified,
                    "english_basic": english_basic,
                },
            )
            if created:
                created_words += 1
            else:
                fields: list[str] = []
                if word.simplified != simplified:
                    word.simplified = simplified
                    fields.append("simplified")
                if word.english_basic != english_basic:
                    word.english_basic = english_basic
                    fields.append("english_basic")
                if fields:
                    word.save(update_fields=fields)
                    updated_words += 1

            _, link_created = WordCategory.objects.get_or_create(
                word=word,
                category=categories[level],
            )
            if link_created:
                created_links += 1

        self.stdout.write(
            f"Seeded {len(cards)} cards across {len(categories)} categories: "
            f"created {created_words} words, updated {updated_words}, "
            f"linked {created_links}."
        )
        self.stdout.write(self.style.SUCCESS("Done."))
