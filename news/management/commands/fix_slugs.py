# Путь: backend/news/management/commands/fix_slugs.py
# Назначение: пересоздание slug для Article и ImportedNews,
# удаление "source-" из старых slug, генерация уникальных SEO-friendly slug.

import uuid
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from unidecode import unidecode
from news.models import Article, ImportedNews


class Command(BaseCommand):
    help = "Пересоздаёт slug для Article и ImportedNews (убирает 'source-')"

    def handle(self, *args, **options):
        updated = 0

        # === Article ===
        for art in Article.objects.all():
            if not art.slug:
                base_slug = slugify(unidecode(art.title))[:50] or str(uuid.uuid4())[:8]
                cat_slug = art.categories.first().slug if art.categories.exists() else "news"
                new_slug = f"{cat_slug}-{base_slug}"
                counter = 1
                while Article.objects.exclude(id=art.id).filter(slug=new_slug).exists():
                    new_slug = f"{cat_slug}-{base_slug}-{counter}"
                    counter += 1
                art.slug = new_slug
                art.save(update_fields=["slug"])
                updated += 1

        # === ImportedNews ===
        for imp in ImportedNews.objects.all():
            regenerate = False

            # 1) Если slug пустой
            if not imp.slug:
                regenerate = True

            # 2) Если slug начинается с "source-"
            elif imp.slug.startswith("source-"):
                regenerate = True

            if regenerate:
                base_slug = slugify(unidecode(imp.title))[:50] or str(uuid.uuid4())[:8]
                src_slug = imp.source_fk.slug if imp.source_fk else "news"  # ✅ заменили fallback
                new_slug = f"{src_slug}-{base_slug}"
                counter = 1
                while ImportedNews.objects.exclude(id=imp.id).filter(slug=new_slug).exists():
                    new_slug = f"{src_slug}-{base_slug}-{counter}"
                    counter += 1
                self.stdout.write(f"✔ {imp.slug} → {new_slug}")
                imp.slug = new_slug
                imp.save(update_fields=["slug"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"✓ Slugs updated for {updated} records"))
