# Назначение: Объединяет дублирующиеся категории (по slug без префиксов/цифр),
# переносит все статьи и импортированные новости в одну категорию.
# Путь: backend/news/management/commands/merge_duplicate_categories.py

import re
from django.core.management.base import BaseCommand
from news.models import Category, Article, ImportedNews


def normalize_slug(slug: str) -> str:
    """Убираем числовые префиксы и лишние дефисы, чтобы найти дубли."""
    return re.sub(r"^\d+-*", "", slug).strip().lower()


class Command(BaseCommand):
    help = "Объединяет дублирующиеся категории (оставляет одну основную)."

    def handle(self, *args, **options):
        categories = Category.objects.all()
        groups = {}

        # Группируем по "нормализованному slug"
        for cat in categories:
            norm = normalize_slug(cat.slug)
            groups.setdefault(norm, []).append(cat)

        merged_count = 0

        for norm, cats in groups.items():
            if len(cats) > 1:
                main = cats[0]  # оставляем первую как основную
                duplicates = cats[1:]

                self.stdout.write(
                    self.style.WARNING(
                        f"Найдены дубликаты для slug '{norm}': {[c.name for c in cats]}"
                    )
                )

                for dup in duplicates:
                    # переносим статьи
                    for article in Article.objects.filter(categories=dup):
                        article.categories.add(main)

                    # переносим импортированные новости
                    ImportedNews.objects.filter(category=dup).update(category=main)

                    self.stdout.write(f" → Перенос: {dup.name} → {main.name}")
                    dup.delete()
                    merged_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Объединение завершено. Удалено дублей: {merged_count}")
        )
