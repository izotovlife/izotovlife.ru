# ===========================================
# Назначение файла: Сбор RSS/Atom-лент и синхронизация в модели Item и News
# Путь в проекте: backend/aggregator/tasks.py
# Описание функционала:
#   - Проходит по активным источникам (Source), парсит ленты через feedparser.
#   - Для каждой записи создает/находит Item (контроль дубликатов по (source, link)).
#   - Создает/находит категории news.Category (используем name, а не несуществующий title).
#   - Создает News, если еще не существует (уникальность по link).
# ===========================================

import hashlib
from email.utils import parsedate_to_datetime

from django.utils.text import slugify

from .models import Source, Item
from news.models import News, Category


def _extract_datetime(entry) -> "datetime|None":
    """
    Пытаемся извлечь дату публикации из полей записи.
    feedparser обычно дает 'published'/'updated' как RFC822-строку,
    которую удобно разбирать через email.utils.parsedate_to_datetime.
    """
    # приоритет полей
    dt_candidates = []
    for key in ("published", "updated", "created"):
        if hasattr(entry, key):
            value = getattr(entry, key)
            if isinstance(value, str) and value.strip():
                dt_candidates.append(value)

    for raw in dt_candidates:
        try:
            return parsedate_to_datetime(raw)
        except Exception:
            continue
    return None


def _extract_image_url(entry) -> str:
    """
    Пытаемся достать URL изображения из разных мест записи.
    """
    # media_content (часто у YouTube/медиа)
    if "media_content" in entry:
        try:
            url = entry.media_content[0].get("url", "")
            if url:
                return url
        except Exception:
            pass

    # enclosure или links с image/*
    if hasattr(entry, "enclosures"):
        for enc in entry.enclosures:
            try:
                if enc.get("type", "").startswith("image"):
                    url = enc.get("href", "")
                    if url:
                        return url
            except Exception:
                continue

    if "links" in entry:
        for link in entry.links:
            try:
                if link.get("type", "").startswith("image"):
                    url = link.get("href", "")
                    if url:
                        return url
            except Exception:
                continue

    return ""


def _extract_categories(entry) -> tuple[str, "str|None"]:
    """
    Возвращает (category_name, subcategory_name|None).
    """
    category_name = "Без категории"
    subcategory_name = None

    # tags — самый частый вариант
    if hasattr(entry, "tags") and entry.tags:
        try:
            # первая — как родительская
            category_name = entry.tags[0].get("term") or category_name
            # вторая — как подкатегория
            if len(entry.tags) > 1:
                subcategory_name = entry.tags[1].get("term") or None
        except Exception:
            pass
    # fallback — поле category
    elif hasattr(entry, "category"):
        try:
            if entry.category:
                category_name = str(entry.category)
        except Exception:
            pass

    # нормализуем пустые строки
    category_name = (category_name or "Без категории").strip() or "Без категории"
    if subcategory_name:
        subcategory_name = subcategory_name.strip() or None

    return category_name, subcategory_name


def fetch_feed_for_source(source: Source) -> int:
    """
    Собирает новости из RSS/Atom-источника.
    Создаёт Item + сразу синхронизирует в News.
    Возвращает количество новых Item/News.
    """
    import feedparser

    feed = feedparser.parse(source.url)
    added = 0

    for entry in feed.entries:
        guid = getattr(entry, "id", "") or getattr(entry, "guid", "")
        link = getattr(entry, "link", "")
        if not link:
            continue

        title = (getattr(entry, "title", "") or "")[:500]
        summary = getattr(entry, "summary", getattr(entry, "description", "")) or ""
        author = getattr(entry, "author", "") or ""

        category_name, subcategory_name = _extract_categories(entry)
        published_at = _extract_datetime(entry)

        # Контроль дубликатов для Item (внутренний хеш содержимого)
        content_hash = hashlib.sha1(
            (title + summary + link).encode("utf-8")
        ).hexdigest()

        item, created = Item.objects.get_or_create(
            source=source,
            link=link,
            defaults={
                "guid": guid,
                "title": title,
                "author": author,
                "category": f"{category_name}/{subcategory_name}" if subcategory_name else category_name,
                "published_at": published_at,
                "content_hash": content_hash,
            },
        )

        if not created:
            # уже есть — пропускаем
            continue

        added += 1

        # === Категории news.Category ===
        # ВАЖНО: у Category нет поля 'title', используем 'name'
        parent_category, _ = Category.objects.get_or_create(
            name=category_name,
            defaults={"slug": slugify(category_name)},
        )

        if subcategory_name:
            category, _ = Category.objects.get_or_create(
                name=subcategory_name,
                defaults={"slug": slugify(subcategory_name)},
            )
        else:
            category = parent_category

        # === Новость ===
        # Делаем уникальность по ссылке: если News с таким link уже есть — не создаем
        News.objects.get_or_create(
            link=link,
            defaults={
                "title": title,
                "category": category,
                "source_type": "rss",
                "is_moderated": True,
                "is_popular": False,
            },
        )

    return added


def fetch_all_feeds():
    """
    Проходит по всем активным источникам и собирает новости.
    Возвращает словарь {название источника: число добавленных новостей или "Ошибка: ..."}.
    """
    results = {}
    sources = Source.objects.filter(is_active=True)

    for source in sources:
        try:
            count = fetch_feed_for_source(source)
            results[getattr(source, "title", str(source))] = count
        except Exception as e:
            results[getattr(source, "title", str(source))] = f"Ошибка: {e}"

    return results
