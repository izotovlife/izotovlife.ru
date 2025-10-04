# Путь: backend/news/management/commands/fix_all_slugs.py
# Назначение: чинит slug у NewsSource, Article и ImportedNews.
# Особенности:
#   • Если slug у NewsSource пустой или равен "source" → пересоздаётся из имени.
#   • У ImportedNews slug пересоздаётся если пустой или начинается с "source-".
#   • Article пересоздаётся только если slug пустой.

import uuid
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from unidecode import unidecode
from news.models import Article, ImportedNews, NewsSource


class Command(BaseCommand):
    help = "Фиксит slug у NewsSource, Article и ImportedNews (убирает 'source-')"

    def handle(self, *args, **options):
        updated_sources = 0
        updated_articles = 0
        updated_imported = 0

        # === NewsSource ===
        for src in NewsSource.objects.all():
            if not src.slug or src.slug == "source":
                base_slug = slugify(unidecode(src.name))[:50] or str(uuid.uuid4())[:8]
                new_slug = base_slug
                counter = 1
                while NewsSource.objects.exclude(id=src.id).filter(slug=new_slug).exists():
                    new_slug = f"{base_slug}-{counter}"
                    counter += 1
                self.stdout.write(f"[SOURCE] {src.name} ({src.slug}) → {new_slug}")
                src.slug = new_slug
                src.save(update_fields=["slug"])
                updated_sources += 1

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
                self.stdout.write(f"[ARTICLE] {art.title[:40]} → {art.slug}")
                updated_articles += 1

        # === ImportedNews ===
        for imp in ImportedNews.objects.all():
            regenerate = False
            if not imp.slug:
                regenerate = True
            elif imp.slug.startswith("source-"):
                regenerate = True

            if regenerate:
                base_slug = slugify(unidecode(imp.title))[:50] or str(uuid.uuid4())[:8]
                src_slug = (imp.source_fk.slug if imp.source_fk else None) or "news"
                new_slug = f"{src_slug}-{base_slug}"
                counter = 1
                while ImportedNews.objects.exclude(id=imp.id).filter(slug=new_slug).exists():
                    new_slug = f"{src_slug}-{base_slug}-{counter}"
                    counter += 1
                self.stdout.write(f"[IMPORTED] {imp.slug} → {new_slug}")
                imp.slug = new_slug
                imp.save(update_fields=["slug"])
                updated_imported += 1

        self.stdout.write(self.style.SUCCESS(
            f"✓ Исправлено: {updated_sources} источников, "
            f"{updated_articles} статей, "
            f"{updated_imported} импортированных новостей"
        ))
