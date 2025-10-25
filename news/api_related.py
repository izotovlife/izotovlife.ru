# Путь: backend/news/api_related.py
# Назначение: Универсальный эндпоинт «Похожие новости» + совместимость со старыми путями.
# URL (новый):   GET /api/news/related/<slug>/?limit=8
# URL (legacy):  GET /api/news/article/<slug>/related/
#                GET /api/news/rss/<category>/<slug>/related/
#                GET /api/news/<category>/<slug>/related/
# Дополнено в этой версии:
#   ✅ Безопасная работа с датами (строки ISO → datetime) и пустыми FileField (без ValueError на .url)
#   ✅ Больше «говорящих» полей картинок (image/cover/lead_image/thumbnail/main_image/image_url/cover_image)
#   ✅ Мягкий обработчик пустого slug: GET /api/news/related/ → 200 с {"items": []} (гасит 404-спам старого фронта)
#   ✅ НИЧЕГО существующего не удалено — только добавлено и усилено.
#
# Примечание: чтобы гасить запросы без slug, в urls.py должен быть маршрут:
#   path("api/news/related/", related_news_empty, name="related_news_empty"),

from django.http import JsonResponse, HttpResponseBadRequest
from django.apps import apps
from django.db.models import Q
from django.utils.dateparse import parse_datetime
from datetime import datetime
from typing import Optional


def _get_model(app_label, model_name):
    try:
        return apps.get_model(app_label, model_name)
    except LookupError:
        return None


Article = _get_model("news", "Article")                 # редакционные
ImportedNews = _get_model("rssfeed", "ImportedNews")    # импортированные (если приложение установлено)


def _as_dt(val) -> Optional[datetime]:
    """Приводим поле даты к datetime, если это строка/дата/датавремя; иначе None."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    # иногда хранится как date
    try:
        from datetime import date
        if isinstance(val, date):
            return datetime(val.year, val.month, val.day)
    except Exception:
        pass
    # строка → пытаемся распарсить ISO
    try:
        s = str(val).strip()
        if not s:
            return None
        dt = parse_datetime(s)
        if dt:
            return dt
    except Exception:
        pass
    return None


def _first_dt(obj) -> Optional[datetime]:
    for name in ("published_at", "pub_date", "created_at", "created", "date"):
        if hasattr(obj, name):
            dt = _as_dt(getattr(obj, name))
            if dt:
                return dt
    return None


def _image_url(obj) -> Optional[str]:
    """Безопасно достаём URL картинки из разных типов полей, не падаем на пустых FileField."""
    for name in ("image", "lead_image", "cover", "thumbnail", "main_image", "image_url", "cover_image", "preview_image"):
        if not hasattr(obj, name):
            continue
        v = getattr(obj, name)
        if not v:
            continue
        # FileField/ImageField → FieldFile
        if hasattr(v, "name") or hasattr(v, "url"):
            fname = getattr(v, "name", "") or ""
            if not fname:
                continue
            try:
                url = getattr(v, "url", None)
                if isinstance(url, str) and url:
                    return url
            except Exception:
                # пустой/битый FileField → пропускаем
                continue
        # строковое поле
        try:
            s = str(v).strip()
            if s:
                return s
        except Exception:
            continue
    return None


def _category(obj):
    for name in ("category", "category_fk", "cat", "section"):
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def _category_lookup(Model):
    """Возвращает имя поля связи с категорией для фильтрации (FK/M2M/строка)."""
    for name in ("category", "category_fk", "cat", "section"):
        try:
            Model._meta.get_field(name)
            return name
        except Exception:
            continue
    return "category"


def _kw_query(title: str) -> Q:
    """Простая полнотекстовая выборка по словам из заголовка, длина >= 4, до 6 штук."""
    if not title:
        return Q()
    raw = title.replace("—", " ").replace("-", " ")
    words = []
    seen = set()
    for w in raw.split():
        w = w.strip()
        if len(w) < 4:
            continue
        lw = w.lower()
        if lw in seen:
            continue
        seen.add(lw)
        words.append(lw)
        if len(words) >= 6:
            break
    q = Q()
    for w in words:
        q |= Q(title__icontains=w)
    return q


def _serialize(obj):
    cat = _category(obj)
    dt = _first_dt(obj)
    return {
        "id": getattr(obj, "pk", None),
        "slug": getattr(obj, "slug", None),
        "title": getattr(obj, "title", None),
        "image": _image_url(obj),
        "category": (
            {
                "slug": getattr(cat, "slug", None),
                "title": (getattr(cat, "title", None) or getattr(cat, "name", None)),
            }
            if cat
            else None
        ),
        "published_at": (dt.isoformat() if dt else None),
    }


def related_news(request, slug):
    """Новый универсальный обработчик «похожих» по slug: /api/news/related/<slug>/?limit=8"""
    if not slug:
        return HttpResponseBadRequest("slug required")

    try:
        limit = max(1, min(int(request.GET.get("limit", "8")), 50))
    except Exception:
        limit = 8

    base = None
    base_type = None

    if Article:
        base = Article.objects.filter(slug=slug).first()
        if base:
            base_type = "article"
    if not base and ImportedNews:
        base = ImportedNews.objects.filter(slug=slug).first()
        if base:
            base_type = "imported"

    # Нет базовой — отдаём пусто (200), чтобы фронт не падал
    if not base:
        return JsonResponse({"items": []}, status=200)

    cat = _category(base)
    title = getattr(base, "title", "") or ""

    q_title = _kw_query(title)

    a_qs = Article.objects.none() if not Article else Article.objects.all()
    i_qs = ImportedNews.objects.none() if not ImportedNews else ImportedNews.objects.all()

    if cat:
        field_a = _category_lookup(Article) if Article else None
        field_i = _category_lookup(ImportedNews) if ImportedNews else None
        if Article and field_a:
            try:
                a_qs = a_qs.filter(**{field_a: cat})
            except Exception:
                # для M2M тоже сработает, но на всякий случай попробуем __in
                try:
                    a_qs = a_qs.filter(**{f"{field_a}__in": [cat]})
                except Exception:
                    pass
        if ImportedNews and field_i:
            try:
                i_qs = i_qs.filter(**{field_i: cat})
            except Exception:
                try:
                    i_qs = i_qs.filter(**{f"{field_i}__in": [cat]})
                except Exception:
                    pass
    else:
        if Article:
            a_qs = a_qs.filter(q_title)
        if ImportedNews:
            i_qs = i_qs.filter(q_title)

    # исключаем базовую запись
    if base_type == "article" and Article:
        a_qs = a_qs.exclude(slug=slug)
    if base_type == "imported" and ImportedNews:
        i_qs = i_qs.exclude(slug=slug)

    def order_safe(qs):
        for f in ("-published_at", "-pub_date", "-created_at", "-created", "-date", "-id"):
            try:
                return qs.order_by(f)
            except Exception:
                continue
        return qs

    if Article:
        a_qs = order_safe(a_qs)[:limit]
    if ImportedNews:
        i_qs = order_safe(i_qs)[:limit]

    combined = list(a_qs) + list(i_qs)
    combined.sort(key=lambda o: (_first_dt(o) or datetime.min), reverse=True)
    combined = combined[:limit]

    return JsonResponse({"items": [_serialize(o) for o in combined]}, status=200)


# ----- Легаси-совместимость: те же данные, но под старыми путями -----

def related_news_legacy_simple(request, slug):
    """
    Совместимость для: /api/news/article/<slug>/related/
                        /api/news/bez-kategorii/<slug>/related/
    """
    return related_news(request, slug=slug)


def related_news_legacy_with_cat(request, category, slug):
    """
    Совместимость для: /api/news/rss/<category>/<slug>/related/
                       /api/news/<category>/<slug>/related/
    Категорию игнорируем, работаем по slug (универсальная логика).
    """
    return related_news(request, slug=slug)


def related_news_empty(request):
    """
    Мягкий обработчик пустого slug: /api/news/related/
    Возвращает 200 с пустым списком — чтобы старые клиенты не сыпали 404 в консоль.
    """
    return JsonResponse({"items": [], "detail": "slug is required"}, status=200)
