# Путь: backend/news/views_covers.py
# Назначение: Батч-эндпоинт, который возвращает ссылки на миниатюры-обложки для всех категорий.
# Формат ответа: {"politika": "https://.../api/media/thumbnail/?src=/uploads/..&w=420&h=236&...", "v-mire": null, ...}

from urllib.parse import urlencode

from django.http import JsonResponse
from django.urls import reverse
from django.views import View

from .models import Category

def _pick_src_for_category(cat):
    """
    Выбираем источник картинки категории из известных полей.
    НИЧЕГО НЕ УДАЛЯЕМ — только проверяем по очереди.
    """
    # добавляйте поля сюда по мере надобности
    candidates = ("cover", "image", "top_image", "preview_image")
    for field in candidates:
        if hasattr(cat, field):
            val = getattr(cat, field) or ""
            if isinstance(val, str) and val.strip():
                return val.strip()
            # File/ImageField → .url
            try:
                url = getattr(val, "url", "") or ""
                if url:
                    return url
            except Exception:
                pass
    return ""

class CategoryCoversBatchView(View):
    def get(self, request):
        # Параметры миниатюр (по умолчанию под карточки категорий)
        try:
            w = int(request.GET.get("w", "420"))
            h = int(request.GET.get("h", "236"))
        except Exception:
            w, h = 420, 236

        fmt = (request.GET.get("fmt") or "webp").lower()
        fit = (request.GET.get("fit") or "cover").lower()
        try:
            q = int(request.GET.get("q", "82"))
        except Exception:
            q = 82

        thumb_path = reverse("media:thumbnail")  # -> /api/media/thumbnail/
        base = request.build_absolute_uri(thumb_path)

        payload = {}
        # only() ускоряет SELECT
        for cat in Category.objects.all().only("id", "slug", "name"):
            raw_src = _pick_src_for_category(cat)
            if raw_src:
                qs = urlencode({"src": raw_src, "w": w, "h": h, "fmt": fmt, "fit": fit, "q": q})
                payload[cat.slug] = f"{base}?{qs}"
            else:
                payload[cat.slug] = None

        # Кэшируйте на nginx/CDN по желанию — тут достаточно длинного client cache.
        resp = JsonResponse(payload)
        resp["Cache-Control"] = "public, max-age=600"  # 10 минут — можно увеличить
        return resp
