# Путь: backend/news/management/commands/cleanup_news.py
# Назначение: Management-команда для удаления "битых" новостей
# (пустые slug, пустое или короткое содержимое).

from django.core.management.base import BaseCommand
from news.utils.cleanup import cleanup_broken_news


class Command(BaseCommand):
    help = "Удаляет битые новости (с пустыми slug или без текста)."

    def handle(self, *args, **options):
        broken = cleanup_broken_news(self.stdout)
        if not broken:
            self.stdout.write(self.style.SUCCESS("✓ Битых новостей не найдено"))
        else:
            self.stdout.write(
                self.style.WARNING(f"✖ Удалено {len(broken)} битых новостей")
            )
