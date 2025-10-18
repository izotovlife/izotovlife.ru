# Путь: backend/news/urls_extra_media.py
# Назначение: Отдельный urls-модуль для подключения медиа-ресайзера, не затрагивая основной news/urls.py.
# Эндпоинт: /api/news/media/thumbnail/?src=...&w=...&h=...&fmt=webp&q=82&fit=cover&sharpen=1

from django.urls import path
from .views_media import thumbnail_proxy

urlpatterns = [
    path("news/media/thumbnail/", thumbnail_proxy, name="thumbnail_proxy"),
]
