# backend/rssfeed/management/commands/fix_empty_summaries.py
# Назначение: Дополнение пустых summary у импортированных новостей.
# Финальный вариант:
#   - requests с таймаутом (3 сек на соединение, 5 сек на чтение)
#   - читаем только первые 200 КБ
#   - feedparser выполняется в ThreadPoolExecutor с таймаутом 5 секунд
#   - аргументы --limit и --dry-run
#   - прогресс каждые 50 новостей
# Путь: backend/rssfeed/management/commands/fix_empty_summaries.py

import re
import html
import requests
import feedparser
import concurrent.futures
from django.core.management.base import BaseCommand
from django.db.models import Q
from news.models import ImportedNews


def clean_html(raw_html: str) -> str:
    """Удаляем HTML-теги и преобразуем спецсимволы (&amp; → &)."""
    text = re.sub(r"<.*?>", "", raw_html or "").strip()
    return html.unescape(text)


def make_summary_from_text(title: str, description: str = "", content: str = "") -> str:
    """Формируем fallback-текст, если summary пустое."""
    base = clean_html(title) + ". "
    if description:
        base += clean_html(description)
    if content:
        base += " " + clean_html(content)
    base = re.sub(r"\s+", " ", base).strip()
    return (base[:200] + "...") if len(base) > 200 else base


def safe_parse(content: bytes, timeout: int = 5):
    """Безопасный вызов feedparser.parse с таймаутом."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(feedparser.parse, content)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return None


class Command(BaseCommand):
    help = "Заполняет пустые summary у импортированных новостей"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Максимальное количество новостей для обработки (по умолчанию все)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только показать, какие summary будут изменены, без сохранения",
        )

    def handle(self, *args, **options):
        limit = options.get("limit")
        dry_run = options.get("dry_run")

        qs = ImportedNews.objects.filter(Q(summary__isnull=True) | Q(summary__exact=""))
        total = qs.count()

        if not total:
            self.stdout.write(self.style.SUCCESS("✅ Нет новостей с пустым summary."))
            return

        if limit:
            qs = qs[:limit]
            self.stdout.write(self.style.WARNING(f"Обработка ограничена {limit} новостями."))

        self.stdout.write(self.style.WARNING(f"Найдено {total} новостей с пустым summary. Начинаем обработку..."))

        updated = 0
        processed = 0

        for news in qs.iterator():
            processed += 1
            try:
                summary = ""

                if news.feed_url:
                    try:
                        resp = requests.get(news.feed_url, timeout=(3, 5), stream=True)
                        resp.raise_for_status()
                        # читаем только первые 200 КБ
                        content = resp.raw.read(200_000, decode_content=True)
                        feed = safe_parse(content, timeout=5)
                    except Exception as e:
                        self.stderr.write(self.style.WARNING(f"Не удалось загрузить RSS {news.feed_url}: {e}"))
                        feed = None

                    if feed:
                        found_entry = None
                        for entry in feed.entries:
                            if entry.get("link") == news.link:
                                found_entry = entry
                                break

                        if found_entry:
                            summary = (
                                found_entry.get("summary")
                                or found_entry.get("description")
                                or (
                                    found_entry.get("content")[0].get("value")
                                    if found_entry.get("content") else ""
                                )
                            )
                            summary = clean_html(summary)

                            if not summary:
                                summary = make_summary_from_text(
                                    news.title,
                                    found_entry.get("description", ""),
                                    found_entry.get("content")[0].get("value") if found_entry.get("content") else ""
                                )

                # fallback без RSS или неудачи
                if not summary:
                    summary = make_summary_from_text(news.title)

                if dry_run:
                    self.stdout.write(f"👉 [dry-run] {news.id}: {summary[:80]}...")
                else:
                    news.summary = summary
                    news.save(update_fields=["summary"])
                    updated += 1

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Ошибка при обработке {news.id}: {e}"))

            # каждые 50 новостей показываем прогресс
            if processed % 50 == 0:
                self.stdout.write(f"Обработано {processed}/{limit or total}...")

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"✅ Dry-run завершён. Всего проверено {limit or total} новостей."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Готово! Исправлено {updated} из {limit or total} новостей."))
