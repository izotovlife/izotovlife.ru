# Путь: backend/news/urls_favorites.py
# Назначение: Подмодуль маршрутов для избранного.

from django.urls import path
from .views_favorites import FavoriteListView, favorite_check, favorite_toggle

urlpatterns = [
    path("", FavoriteListView.as_view(), name="favorites-list"),            # GET /api/news/favorites/
    path("check/", favorite_check, name="favorites-check"),                 # GET /api/news/favorites/check/?slug=...
    path("toggle/", favorite_toggle, name="favorites-toggle"),              # POST /api/news/favorites/toggle/
]
