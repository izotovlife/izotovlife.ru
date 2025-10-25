# Путь: backend/news/urls_perf.py
# Назначение: URLs для производительных вспомогательных эндпоинтов (батч-обложки категорий).

from django.urls import path
from .views_covers import CategoryCoversBatchView

app_name = "news_perf"

urlpatterns = [
    # => /api/categories/covers/?w=420&h=236&fmt=webp&fit=cover&q=82
    path("categories/covers/", CategoryCoversBatchView.as_view(), name="category_covers_batch"),
]
