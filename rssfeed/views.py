# backend/rssfeed/views.py
# Назначение: Вью для запуска импорта RSS из админки.
# Путь: backend/rssfeed/views.py

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
import feedparser
import re

from news.models import ImportedNews, Category
from .models import RssFeedSource


def extract_image(entry):
    """Достаём картинку из RSS-элемента."""
    media = entry.get("media_content")
    if media and isinstance(media, list):
        url = media[0].get("url")
        if url:
            return url

    enclosure = entry.get("enclosures")
    if enclosure and isinstance(enclosure, list):
        url = enclosure[0].get("url")
        if url:
            return url

    summary = entry.get("summary", "")
    match = re.search(r'<img[^>]+src="([^"]+)"', summary)
    if match:
        return match.group(1)

    return ""


def import_rss_source(request, pk):
    """
    Импорт новостей из выбранного источника RSS (в админке).
    """
    source = get_object_or_404(RssFeedSource, pk=pk)
    feed = feedparser.parse(source.url)

    created_count = 0
    for entry in feed.entries:
        link = entry.get("link")
        if ImportedNews.objects.filter(link=link).exists():
            continue

        title = entry.get("title")
        summary = entry.get("summary", "")

        # Категория из RSS (если нет — "Общее")
        cat_name = None
        if hasattr(entry, "tags") and entry.tags:
            cat_name = entry.tags[0].get("term")
        if not cat_name:
            cat_name = "Общее"

        category, _ = Category.objects.get_or_create(
            name=cat_name,
            defaults={"slug": cat_name.lower().replace(" ", "-")},
        )

        ImportedNews.objects.create(
            title=title,
            summary=summary,
            link=link,
            source=feed.feed.get("title", source.name),
            published_at=timezone.now(),
            category=category,
            image=extract_image(entry),
        )
        created_count += 1

    messages.success(request, f"Импортировано {created_count} новостей из {source.name}")
    return redirect(reverse("admin:rssfeed_rssfeedsource_changelist"))

