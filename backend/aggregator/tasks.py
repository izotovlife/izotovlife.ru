# backend/aggregator/tasks.py

import feedparser
import hashlib
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify

from .models import Source, Item
from news.models import News, Category


def fetch_feed_for_source(source: Source) -> int:
    """
    Собирает новости из RSS/Atom-источника.
    Создаёт Item + сразу синхронизирует в News.
    """
    feed = feedparser.parse(source.url)
    added = 0

    for entry in feed.entries:
        guid = getattr(entry, "id", "") or getattr(entry, "guid", "")
        link = getattr(entry, "link", "")
        title = getattr(entry, "title", "")[:500]
        summary = getattr(entry, "summary", getattr(entry, "description", "")) or title
        author = getattr(entry, "author", "")

        # Категория и подкатегория
        category_name = "Без категории"
        subcategory_name = None
        if hasattr(entry, "tags"):
            if len(entry.tags) > 0:
                category_name = entry.tags[0]["term"]
            if len(entry.tags) > 1:
                subcategory_name = entry.tags[1]["term"]
        elif hasattr(entry, "category"):
            category_name = entry.category

        # Картинка
        image_url = ""
        if "media_content" in entry:
            try:
                image_url = entry.media_content[0].get("url", "")
            except Exception:
                pass
        elif "links" in entry:
            for l in entry.links:
                if l.get("type", "").startswith("image"):
                    image_url = l.get("href")
                    break
        elif hasattr(entry, "enclosures"):
            for enc in entry.enclosures:
                if enc.get("type", "").startswith("image"):
                    image_url = enc.get("href", "")
                    break

        # Дата публикации
        published_at = None
        if hasattr(entry, "published"):
            try:
                published_at = parse_datetime(entry.published)
            except Exception:
                published_at = None

        # Контроль дубликатов
        content_hash = hashlib.sha1(
            (title + summary + link).encode("utf-8")
        ).hexdigest()

        obj, created = Item.objects.get_or_create(
            source=source,
            link=link,
            defaults={
                "guid": guid,
                "title": title,
                "summary": summary,
                "author": author,
                "category": f"{category_name}/{subcategory_name}" if subcategory_name else category_name,
                "image_url": image_url,
                "published_at": published_at,
                "content_hash": content_hash,
            },
        )

        if created:
            added += 1

            # === Категории ===
            parent_category, _ = Category.objects.get_or_create(
                title=category_name,
                defaults={"slug": slugify(category_name)}
            )

            if subcategory_name:
                category, _ = Category.objects.get_or_create(
                    title=subcategory_name,
                    defaults={"slug": slugify(subcategory_name)},
                )
            else:
                category = parent_category

            # === Новость ===
            News.objects.get_or_create(
                link=link,   # лучше уникальность по ссылке
                defaults={
                    "title": title,
                    "content": summary,
                    "image": image_url,
                    "category": category,
                    "is_approved": True,
                    "is_popular": False,
                    "author": None,
                }
            )

    return added


def fetch_all_feeds():
    """
    Проходит по всем активным источникам и собирает новости.
    Возвращает словарь {название источника: число добавленных новостей или ошибка}.
    """
    results = {}
    sources = Source.objects.filter(is_active=True)  # только активные

    for source in sources:
        try:
            count = fetch_feed_for_source(source)
            results[source.title] = count
        except Exception as e:
            results[source.title] = f"Ошибка: {e}"

    return results
