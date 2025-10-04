# backend/news/management/commands/regen_slugs.py
# Назначение: Перегенерация slug у Article и ImportedNews в формате SEO.
#   • Article → {category-slug}-{title-slug}
#   • ImportedNews → {source-slug}-{title-slug}
#   • Если slug уже занят → добавляем -1, -2 и т.д.
#   • Дубликаты удаляются автоматически (переписываем slug).

import uuid
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from unidecode import unidecode
from news.models import Article, ImportedNews


def unique_slug(model, base_slug, exclude_id=None):
    """Генерация уникального slug с добавлением -1, -2 и т.д."""
    new_slug = base_slug
    counter = 1
    qs = model.objects.exclude(id=exclude_id)
    while qs.filter(slug=new_slug).exists():
        new_slug = f"{base_slug}-{counter}"
        counter += 1
    return new_slug


class Command(BaseCommand):
    help = "Перегенерация slug для Article и ImportedNews с учётом категории/источника"

    def handle(self, *args, **options):
        updated = 0

        # --- Обновляем Article ---
        for art in Article.objects.all():
            base_slug = slugify(unidecode(art.title))[:50] or str(uuid.uuid4())[:8]
            cat_slug = art.categories.first().slug if art.categories.exists() else "news"
            new_slug = f"{cat_slug}-{base_slug}"
            new_slug = unique_slug(Article, new_slug, exclude_id=art.id)

            if art.slug != new_slug:
                art.slug = new_slug
                art.save(update_fields=["slug"])
                self.stdout.write(self.style.SUCCESS(f"[Article] {art.id} → {new_slug}"))
                updated += 1

        # --- Обновляем ImportedNews ---
        for imp in ImportedNews.objects.all():
            base_slug = slugify(unidecode(imp.title))[:50] or str(uuid.uuid4())[:8]
            src_slug = getattr(imp.source_fk, "slug", None) or "source"
            new_slug = f"{src_slug}-{base_slug}"
            new_slug = unique_slug(ImportedNews, new_slug, exclude_id=imp.id)

            if imp.slug != new_slug:
                imp.slug = new_slug
                imp.save(update_fields=["slug"])
                self.stdout.write(self.style.SUCCESS(f"[ImportedNews] {imp.id} → {new_slug}"))
                updated += 1

        self.stdout.write(self.style.NOTICE(f"✓ Slugs regenerated. Updated: {updated} records"))
