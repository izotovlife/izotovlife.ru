# backend/rssfeed/admin.py
# Назначение: регистрация источников RSS в админке и запуск импорта прямо из интерфейса.
# Теперь при ошибках показываются подробные сообщения (HTTP-код, Content-Type, ошибка XML).
# Все ошибки и результаты также пишутся в файл logs/rss_import.log.
# Путь: backend/rssfeed/admin.py

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.utils import timezone
from django.utils.text import slugify
from django.utils.html import format_html

import requests, feedparser, time, re, os, logging
from datetime import datetime, timezone as dt_timezone

from .models import RssFeedSource
from news.models import ImportedNews, Category


# === Логирование ===
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "rss_import.log")

logger = logging.getLogger("rss_import")
if not logger.handlers:
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)


def extract_image(entry):
    """Пытаемся вытащить картинку из RSS-записи."""
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
    """Генерирует уникальный slug для модели (например Category)."""
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
        """Импорт выделенных источников из списка."""
        added, skipped, errors = 0, 0, 0

        for source in queryset:
            try:
                added_count, skipped_count = self._import_feed(source)
                added += added_count
                skipped += skipped_count
                logger.info(f"{source.name}: импорт завершён (добавлено {added_count}, пропущено {skipped_count})")
            except Exception as e:
                errors += 1
                msg = f"Ошибка при импорте {source.name}: {e}"
                self.message_user(request, msg, level=messages.ERROR)
                logger.error(msg)

        self.message_user(
            request,
            f"Импорт завершён: добавлено {added}, пропущено {skipped}, ошибок {errors}.",
            level=messages.SUCCESS if errors == 0 else messages.WARNING
        )

    import_rss_action.short_description = "Импортировать выбранные источники"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:pk>/import/",
                self.admin_site.admin_view(self.import_rss_view),
                name="rssfeed_rssfeedsource_import",
            ),
        ]
        return custom_urls + urls

    def import_rss_view(self, request, pk):
        """Импорт из конкретного источника (по кнопке в списке)."""
        source = self.get_object(request, pk)
        if not source:
            self.message_user(request, "Источник не найден", level=messages.ERROR)
            return redirect("..")

        try:
            added, skipped = self._import_feed(source)
            msg = f"Импорт завершён: {source.name} (добавлено {added}, пропущено {skipped})."
            self.message_user(request, msg, level=messages.SUCCESS)
            logger.info(msg)
        except Exception as e:
            msg = f"Ошибка при импорте {source.name}: {e}"
            self.message_user(request, msg, level=messages.ERROR)
            logger.error(msg)

        return redirect("..")

    def import_link(self, obj):
        """Отдельная кнопка 'Импортировать' в списке."""
        return format_html('<a class="button" href="{}/import/">Импортировать</a>', obj.pk)

    import_link.short_description = "Действие"

    # === Внутренняя логика импорта ===
    def _import_feed(self, source):
        """Загружает новости из одного источника и сохраняет в БД с диагностикой ошибок."""
        try:
            resp = requests.get(source.url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        except requests.RequestException as e:
            raise ValueError(f"Ошибка сети: {e}")

        if resp.status_code != 200:
            raise ValueError(f"Сервер вернул {resp.status_code}")

        content_type = resp.headers.get("Content-Type", "")
        if "xml" not in content_type and "rss" not in content_type:
            raise ValueError(f"Неподдерживаемый Content-Type: {content_type}")

        feed = feedparser.parse(resp.content)

        if feed.bozo:
            raise ValueError(f"Ошибка парсинга RSS: {feed.bozo_exception}")

        if not feed.entries:
            raise ValueError("Лента пустая (нет элементов <item>)")

        source_title = feed.feed.get("title", source.name)

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

            # Категория
            if hasattr(entry, "tags") and entry.tags:
                category_name = entry.tags[0].get("term", "Без категории").strip()
            else:
                category_name = "Без категории"

            slug_value = get_unique_slug(Category, category_name)
            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={"slug": slug_value}
            )

            image_url = extract_image(entry)

            news, created = ImportedNews.objects.get_or_create(
                link=link,
                defaults={
                    "source": source_title,
                    "feed_url": source.url,
                    "title": title,
                    "summary": summary,
                    "image": image_url,
                    "published_at": published_at or timezone.now(),
                    "category": category,
                }
            )

            if created:
                added_count += 1
            else:
                skipped_count += 1

        return added_count, skipped_count
