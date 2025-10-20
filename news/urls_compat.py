# Путь: news/urls_compat.py
# Назначение: Совместимость старых путей API → редиректы на актуальные маршруты.
# ВАЖНО: query_string=True — пробрасываем параметры запроса (?src=..., w, h, fmt, ...)

from django.urls import path, re_path  # re_path оставляем, вдруг добавятся паттерны
from django.views.generic.base import RedirectView

app_name = "news_compat"

urlpatterns = [
    # Старый путь миниатюр: /api/news/thumbnail/ → новый ресайзер
    path(
        "api/news/thumbnail/",
        RedirectView.as_view(
            url="/api/media/thumbnail/",
            permanent=True,
            query_string=True,  # ← добавлено
        ),
        name="compat_news_thumbnail",
    ),
    # Ещё один старый вариант: /api/news/media/thumbnail/ → новый ресайзер
    path(
        "api/news/media/thumbnail/",
        RedirectView.as_view(
            url="/api/media/thumbnail/",
            permanent=True,
            query_string=True,  # ← добавлено
        ),
        name="compat_news_media_thumbnail",
    ),
]
