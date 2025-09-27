# backend/news/management/commands/regenerate_category_slugs.py
# Назначение: Перегенерация slug у категорий. Если slug пустой или равен "bez-kategorii*",
# он заменяется на нормальный латинизированный slug по названию категории.
# Путь: backend/news/management/commands/regenerate_category_slugs.py

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from news.models import Category
import unicodedata
import re


def slugify_unicode(value: str) -> str:
    """Транслитерация + slugify с поддержкой Unicode"""
    value = unicodedata.normalize("NFKD", value)
    return slugify(value, allow_unicode=True)


class Command(BaseCommand):
    help = "Перегенерирует slug категорий из их названий (заменяет bez-kategorii-* на нормальные латинские)."

    def handle(self, *args, **options):
        updated = 0
        skipped = 0

        for cat in Category.objects.all():
            # если slug пустой или кривой "bez-kategorii..."
            if not cat.slug or re.match(r"^bez-kategorii", cat.slug):
                new_slug = slugify_unicode(cat.name)

                if not new_slug:
                    new_slug = "bez-kategorii"

                # гарантируем уникальность
                base_slug = new_slug
                counter = 1
                while Category.objects.exclude(id=cat.id).filter(slug=new_slug).exists():
                    new_slug = f"{base_slug}-{counter}"
                    counter += 1

                old_slug = cat.slug
                cat.slug = new_slug
                cat.save(update_fields=["slug"])
                self.stdout.write(f"Категория '{cat.name}': {old_slug} → {cat.slug}")
                updated += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"Готово! Обновлено: {updated}, пропущено: {skipped}"
        ))
