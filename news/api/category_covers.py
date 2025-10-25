# Путь: backend/news/api/category_covers.py
# Назначение: Батч-эндпоинт /api/categories/covers/ → карта {slug: image_url}.
# Что делает:
#   • Определяет связь с Category (FK или M2M) автоматически.
#   • Выбирает КАРТИНКУ ИЗ САМОЙ ПОПУЛЯРНОЙ публикации категории (Article + ImportedNews вместе).
#   • Популярность = views/hits + 100*rank + 10*comments + 5*likes + 5*shares + бонус свежести (до +200 за <30 дней).
#   • Пропускает заглушки (default_news.svg), пустые URL и АУДИО (mp3/ogg/wav/m4a/aac/flac).
#   • Если нет подходящего изображения — подставляет статический фолбэк:
#         /static/categories/<slug>.(webp|jpg|png) или /static/categories/default.*.
#   • Кэш: per-category (10 мин) + весь ответ (5 мин). Абсолютные URL для корректной загрузки с другого порта.

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple, Optional
from datetime import timedelta

from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.db.models import QuerySet
from django.utils import timezone
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from rest_framework.views import APIView

# Модели проекта
from news.models import Category, Article, ImportedNews  # noqa

# Поля, где может лежать картинка
IMAGE_FIELD_CANDIDATES: tuple[str, ...] = (
    "image",
    "cover_image",
    "preview_image",
    "thumbnail",
    "image_url",
    "thumb",
    "photo",
)

# ⬇️ ДОБАВЛЕНО: список аудио-расширений, которые мы не считаем обложкой
AUDIO_EXTS: tuple[str, ...] = (".mp3", ".ogg", ".oga", ".wav", ".m4a", ".aac", ".flac")

CANDIDATES_LIMIT = 80
FRESH_DAYS = 30


# ---------- Рефлексия полей ----------
def _model_has_field(model, name: str) -> bool:
    return any(getattr(f, "name", None) == name for f in model._meta.get_fields())

def _image_only_fields(model) -> List[str]:
    return [f for f in IMAGE_FIELD_CANDIDATES if _model_has_field(model, f)]

def _category_field_names(model) -> List[str]:
    names: List[str] = []
    for f in model._meta.get_fields():
        rel_model = getattr(f, "related_model", None)
        if rel_model is Category:
            names.append(f.name)
    return names


# ---------- Извлечение изображения ----------
def _first_valid_image_url(obj) -> str:
    """
    Возвращает первый «валидный» URL изображения из набора возможных полей объекта.
    Пропускаем пустые, заглушки default_news.svg и аудио-файлы (mp3, ogg, wav, ...).
    """
    for name in IMAGE_FIELD_CANDIDATES:
        if hasattr(obj, name):
            val = getattr(obj, name)
            if not val:
                continue
            url = getattr(val, "url", val)  # FileField/CharField
            if not url:
                continue
            s = str(url)
            s_low = s.lower().split("?", 1)[0]
            if "default_news.svg" in s_low:
                continue
            # ⬇️ ДОБАВЛЕНО: фильтрация аудио на бэке
            if any(s_low.endswith(ext) for ext in AUDIO_EXTS):
                continue
            return s
    return ""


# ---------- Подсчёт популярности ----------
def _dt(obj, *names) -> Optional[timezone.datetime]:
    for n in names:
        if hasattr(obj, n):
            v = getattr(obj, n)
            if v:
                return v
    return None

def _num(obj, *names) -> int:
    for n in names:
        if hasattr(obj, n):
            try:
                return int(getattr(obj, n) or 0)
            except Exception:
                continue
    return 0

def _popularity_score(obj) -> float:
    views = _num(obj, "views", "hits")
    rank = _num(obj, "rank")
    comments = _num(obj, "comments_count", "comments")
    likes = _num(obj, "likes")
    shares = _num(obj, "shares")

    score = float(views) + 100.0 * rank + 10.0 * comments + 5.0 * likes + 5.0 * shares

    dt = _dt(obj, "published_at", "created_at")
    if dt:
        try:
            now = timezone.now()
            age = (now - dt).total_seconds()
            horizon = float(timedelta(days=FRESH_DAYS).total_seconds())
            freshness = max(0.0, 1.0 - age / horizon)  # 0..1
            score += 200.0 * freshness
        except Exception:
            pass

    return score


# ---------- Кандидаты и выбор ----------
def _order_fields(model) -> Iterable[str]:
    order = []
    if _model_has_field(model, "views"): order.append("-views")
    if _model_has_field(model, "hits"): order.append("-hits")
    if _model_has_field(model, "rank"): order.append("-rank")
    if _model_has_field(model, "comments_count"): order.append("-comments_count")
    elif _model_has_field(model, "comments"): order.append("-comments")
    if _model_has_field(model, "likes"): order.append("-likes")
    if _model_has_field(model, "shares"): order.append("-shares")
    if _model_has_field(model, "published_at"): order.append("-published_at")
    elif _model_has_field(model, "created_at"): order.append("-created_at")
    order.append("-id")
    return order

def _filter_by_category(model, cat: Category) -> QuerySet:
    names = _category_field_names(model)
    if not names:
        return model.objects.none()
    field = names[0]  # FK или M2M — filter(**{field: cat}) сработает
    return model.objects.filter(**{field: cat}).order_by(*_order_fields(model))

def _top_candidates_with_images(model, cat: Category, limit=CANDIDATES_LIMIT) -> List[Tuple[float, str]]:
    qs = _filter_by_category(model, cat)
    fields = _image_only_fields(model)
    if fields:
        qs = qs.only(*fields, "id")
    qs = qs[:limit]

    result: List[Tuple[float, str]] = []
    for obj in qs:
        url = _first_valid_image_url(obj)
        if not url:
            continue
        score = _popularity_score(obj)
        result.append((score, url))
    return result

def choose_best_cover_for_category(cat: Category) -> str:
    try:
        a = _top_candidates_with_images(Article, cat)
    except Exception:
        a = []
    try:
        i = _top_candidates_with_images(ImportedNews, cat)
    except Exception:
        i = []

    best_url = ""
    best_score = -1.0
    for score, url in a + i:
        if score > best_score:
            best_score = score
            best_url = url
    return best_url


# ---------- Фолбэк и вью ----------
def _static_fallback_for_slug(slug: str) -> str:
    candidates = [
        f"categories/{slug}.webp",
        f"categories/{slug}.jpg",
        f"categories/{slug}.png",
        "categories/default.webp",
        "categories/default.jpg",
        "categories/default.png",
    ]
    for rel in candidates:
        if finders.find(rel):
            return static(rel)  # отдаём относительный /static/… — ниже превратим в абсолютный
    return ""

@method_decorator(cache_page(60 * 5), name="dispatch")  # кэш всего ответа на 5 минут
class CategoryCoversView(APIView):
    """GET /api/categories/covers/ → {slug: absolute_image_url_or_static_or_empty}"""
    def get(self, request, *args, **kwargs):
        result: Dict[str, str] = {}
        cats = Category.objects.all().only("id", "slug")

        for cat in cats:
            key = f"category_cover:{cat.slug}"
            url = cache.get(key)
            if url is None:
                try:
                    url = choose_best_cover_for_category(cat) or ""
                except Exception:
                    url = ""
                if not url:
                    url = _static_fallback_for_slug(cat.slug) or ""
                cache.set(key, url, 60 * 10)  # 10 минут

            # Абсолютный URL, чтобы фронт на :3001 подтягивал без CORS/портовых нюансов
            if url and url.startswith("/"):
                url = request.build_absolute_uri(url)

            result[cat.slug] = url

        return JsonResponse(result, safe=True)
