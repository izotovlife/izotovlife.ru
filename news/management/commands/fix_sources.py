# Путь: backend/news/management/commands/fix_sources.py
# Назначение: задать slug всем источникам (NewsSource), если он пустой.

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from unidecode import unidecode
from news.models import NewsSource

class Command(BaseCommand):
    help = "Генерирует slug для всех NewsSource, у кого он пустой"

    def handle(self, *args, **options):
        fixed = 0
        for src in NewsSource.objects.all():
            if not src.slug:
                base_slug = slugify(unidecode(src.name))[:50]
                new_slug = base_slug
                counter = 1
                while NewsSource.objects.exclude(id=src.id).filter(slug=new_slug).exists():
                    new_slug = f"{base_slug}-{counter}"
                    counter += 1
                src.slug = new_slug
                src.save(update_fields=["slug"])
                self.stdout.write(f"✔ {src.name} → {src.slug}")
                fixed += 1
        self.stdout.write(self.style.SUCCESS(f"✓ Исправлено {fixed} источников"))
