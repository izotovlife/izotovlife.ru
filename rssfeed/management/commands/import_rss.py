# backend/rssfeed/management/commands/import_rss.py
# Назначение: Импорт новостей из RSS-источников (заголовок, ссылка, дата, картинка, категория, текст/summary).
# Особенности и обновления:
#   • Сохранение абзацов при очистке HTML (перевод <p>/<br> в \n, потом удаление тегов).
#   • Умный фолбэк, если из RSS пришла пустота: загрузка HTML-страницы и извлечение текста
#     (meta description, og:description, первые <p> основной статьи).
#   • Порог качества: MIN_SUMMARY_CHARS и MIN_PARAGRAPHS — не сохраняем «пустышки».
#   • Безопасная работа с разными именами полей в ImportedNews (image/image_url/cover_image).
#   • Нормализация ссылок (обрезаем UTM и хвосты трекинга).
#   • Ничего не удалено из прежней логики: feedparser, Category/NewsSource поддержаны.
# Путь: backend/rssfeed/management/commands/import_rss.py

import feedparser
import re
import time
import html
from datetime import datetime
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import requests
from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from django.db import transaction

from news.models import ImportedNews, Category, NewsSource


# --- ПАРАМЕТРЫ КАЧЕСТВА / СЕТИ ------------------------------------------------

REQUEST_TIMEOUT = 8  # сек — не зависаем на вечность
MIN_SUMMARY_CHARS = 120  # хотя бы 120 символов осмысленного текста
MIN_PARAGRAPHS = 1       # хотя бы 1 абзац
MAX_SUMMARY_CHARS = 1200 # подрежем слишком длинное превью (summary)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Частые «хвосты» для удаления из ссылки
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "yclid", "fbclid", "gclid", "utm_referrer", "utm_name"
}

# Фразы-шумы, которые стоит чистить из текста
TRASH_PATTERNS = [
    r"Читать далее.*?$",
    r"Подробнее.*?$",
    r"Подробности.*?$",
    r"Источник:\s*.+$",
]
TRASH_RE = re.compile("|".join(TRASH_PATTERNS), re.IGNORECASE | re.MULTILINE)


# --- УТИЛИТЫ ОЧИСТКИ ТЕКСТА ---------------------------------------------------

def strip_tracking_params(url: str) -> str:
    """Удаляем UTM и прочие трекинговые параметры, не меняя остальное."""
    try:
        parsed = urlparse(url)
        if not parsed.query:
            return url
        qs = dict(parse_qsl(parsed.query, keep_blank_values=True))
        qs = {k: v for k, v in qs.items() if k not in TRACKING_PARAMS}
        new_query = urlencode(qs, doseq=True)
        return urlunparse(parsed._replace(query=new_query))
    except Exception:
        return url


def html_to_text_preserve_paragraphs(raw_html: str) -> str:
    """
    Переводим <p>/<br> в переносы строк, убираем остальное,
    нормализуем пробелы, возвращаем человекочитаемый текст.
    """
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "lxml")

    # Заменяем <br> на '\n'
    for br in soup.find_all(["br"]):
        br.replace_with("\n")

    # Ставим '\n\n' между блоковыми абзацами
    for p in soup.find_all(["p", "div", "li"]):
        if p.text:
            p.insert_after(soup.new_string("\n"))

    text = soup.get_text(separator="\n")
    text = html.unescape(text)
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)              # лишние пробелы
    text = re.sub(r"\n{3,}", "\n\n", text).strip()   # много переносов → два

    # Чистим хвосты «Подробнее…»
    text = TRASH_RE.sub("", text).strip()
    return text


def first_paragraphs(text: str, max_chars: int = MAX_SUMMARY_CHARS) -> str:
    """Оставляем первые 1–3 абзаца, ограничиваем длину."""
    if not text:
        return ""
    parts = [p.strip() for p in text.split("\n") if p.strip()]
    if not parts:
        return ""
    # Берём первые абзацы, пока не превысим лимит
    picked = []
    total = 0
    for p in parts:
        if total and total + len(p) + 2 > max_chars:
            break
        picked.append(p)
        total += len(p) + 2
        if len(picked) >= 3:
            break
    result = "\n\n".join(picked).strip()
    return result[:max_chars].rstrip()


# --- ИЗВЛЕЧЕНИЕ ИЗ RSS-ЭЛЕМЕНТОВ ----------------------------------------------

def extract_link(entry) -> str:
    for key in ("link", "id", "href"):
        url = getattr(entry, key, None) or entry.get(key)
        if url:
            return strip_tracking_params(url)
    return ""


def extract_title(entry) -> str:
    for key in ("title",):
        val = getattr(entry, key, None) or entry.get(key)
        if val:
            return html.unescape(BeautifulSoup(val, "lxml").get_text(" ").strip())
    return ""


def extract_raw_html_from_entry(entry) -> str:
    """
    Пытаемся достать «богатый» HTML: content:encoded → content[0].value → summary/detail.
    """
    # feedparser кладёт content:encoded в entry.get('content')[0].value
    if entry.get("content"):
        try:
            return entry["content"][0].get("value") or ""
        except Exception:
            pass
    # summary_detail.value
    if entry.get("summary_detail") and entry["summary_detail"].get("value"):
        return entry["summary_detail"]["value"]
    # summary
    if entry.get("summary"):
        return entry["summary"]
    # description
    if entry.get("description"):
        return entry["description"]
    return ""


def extract_image_from_entry(entry) -> str:
    """
    Пытаемся достать картинку из enclosures/media/thumbnails.
    """
    # media:content
    media_content = entry.get("media_content") or entry.get("media:content")
    if media_content:
        if isinstance(media_content, list) and media_content:
            url = media_content[0].get("url") or media_content[0].get("@url")
            if url:
                return url
        if isinstance(media_content, dict):
            url = media_content.get("url") or media_content.get("@url")
            if url:
                return url

    # enclosure
    if entry.get("enclosures"):
        for enc in entry["enclosures"]:
            url = enc.get("url")
            if url and (enc.get("type", "").startswith("image") or url.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))):
                return url

    # thumbnail
    thumb = entry.get("media_thumbnail") or entry.get("media:thumbnail")
    if thumb:
        if isinstance(thumb, list) and thumb:
            url = thumb[0].get("url") or thumb[0].get("@url")
            if url:
                return url
        if isinstance(thumb, dict):
            url = thumb.get("url") or thumb.get("@url")
            if url:
                return url

    return ""


def extract_published(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        if entry.get(key):
            try:
                # time.struct_time → aware datetime в UTC
                ts = time.mktime(entry[key])
                return timezone.make_aware(datetime.fromtimestamp(ts), timezone=timezone.utc)
            except Exception:
                pass
    return None


def extract_category(entry) -> str:
    # Берём первый тег из entry.tags, если есть
    tags = entry.get("tags") or []
    if tags:
        tag0 = tags[0]
        label = tag0.get("label") or tag0.get("term")
        if label:
            return label.strip()
    # Фолбэк
    return "Лента новостей"


# --- ФОЛБЭК: ЗАГРУЗКА СТРАНИЦЫ И ВЫТАСКИВАНИЕ ТЕКСТА/КАРТИНКИ -----------------

def fetch_page(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT})
        if resp.status_code != 200 or not resp.text:
            return None
        return BeautifulSoup(resp.text, "lxml")
    except Exception:
        return None


def page_extract_text(soup: BeautifulSoup) -> str:
    if not soup:
        return ""
    # 1) meta description / og:description
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        txt = md["content"].strip()
        if txt:
            return txt

    ogd = soup.find("meta", attrs={"property": "og:description"})
    if ogd and ogd.get("content"):
        txt = ogd["content"].strip()
        if txt:
            return txt

    # 2) Пытаемся найти основной блок статьи
    candidates = []
    for attr, val in (("id", "article"), ("id", "content"), ("class_", "article"), ("class_", "content"), ("class_", "post")):
        try:
            if attr == "id":
                node = soup.find(attrs={"id": re.compile(val, re.I)})
            else:
                node = soup.find(attrs={"class": re.compile(val, re.I)})
            if node:
                candidates.append(node)
        except Exception:
            pass
    # если кандидатов нет — берём просто <article> или основной <div>
    if not candidates:
        candidates = soup.find_all("article") or [soup.body]

    for node in candidates:
        if not node:
            continue
        # Берём первые 3 абзаца
        ps = [p.get_text(" ", strip=True) for p in node.find_all("p")]
        ps = [p for p in ps if p and len(p) > 40]  # отсечь короткие подписи
        if ps:
            text = "\n\n".join(ps[:3]).strip()
            if text:
                return text

    return ""


def page_extract_image(soup: BeautifulSoup) -> str:
    if not soup:
        return ""
    og = soup.find("meta", attrs={"property": "og:image"})
    if og and og.get("content"):
        return og["content"].strip()
    tw = soup.find("meta", attrs={"name": "twitter:image"})
    if tw and tw.get("content"):
        return tw["content"].strip()
    # Первое <img> в статье
    art = soup.find("article")
    if art:
        img = art.find("img")
    else:
        img = soup.find("img")
    if img and img.get("src"):
        return img["src"].strip()
    return ""


# --- ВСПОМОГАТЕЛЬНОЕ: СОХРАНЕНИЕ С УЧЁТОМ ПОЛЕЙ МОДЕЛИ ------------------------

def model_has_field(model, field_name: str) -> bool:
    return any(getattr(f, "name", "") == field_name for f in model._meta.get_fields())


def assign_if_exists(instance, **kwargs):
    """Безопасно присваиваем поля, только если они действительно есть у модели."""
    for k, v in kwargs.items():
        if model_has_field(instance.__class__, k):
            setattr(instance, k, v)


# --- ОСНОВНАЯ ЛОГИКА -----------------------------------------------------------

class Command(BaseCommand):
    help = "Импорт новостей из RSS с безопасной очисткой текста и фолбэком на парсинг страницы."

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            nargs="*",
            help="Ограничить импорт конкретными источниками по слагу NewsSource (например: ria-novosti tass lenta-ru).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        only_slugs = set(options.get("only") or [])
        sources = list(NewsSource.objects.filter(is_active=True).order_by("name"))
        if only_slugs:
            sources = [s for s in sources if s.slug in only_slugs]

        if not sources:
            self.stdout.write(self.style.WARNING("Нет активных источников NewsSource."))
            return

        total_new, total_skipped = 0, 0

        for src in sources:
            if not src.feed_url:
                self.stdout.write(self.style.WARNING(f"✖ Пропущен '{src.name}': нет feed_url"))
                continue

            self.stdout.write(self.style.NOTICE(f"→ Импорт из {src.name} ({src.feed_url})"))

            try:
                feed = feedparser.parse(src.feed_url)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Ошибка парсинга: {e}"))
                continue

            if not feed or not feed.get("entries"):
                self.stdout.write(self.style.WARNING("  В ленте нет записей."))
                continue

            added, skipped = 0, 0

            for entry in feed["entries"]:
                try:
                    link = extract_link(entry)
                    if not link:
                        skipped += 1
                        continue

                    title = extract_title(entry)
                    raw_html = extract_raw_html_from_entry(entry)
                    img_from_feed = extract_image_from_entry(entry)
                    published_dt = extract_published(entry) or timezone.now()

                    # 1) Очищаем HTML из RSS, но сохраняем абзацы
                    text = html_to_text_preserve_paragraphs(raw_html)
                    text = first_paragraphs(text, MAX_SUMMARY_CHARS)

                    # 2) Если пусто — фолбэк: грузим страницу и вытаскиваем оттуда
                    if (len(text) < MIN_SUMMARY_CHARS) or (len([p for p in text.split("\n") if p.strip()]) < MIN_PARAGRAPHS):
                        soup = fetch_page(link)
                        fallback_txt = page_extract_text(soup)
                        fallback_txt = html_to_text_preserve_paragraphs(fallback_txt)
                        fallback_txt = first_paragraphs(fallback_txt, MAX_SUMMARY_CHARS)
                        if len(fallback_txt) >= len(text):
                            text = fallback_txt
                        # картинка со страницы, если из RSS не пришла
                        if not img_from_feed:
                            img_from_page = page_extract_image(soup)
                            if img_from_page:
                                img_from_feed = img_from_page

                    # 3) Ещё раз проверим пороги качества
                    para_count = len([p for p in (text or "").split("\n") if p.strip()])
                    if not text or len(text) < MIN_SUMMARY_CHARS or para_count < MIN_PARAGRAPHS:
                        skipped += 1
                        self.stdout.write(self.style.WARNING(
                            f"  — Пропуск: «{title[:60]}…» (малый текст: {len(text)} симв., {para_count} абз.)"
                        ))
                        continue

                    # Категория
                    cat_name = extract_category(entry).strip() or "Лента новостей"
                    cat_slug = slugify(cat_name) or "lenta-novostei"
                    category, _ = Category.objects.get_or_create(slug=cat_slug, defaults={"name": cat_name})

                    # Ищем дубль по ссылке
                    existing = ImportedNews.objects.filter(link=link).first()
                    if existing:
                        # Обновим только то, что безопасно
                        assign_if_exists(existing, summary=text)
                        if img_from_feed:
                            # безопасно запишем, как бы ни называлось поле
                            if model_has_field(ImportedNews, "image"):
                                assign_if_exists(existing, image=img_from_feed)
                            elif model_has_field(ImportedNews, "image_url"):
                                assign_if_exists(existing, image_url=img_from_feed)
                            elif model_has_field(ImportedNews, "cover_image"):
                                assign_if_exists(existing, cover_image=img_from_feed)
                        assign_if_exists(existing, category=category, source=src, published_at=published_dt)
                        existing.save(update_fields=[f.name for f in existing._meta.fields if f.name not in ("id",)])
                        continue  # дубль не считаем «added»

                    # Создаём запись. Соберём поля динамически.
                    news = ImportedNews()
                    assign_if_exists(news, title=title)
                    assign_if_exists(news, summary=text)
                    assign_if_exists(news, link=link)
                    assign_if_exists(news, category=category)
                    assign_if_exists(news, source=src)
                    assign_if_exists(news, published_at=published_dt)

                    if img_from_feed:
                        if model_has_field(ImportedNews, "image"):
                            assign_if_exists(news, image=img_from_feed)
                        elif model_has_field(ImportedNews, "image_url"):
                            assign_if_exists(news, image_url=img_from_feed)
                        elif model_has_field(ImportedNews, "cover_image"):
                            assign_if_exists(news, cover_image=img_from_feed)

                    news.save()
                    added += 1

                except Exception as e:
                    skipped += 1
                    self.stdout.write(self.style.ERROR(f"  Ошибка по записи: {e}"))

            total_new += added
            total_skipped += skipped
            self.stdout.write(self.style.SUCCESS(f"  ✓ Добавлено: {added}  |  Пропущено: {skipped}"))

        self.stdout.write(self.style.SUCCESS(f"ГОТОВО. Всего добавлено: {total_new}, пропущено: {total_skipped}"))
