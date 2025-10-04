# Путь: backend/news/management/commands/fix_imported_slugs.py
# Назначение: починить slug у ImportedNews (убрать префикс источника).
# Команда: python manage.py fix_imported_slugs

from django.core.management.base import BaseCommand
from news.models import ImportedNews
from django.utils.text import slugify
from unidecode import unidecode

class Command(BaseCommand):
    help = "Фиксирует slug у ImportedNews (убирает source- / rt- и т.п., оставляя чистый slug по title)."

    def handle(self, *args, **options):
        count = 0
        for n in ImportedNews.objects.all():
            # slug без source-slug
            base_slug = slugify(unidecode(n.title))[:50] or str(n.id)
            new_slug = base_slug

            # проверка уникальности
            counter = 1
            while ImportedNews.objects.exclude(id=n.id).filter(slug=new_slug).exists():
                new_slug = f"{base_slug}-{counter}"
                counter += 1

            if n.slug != new_slug:
                self.stdout.write(f"⚡ Fix slug {n.id}: {n.slug} → {new_slug}")
                n.slug = new_slug
                n.save(update_fields=["slug"])
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Готово! Исправлено {count} slug."))
