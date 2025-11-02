# Путь: backend/news/views_related.py
# Назначение: Эндпоинт «Похожие новости» с толерантным входом (slug ИЛИ id), расширенным поиском
#             и безопасными фолбэками. Работает и с Article, и с ImportedNews.
#
# Что внутри (полный файл):
# - canon_slug(): канонизация спорных слагов (obschestvo→obshchestvo и т.п.)
# - resolve_base_by_id/slug(): ищем опорную запись в Article/ImportedNews по id/slug/seo_slug/url_slug
# - build_candidates(): собираем пул кандидатов (та же категория, общие теги, та же доменная зона источника, свежие)
# - score_candidates(): считаем интегральный скор (категория, пересечение тегов, схожесть заголовка, «свежесть», домен)
# - serialize_item(): минимальный сериалайзер в единый вид, понятный фронту (id, slug, title, category.slug, image, seo_url)
# - related_news(): основной обработчик:
#       * GET-параметры: slug ИЛИ id (+ limit)
#       * альтернативно берёт slug из PATH (news/<slug>/related/)
#       * если база не найдена — возвращает {"results": [], "count": 0}, БЕЗ 400
#       * сортирует по скору, режет до limit, отдаёт JSON
#
# Важно:
# - Никаких жёстких зависимостей на PostgreSQL. Если есть pg_trgm — можно ускорить позже (см. комментарии).
# - Масштабируемый фолбэк: даже при SQLite всё работает (схожесть заголовка по difflib.SequenceMatcher).
# - Для больших баз можно прикрутить TrigramSimilarity и GIN-индексы отдельной миграцией (ниже даю пример).

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

import math
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse

from django.db import connection
from django.db.models import Q, QuerySet
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# --- МЯГКИЕ ИМПОРТЫ МОДЕЛЕЙ (если чего-то нет — просто пропустим) ---
Article = None
ImportedNews = None
try:
    from news.models import Article as ArticleModel
    Article = ArticleModel
except Exception:
    Article = None

try:
    from rssfeed.models import ImportedNews as ImportedNewsModel
    ImportedNews = ImportedNewsModel
except Exception:
    ImportedNews = None

# --- Канонизация «капризных» слагов ---
_ALIAS_MAP = {
    "obschestvo": "obshchestvo",
    "lenta-novostej": "lenta-novostey",
    "proisshestvija": "proisshestviya",
}

def canon_slug(s: Optional[str]) -> Optional[str]:
    if not s:
        return s
    s = s.strip().strip("/").lower()
    s = s.replace("—", "-").replace("–", "-").replace("_", "-")
    while "--" in s:
        s = s.replace("--", "-")
    return _ALIAS_MAP.get(s, s)

# --- Утилиты безопасного доступа к полям ---
def get_field(obj: Any, *names: str, default=None):
    for n in names:
        if hasattr(obj, n):
            val = getattr(obj, n)
            if val is not None:
                return val
    return default

def has_m2m(obj: Any, name: str) -> bool:
    try:
        return hasattr(obj, name) and hasattr(getattr(obj, name), "all")
    except Exception:
        return False

def obj_category_id(obj: Any):
    return get_field(obj, "category_id", default=None)

def obj_category(obj: Any):
    return get_field(obj, "category", default=None)

def obj_title(obj: Any) -> str:
    return get_field(obj, "title", "headline", default="") or ""

def obj_slug(obj: Any) -> Optional[str]:
    return get_field(obj, "slug", "seo_slug", "url_slug", default=None)

def obj_image(obj: Any) -> Optional[str]:
    return get_field(obj, "image", "image_url", "cover", "cover_image", default=None)

def obj_published(obj: Any):
    return get_field(obj, "published_at", "created_at", "updated_at", default=None)

def obj_source_url(obj: Any) -> Optional[str]:
    return get_field(obj, "original_url", "url", "link", default=None)

def extract_domain(u: Optional[str]) -> str:
    if not u:
        return ""
    try:
        host = urlparse(u).hostname or ""
        return re.sub(r"^www\.", "", host)
    except Exception:
        return ""

# --- Резолвинг базовой записи ---
def _first(qs: QuerySet):
    try:
        return qs.first()
    except Exception:
        return None

def resolve_base_by_slug(raw_slug: str) -> Tuple[Optional[object], Optional[Type]]:
    slug = canon_slug(raw_slug)
    if not slug:
        return None, None

    def hunt(model: Type) -> Optional[object]:
        if model is None:
            return None
        # Проверим возможные поля для slug
        fields = [f for f in ("slug", "seo_slug", "url_slug") if hasattr(model, f)]
        if not fields:
            return None
        q = Q()
        for f in fields:
            q |= Q(**{f: slug})
        obj = _first(model.objects.filter(q))
        if obj:
            return obj
        # Мягкий поиск при расхождениях
        q2 = Q()
        for f in fields:
            q2 |= Q(**{f + "__startswith": slug}) | Q(**{f + "__icontains": slug})
        return _first(model.objects.filter(q2))

    # Приоритет: сначала Article, затем ImportedNews
    obj = hunt(Article) or hunt(ImportedNews)
    return (obj, obj.__class__) if obj else (None, None)

def resolve_base_by_id(obj_id: str) -> Tuple[Optional[object], Optional[Type]]:
    def by_pk(model: Type):
        if model is None:
            return None
        try:
            return model.objects.filter(pk=obj_id).first()
        except Exception:
            return None
    obj = by_pk(Article) or by_pk(ImportedNews)
    return (obj, obj.__class__) if obj else (None, None)

# --- Сбор кандидатов ---
def order_recent(qs: QuerySet) -> QuerySet:
    if hasattr(qs.model, "published_at"):
        return qs.order_by("-published_at")
    if hasattr(qs.model, "created_at"):
        return qs.order_by("-created_at")
    return qs.order_by("-pk")

def build_candidates(base: object, limit_each: int = 200) -> List[Tuple[str, int, object]]:
    """
    Возвращает список (model_label, pk, obj) кандидатов из обеих моделей.
    Источники кандидатов:
      1) та же категория
      2) общие теги (если есть)
      3) тот же домен источника
      4) просто свежие
    """
    models: List[Type] = [m for m in (Article, ImportedNews) if m is not None]
    cat_id = obj_category_id(base)
    base_domain = extract_domain(obj_source_url(base))

    def take(model: Type, base_obj: object) -> List[object]:
        qs = model.objects.all()
        if hasattr(model, "is_published"):
            qs = qs.filter(is_published=True)
        # 1) та же категория
        part: List[object] = []
        if cat_id is not None and hasattr(model, "category_id"):
            part += list(order_recent(qs.filter(category_id=cat_id))[:limit_each])
        # 2) теги
        if has_m2m(base_obj, "tags") and hasattr(model, "tags"):
            try:
                base_tags = list(base_obj.tags.all())
                if base_tags:
                    part += list(order_recent(qs.filter(tags__in=base_tags).distinct())[:limit_each])
            except Exception:
                pass
        # 3) тот же домен
        if base_domain:
            # пробуем искать по url/link/ original_url
            qdom = Q()
            for f in ("original_url", "url", "link"):
                if hasattr(model, f):
                    qdom |= Q(**{f + "__icontains": base_domain})
            if qdom.children:
                part += list(order_recent(qs.filter(qdom))[:limit_each])
        # 4) просто свежие
        part += list(order_recent(qs)[:limit_each])
        # исключаем сам объект
        try:
            part = [o for o in part if getattr(o, "pk", None) != getattr(base_obj, "pk", None)]
        except Exception:
            pass
        return part

    pool: List[Tuple[str, int, object]] = []
    for m in models:
        for o in take(m, base):
            key = (m.__name__, getattr(o, "pk", -1))
            pool.append((key[0], key[1], o))

    # дедуп по (model, pk) с сохранением порядка (последний wins не важен)
    uniq: Dict[Tuple[str, int], object] = {}
    for label, pk, obj in pool:
        uniq[(label, pk)] = obj
    result = [(k[0], k[1], v) for k, v in uniq.items()]
    return result

# --- Схожесть заголовка (фолбэк без Postgres) ---
_word_re = re.compile(r"[a-zа-яё0-9]+", re.IGNORECASE)

def normalize_text(s: str) -> str:
    s = (s or "").lower()
    return " ".join(_word_re.findall(s))

def title_similarity(a: str, b: str) -> float:
    a_n = normalize_text(a)
    b_n = normalize_text(b)
    if not a_n or not b_n:
        return 0.0
    return SequenceMatcher(a=a_n, b=b_n).ratio()  # [0..1]

# --- Скоринг кандидатов ---
@dataclass
class Scored:
    label: str
    pk: int
    obj: object
    score: float

def recency_score(dt) -> float:
    """0..1: чем свежее, тем ближе к 1"""
    try:
        if not dt:
            return 0.0
        now = timezone.now()
        if timezone.is_naive(dt):
            # допустим наивный — преобразуем к now.tzinfo
            dt = dt.replace(tzinfo=now.tzinfo)
        days = max((now - dt).total_seconds() / 86400.0, 0.0)
        # до 2 недель ~1, дальше плавное затухание
        return 1.0 / (1.0 + days / 14.0)
    except Exception:
        return 0.0

def tag_overlap_score(base: object, cand: object) -> float:
    if not (has_m2m(base, "tags") and has_m2m(cand, "tags")):
        return 0.0
    try:
        b = {t.pk for t in base.tags.all()}
        c = {t.pk for t in cand.tags.all()}
        inter = len(b & c)
        if inter == 0:
            return 0.0
        # логарифмическая шкала, чтоб не «разносили» многотеговые
        return math.log(1 + inter, 2)  # 1→1, 3→~2, 7→~3
    except Exception:
        return 0.0

def same_category_score(base: object, cand: object) -> float:
    try:
        return 1.0 if obj_category_id(base) is not None and obj_category_id(base) == obj_category_id(cand) else 0.0
    except Exception:
        return 0.0

def same_domain_score(base: object, cand: object) -> float:
    bd = extract_domain(obj_source_url(base))
    cd = extract_domain(obj_source_url(cand))
    if not bd or not cd:
        return 0.0
    return 1.0 if bd == cd else 0.0

def compute_score(base: object, cand: object) -> float:
    w_cat = 3.0
    w_tags = 2.0
    w_title = 5.0
    w_rec = 0.6
    w_dom = 0.8

    s_cat = same_category_score(base, cand)
    s_tags = tag_overlap_score(base, cand)
    s_title = title_similarity(obj_title(base), obj_title(cand))
    s_rec = recency_score(obj_published(cand))
    s_dom = same_domain_score(base, cand)

    return w_cat * s_cat + w_tags * s_tags + w_title * s_title + w_rec * s_rec + w_dom * s_dom

# --- Сериализация в единый вид для фронта ---
def serialize_item(o: object) -> Dict[str, Any]:
    cid = getattr(o, "pk", None)
    slug = obj_slug(o) or ""
    title = obj_title(o) or ""
    image = obj_image(o)
    cat = obj_category(o)
    cat_slug = getattr(cat, "slug", None) if cat else None

    # seo_url для фронта: /<category>/<slug>/ (если можем построить)
    seo_url = None
    if cat_slug and slug:
        seo_url = f"/{cat_slug}/{slug}/"

    # аккуратно достанем source title, если есть
    src_title = get_field(o, "source_title", "source_name", default=None)
    if not src_title:
        # попробуем из связанного source/name, если есть
        src = get_field(o, "source", default=None)
        if src:
            src_title = get_field(src, "title", "name", default=None)

    return {
        "id": cid,
        "slug": slug,
        "title": title,
        "image": image,
        "category": {"slug": cat_slug} if cat_slug else None,
        "seo_url": seo_url,
        "source_title": src_title,
        # можно добавить published_at, если поле есть
        "published_at": str(obj_published(o)) if obj_published(o) else None,
    }

# --- Основной обработчик ---
@api_view(["GET"])
@permission_classes([AllowAny])
def related_news(request, slug: Optional[str] = None):
    """
    Поддерживаем оба варианта:
      1) /api/news/<slug>/related/?limit=8  → slug приходит как аргумент роутера
      2) /api/news/related/?slug=<slug>&limit=8
      3) /api/news/related/?id=<pk>&limit=8
    При отсутствии базы — мягкий ответ {"results": [], "count": 0}.
    """
    raw_slug = slug or request.query_params.get("slug")
    obj_id = request.query_params.get("id")
    try:
        limit = int(request.query_params.get("limit", "8"))
    except Exception:
        limit = 8

    base_obj: Optional[object] = None
    base_model: Optional[Type] = None

    # приоритет id
    if obj_id:
        base_obj, base_model = resolve_base_by_id(obj_id)

    if base_obj is None and raw_slug:
        base_obj, base_model = resolve_base_by_slug(raw_slug)

    if base_obj is None or base_model is None:
        return Response({"results": [], "count": 0})

    # Собираем кандидатов и считаем скор
    cand_triplets = build_candidates(base_obj, limit_each=200)
    scored: List[Scored] = []
    for label, pk, obj in cand_triplets:
        try:
            sc = compute_score(base_obj, obj)
        except Exception:
            sc = 0.0
        scored.append(Scored(label=label, pk=pk, obj=obj, score=sc))

    # Сортировка: по убыванию score, при равенстве — по свежести
    scored.sort(
        key=lambda x: (
            -x.score,
            -(obj_published(x.obj).timestamp() if obj_published(x.obj) else 0.0),
            -x.pk,
        )
    )

    # Срез и сериализация
    top = scored[: max(0, limit)]
    data = [serialize_item(s.obj) for s in top]
    return Response({"results": data, "count": len(data)})
