# backend/news/management/commands/clean_categories.py
# Назначение: Чистка категорий от числовых префиксов, объединение дубликатов и перенос статей.
# Путь: backend/news/management/commands/clean_categories.py

import re
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from news.models import Category, Article


class Command(BaseCommand):
    help = "Удаляет числовые префиксы у категорий и объединяет дубликаты"

    def handle(self, *args, **options):
        updated, merged = 0, 0

        for cat in Category.objects.all():
            clean_name = re.sub(r"^\d+\s*", "", cat.name).strip()
            if not clean_name:  # если строка пустая после очистки
                clean_name = "Без категории"

            # если имя не изменилось — пропускаем
            if clean_name == cat.name:
                continue

            # если уже есть такая категория → переносим статьи
            try:
                existing = Category.objects.exclude(id=cat.id).get(name=clean_name)
            except Category.DoesNotExist:
                existing = None

            if existing:
                # переносим статьи
                articles = Article.objects.filter(categories=cat)
                for art in articles:
                    art.categories.add(existing)
                    art.categories.remove(cat)

                self.stdout.write(
                    self.style.WARNING(
                        f"Объединена категория {cat.name} → {existing.name}"
                    )
                )
                cat.delete()
                merged += 1
            else:
                old_name = cat.name
                cat.name = clean_name
                cat.slug = slugify(clean_name)
                cat.save(update_fields=["name", "slug"])
                self.stdout.write(
                    self.style.SUCCESS(f"Переименована {old_name} → {clean_name}")
                )
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово! Обновлено: {updated}, объединено: {merged}"
            )
        )
