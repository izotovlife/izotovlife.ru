# Путь: backend/news/management/commands/cleanup_trash_news.py
# Назначение: Чистка загруженных новостей от хвостов "Читать далее" и пр.

import re
from django.core.management.base import BaseCommand
from news.models import ImportedNews

TRASH_PATTERNS = [
    r"Читать далее.*?$",
    r"Подробнее.*?$",
    r"Подробности.*?$",
    r"Источник:\s*.+$",
]
TRASH_RE = re.compile("|".join(TRASH_PATTERNS), re.IGNORECASE | re.MULTILINE)


class Command(BaseCommand):
    help = "Удаляет из summary хвосты типа 'Читать далее', 'Подробнее', 'Источник…'."

    def handle(self, *args, **options):
        cleaned_count = 0
        for n in ImportedNews.objects.all():
            old = n.summary or ""
            new = TRASH_RE.sub("", old).strip()
            if new != old:
                n.summary = new or "[Без текста]"
                try:
                    n.save(update_fields=["summary"])
                    cleaned_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Ошибка при сохранении {n.id}: {e}"))
        self.stdout.write(self.style.SUCCESS(f"✓ Очищено {cleaned_count} новостей"))
