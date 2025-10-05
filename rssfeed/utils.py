# Путь: backend/rssfeed/utils.py
# Назначение: Импорт RSS одного источника с проверкой изображений и логированием результатов в базу.

import feedparser
import requests
from dateutil import parser as dtparser
from django.utils import timezone
from news.models import ImportedNews
from news.models_logs import RSSImportLog


def log_rss(source_name: str, message: str, level: str = "INFO"):
    """Записывает лог в базу данных."""
    RSSImportLog.objects.create(source_name=source_name, message=message, level=level)


def safe_image_url(url: str | None, source_name: str = "") -> str | None:
    """
    Проверяет, что ссылка действительно ведёт на доступное изображение.
    Возвращает исходный URL, если картинка существует, иначе None.
    """
    if not url:
        return None
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        content_type = r.headers.get("Content-Type", "").lower()
        if r.status_code < 400 and "image" in content_type:
            return url
        else:
            log_rss(source_name, f"Битая картинка ({r.status_code}): {url}", "WARNING")
    except requests.RequestException as e:
        log_rss(source_name, f"Ошибка проверки картинки: {url} — {e}", "ERROR")
    return None


def import_feed_now(source):
    """
    Импортирует один RSSFeedSource.
    Возвращает количество новых записей.
    """
    parsed = feedparser.parse(source.url)
    imported = 0

    if not parsed.entries:
        log_rss(source.name, f"Пустой фид или ошибка загрузки: {source.url}", "WARNING")

    for entry in parsed.entries:
        link = entry.get("link")
        title = entry.get("title", "").strip()
        summary = entry.get("summary", "")
        published = None

        if "published" in entry:
            try:
                published = dtparser.parse(entry.published)
            except Exception:
                published = timezone.now()

        # Извлекаем и проверяем картинку
        image = None
        if "media_content" in entry and entry.media_content:
            image = entry.media_content[0].get("url")
        elif "links" in entry:
            for l in entry.links:
                if l.get("type", "").startswith("image"):
                    image = l.get("href")
                    break

        image = safe_image_url(image, source.name)

        if not link or not title:
            log_rss(source.name, f"Пропущена запись без ссылки или заголовка", "WARNING")
            continue

        obj, created = ImportedNews.objects.get_or_create(
            link=link,
            defaults={
                "title": title[:500],
                "summary": summary,
                "image": image or "",
                "published_at": published,
                "source": source.name,
                "category": source.category,
            },
        )

        if created:
            imported += 1

    log_rss(source.name, f"Импортировано новых новостей: {imported}", "INFO")
    return imported
