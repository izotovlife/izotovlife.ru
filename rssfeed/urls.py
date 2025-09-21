# backend/rssfeed/urls.py
# Назначение: URL для запуска импорта RSS из админки.
# Путь: backend/rssfeed/urls.py

from django.urls import path
from .views import import_rss_source

urlpatterns = [
    path("import/<int:pk>/", import_rss_source, name="rssfeed_rssfeedsource_import"),
]

