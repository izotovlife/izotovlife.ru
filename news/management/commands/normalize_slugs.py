# Путь: backend/news/management/commands/normalize_slugs.py
# Назначение: Очистка и пересоздание slug для Article и ImportedNews.
# Использование:
#   python manage.py normalize_slugs
#
# Логика:
#   • Article → category.slug + "-" + slugified(title)
#   • ImportedNews → source.slug + "-" + slugified(title) (если есть source)
#   • Если slug меняется → пересохраняем.
#   • Если slug пустой → создаём.
#   • Выводим статистику.

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from unidecode import unidecode

from news.models import Article, ImportedNews


class Command(BaseCommand):
    help = "Нормализует slug для Article и ImportedNews"

    def handle(self, *args, **options):
        fixed_articles = 0
        fixed_imported = 0

        # --- Обработка Article ---
        for art in Article.objects.all():
            base = slugify(unidecode(art.title or ""))[:100]
            prefix = art.categories.first().slug if art.categories.exists() else "news"
            new_slug = f"{prefix}-{base}".strip("-")

            if art.slug != new_slug and new_slug:
                old = art.slug
                art.slug = new_slug
                art.save(update_fields=["slug"])
                fixed_articles += 1
                self.stdout.write(f"[ARTICLE] {old} → {new_slug}")

        # --- Обработка ImportedNews ---
        for imp in ImportedNews.objects.all():
            base = slugify(unidecode(imp.title or ""))[:100]
            prefix = imp.source.slug if getattr(imp, "source", None) else "source"
            new_slug = f"{prefix}-{base}".strip("-")

            if imp.slug != new_slug and new_slug:
                old = imp.slug
                imp.slug = new_slug
                imp.save(update_fields=["slug"])
                fixed_imported += 1
                self.stdout.write(f"[IMPORTED] {old} → {new_slug}")

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Исправлено: {fixed_articles} статей, {fixed_imported} импортированных новостей"
            )
        )
