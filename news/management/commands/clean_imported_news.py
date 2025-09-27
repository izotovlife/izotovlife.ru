# backend/news/management/commands/clean_imported_news.py
# Назначение: Очистка уже сохранённых новостей (summary, title) от HTML-тегов,
#             спецсимволов и служебных хвостов типа "Читать далее".
# Путь: backend/news/management/commands/clean_imported_news.py

import re
import html
from django.core.management.base import BaseCommand
from news.models import ImportedNews


def clean_html(raw_html: str) -> str:
    """Удаляем HTML-теги, спецсимволы и хвосты типа 'Читать далее'."""
    text = re.sub(r"<.*?>", "", raw_html or "").strip()
    text = html.unescape(text)

    # убираем "Читать далее", "Подробнее" и подобные хвосты в конце текста
    text = re.sub(r"(Читать далее.*$|Подробнее.*$)", "", text, flags=re.IGNORECASE).strip()

    return text


class Command(BaseCommand):
    help = "Очистка уже сохранённых новостей от HTML-тегов и служебных хвостов"

    def handle(self, *args, **options):
        updated = 0

        for news in ImportedNews.objects.all():
            cleaned_summary = clean_html(news.summary or "")
            cleaned_title = clean_html(news.title or "")

            if news.summary != cleaned_summary or news.title != cleaned_title:
                news.summary = cleaned_summary
                news.title = cleaned_title
                news.save(update_fields=["summary", "title"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Очищено {updated} новостей"))
