# backend/news/management/commands/fix_category_slugs.py
# Назначение: Пересоздание slug у категорий, перевод кириллицы в латиницу (transliteration).
# Гарантируется уникальность slug, старые некорректные slug перезаписываются.
# Путь: backend/news/management/commands/fix_category_slugs.py

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from unidecode import unidecode
from news.models import Category


class Command(BaseCommand):
    help = "Пересоздание slug у категорий (транслитерация в латиницу, исправление дублей)."

    def handle(self, *args, **options):
        seen = set()
        updated = 0

        for c in Category.objects.all():
            base = slugify(unidecode(c.name))  # кириллица → латиница
            if not base:
                base = "category"
            slug = base
            counter = 1
            while slug in seen or Category.objects.exclude(id=c.id).filter(slug=slug).exists():
                counter += 1
                slug = f"{base}-{counter}"

            old_slug = c.slug
            c.slug = slug
            c.save()
            seen.add(slug)
            updated += 1
            self.stdout.write(self.style.SUCCESS(f"{c.name}: {old_slug} → {c.slug}"))

        self.stdout.write(self.style.SUCCESS(f"✅ Пересоздано slug у {updated} категорий"))
