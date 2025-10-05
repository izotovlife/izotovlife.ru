# Путь: backend/news/urls_rss_compat.py
# Назначение: Маршруты-адаптеры под фронтовые пути RSS:
#   • /api/news/rss/source/<source>/<slug>/
#   • /api/news/rss/source/<source>/<slug>/related/

from django.urls import path
from .api_rss_compat import ImportedNewsDetailCompat, ImportedNewsRelatedCompat

app_name = "news_rss_compat"

urlpatterns = [
    path(
        "rss/source/<slug:source>/<slug:slug>/",
        ImportedNewsDetailCompat.as_view(),
        name="rss_detail_compat",
    ),
    path(
        "rss/source/<slug:source>/<slug:slug>/related/",
        ImportedNewsRelatedCompat.as_view(),
        name="rss_related_compat",
    ),
]
