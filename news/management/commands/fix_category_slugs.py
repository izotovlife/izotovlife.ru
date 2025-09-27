# Назначение: фиксит slug у категорий, переписывая их транслитерацией (латиница).
# Пример: "Россия" → "rossiia", "Мир" → "mir".
# Путь: backend/news/management/commands/fix_category_slugs.py

import re
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from unidecode import unidecode
from news.models import Category


class Command(BaseCommand):
    help = "Переписывает slug категорий транслитерацией (латиница)"

    def handle(self, *args, **options):
        updated, skipped = 0, 0

        for cat in Category.objects.all():
            if (not cat.slug or
                cat.slug.startswith("bez-kategorii") or
                re.search(r"[а-яА-Я]", cat.slug)):

                # Транслитерация в латиницу + slugify
                translit_name = unidecode(cat.name)
                new_slug = slugify(translit_name) or "category"
                base_slug = new_slug
                counter = 1

                while Category.objects.exclude(id=cat.id).filter(slug=new_slug).exists():
                    new_slug = f"{base_slug}-{counter}"
                    counter += 1

                self.stdout.write(
                    self.style.SUCCESS(f"{cat.name}: {cat.slug} → {new_slug}")
                )

                cat.slug = new_slug
                cat.save(update_fields=["slug"])
                updated += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(f"Готово! Обновлено: {updated}, пропущено: {skipped}")
        )
