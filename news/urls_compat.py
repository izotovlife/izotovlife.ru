# Путь: news/urls_compat.py
# Назначение: Совместимость старых маршрутов API. Перенаправляем старые пути на актуальные.
# Ничего текущего не ломает. Можно расширять новыми редиректами по мере необходимости.

from django.urls import path
from django.views.generic.base import RedirectView

urlpatterns = [
    # Старый путь фронта → новый ресайзер миниатюр
    path(
        "api/news/thumbnail/",
        RedirectView.as_view(url="/api/media/thumbnail/", permanent=True),
    ),
]
