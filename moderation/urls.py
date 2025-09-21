# backend/moderation/urls.py
# Назначение: URL-ы панелей редактора.
# Путь: backend/moderation/urls.py

from django.urls import path
from .views import QueueView, ReviewView

urlpatterns = [
    path('queue/', QueueView.as_view(), name='moderation_queue'),
    path('review/<int:article_id>/', ReviewView.as_view(), name='moderation_review'),
]
