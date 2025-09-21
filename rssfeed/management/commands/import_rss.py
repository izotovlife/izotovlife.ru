# backend/rssfeed/management/commands/import_rss.py
# Назначение: Импорт новостей из RSS-источников (заголовок, описание, ссылка, категория, картинка, дата публикации).
# При импорте автоматически создаются новые категории, если их нет. Добавлена диагностика ошибок (пустая/невалидная лента).
# Путь: backend/rssfeed/management/commands/import_rss.py

import feedparser
import re
import time
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from news.models import ImportedNews, Category


def clean_html(raw_html: str) -> str:
    """Удаляем HTML-теги и пробелы из текста"""
    return re.sub(r"<.*?>", "", raw_html or "").strip()


def extract_summary(entry, title: str) -> str:
    """Пробуем вытащить краткое описание разными способами"""
    summary = (
        entry.get("summary")
        or entry.get("description")
        or (
            entry.get("content")[0].get("value")
            if entry.get("content") else ""
        )
    )
    summary = clean_html(summary)

    if not summary:
        # fallback: берём первое предложение из title/content
        content_text = clean_html(entry.get("title", "")) + ". "
        if entry.get("content"):
            content_text += clean_html(entry.get("content")[0].get("value") or "")
        # режем по точке
        sentences = re.split(r"[.!?]", content_text)
        summary = sentences[0].strip() if sentences and sentences[0] else title

    return summary


def extract_image(entry):
    """Пытаемся достать картинку из RSS-элемента."""
    # 1. media:content
    media = entry.get("media_content")
    if media and isinstance(media, list):
        return media[0].get("url")

    # 2. enclosure
    enclosure = entry.get("enclosures")
    if enclosure and isinstance(enclosure, list):
        return enclosure[0].get("href")

    # 3. content:encoded или summary с <img>
    if "summary" in entry and "<img" in entry.summary:
        match = re.search(r'<img[^>]+src="([^"]+)"', entry.summary)
        if match:
            return match.group(1)

    return ""


class Command(BaseCommand):
    help = "Импорт новостей из RSS-ленты"

    def add_arguments(self, parser):
        parser.add_argument("feed_url", type=str, help="URL RSS-ленты")

    def handle(self, *args, **options):
        feed_url = options["feed_url"]
        self.stdout.write(f"Загружаем: {feed_url}")

        feed = feedparser.parse(feed_url)

        # Проверка ошибок парсинга
        if feed.bozo:
            self.stderr.write(self.style.ERROR(
                f"Ошибка при импорте {feed_url}: {feed.bozo_exception}"
            ))
            return

        if not feed.entries:
            self.stderr.write(self.style.ERROR(
                f"Ошибка при импорте {feed_url}: лента пустая"
            ))
            return

        source_title = feed.feed.get("title", "Неизвестный источник")
        added, skipped = 0, 0

        for entry in feed.entries:
            # Заголовок и ссылка
            title = entry.get("title", "Без заголовка").strip()
            link = entry.get("link")
            if not link:
                continue  # пропускаем некорректные записи

            # --- Краткое описание ---
            summary = extract_summary(entry, title)

            # --- Дата публикации ---
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_at = datetime.fromtimestamp(
                    time.mktime(entry.published_parsed),
                    tz=timezone.utc
                )

            # --- Категория ---
            if hasattr(entry, "tags") and entry.tags:
                category_name = entry.tags[0].get("term", "Без категории").strip()
            else:
                category_name = "Без категории"

            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={"slug": slugify(category_name)}
            )

            # --- Картинка ---
            image_url = extract_image(entry)

            # --- Сохраняем новость ---
            news, created = ImportedNews.objects.get_or_create(
                link=link,
                defaults={
                    "source": source_title,
                    "feed_url": feed_url,
                    "title": title,
                    "summary": summary,
                    "image": image_url,
                    "published_at": published_at or timezone.now(),
                    "category": category,
                }
            )

            if created:
                added += 1
                self.stdout.write(self.style.SUCCESS(f"Добавлена новость: {title[:70]}..."))
            else:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"Уже есть: {title[:70]}..."))

        self.stdout.write(self.style.SUCCESS(
            f"Импорт завершён: добавлено {added}, пропущено {skipped}."
        ))
