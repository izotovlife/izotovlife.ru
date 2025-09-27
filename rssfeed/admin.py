# backend/rssfeed/admin.py
# Назначение: регистрация источников RSS в админке и запуск импорта прямо из интерфейса.
# Обновлено:
#   - Используются правильные поля ImportedNews (source_fk, image, feed_url).
#   - Если у новости нет картинки, подставляется logo источника (если есть).

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.utils.text import slugify
from django.utils.html import format_html

import requests, feedparser, time, re, os, logging
from datetime import datetime, timezone as dt_timezone

from .models import RssFeedSource
from news.models import ImportedNews, Category, NewsSource


def extract_image(entry):
    media = entry.get("media_content")
    if media and isinstance(media, list):
        return media[0].get("url")

    enclosure = entry.get("enclosures")
    if enclosure and isinstance(enclosure, list):
        return enclosure[0].get("href")

    if "summary" in entry and "<img" in entry.summary:
        match = re.search(r'<img[^>]+src="([^"]+)"', entry.summary)
        if match:
            return match.group(1)

    return ""


def get_unique_slug(model, name):
    base_slug = slugify(name) or "category"
    slug = base_slug
    counter = 1
    while model.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


@admin.register(RssFeedSource)
class RssFeedSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "created_at", "import_link")
    actions = ["import_rss_action"]

    def import_rss_action(self, request, queryset):
        added, skipped, errors = 0, 0, 0

        for source in queryset:
            try:
                added_count, skipped_count = self._import_feed(source)
                added += added_count
                skipped += skipped_count
            except Exception as e:
                errors += 1
                self.message_user(request, f"Ошибка при импорте {source.name}: {e}", level=messages.ERROR)

        self.message_user(
            request,
            f"Импорт завершён: добавлено {added}, пропущено {skipped}, ошибок {errors}.",
            level=messages.SUCCESS if errors == 0 else messages.WARNING
        )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("<int:pk>/import/", self.admin_site.admin_view(self.import_rss_view), name="rssfeed_rssfeedsource_import"),
        ]
        return custom_urls + urls

    def import_rss_view(self, request, pk):
        source = self.get_object(request, pk)
        if not source:
            self.message_user(request, "Источник не найден", level=messages.ERROR)
            return redirect("..")

        try:
            added, skipped = self._import_feed(source)
            self.message_user(request, f"Импорт завершён: {source.name} (добавлено {added}, пропущено {skipped}).", level=messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Ошибка при импорте {source.name}: {e}", level=messages.ERROR)

        return redirect("..")

    def import_link(self, obj):
        return format_html('<a class="button" href="{}/import/">Импортировать</a>', obj.pk)

    import_link.short_description = "Действие"

    def _import_feed(self, source):
        resp = requests.get(source.url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            raise ValueError(f"Сервер вернул {resp.status_code}")

        feed = feedparser.parse(resp.content)
        if feed.bozo:
            raise ValueError(f"Ошибка парсинга RSS: {feed.bozo_exception}")
        if not feed.entries:
            raise ValueError("Лента пустая")

        source_title = feed.feed.get("title", source.name)
        source_obj, _ = NewsSource.objects.get_or_create(
            name=source_title,
            defaults={"slug": slugify(source_title) or "source"}
        )

        added_count, skipped_count = 0, 0

        for entry in feed.entries:
            title = entry.get("title", "Без заголовка")
            link = entry.get("link")
            if not link:
                continue

            summary = entry.get("summary", "")
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_at = datetime.fromtimestamp(
                    time.mktime(entry.published_parsed),
                    tz=dt_timezone.utc
                )

            if hasattr(entry, "tags") and entry.tags:
                category_name = entry.tags[0].get("term", "Без категории").strip()
            else:
                category_name = "Без категории"

            slug_value = get_unique_slug(Category, category_name)
            category, _ = Category.objects.get_or_create(name=category_name, defaults={"slug": slug_value})

            image_url = extract_image(entry)
            if not image_url and source_obj.logo:
                image_url = source_obj.logo.url

            news, created = ImportedNews.objects.get_or_create(
                link=link,
                defaults={
                    "source_fk": source_obj,
                    "title": title,
                    "summary": summary,
                    "image": image_url,
                    "published_at": published_at or timezone.now(),
                    "category": category,
                    "feed_url": source.url,
                }
            )

            if created:
                added_count += 1
            else:
                skipped_count += 1

        return added_count, skipped_count
