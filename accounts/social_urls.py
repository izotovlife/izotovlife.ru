# Путь: news_aggregator/accounts/social_urls.py
# Назначение: Роут для завершения соц-логина → /api/auth/social/complete/

from django.urls import path
from .social_views import SocialCompleteView

urlpatterns = [
    path("complete/", SocialCompleteView.as_view(), name="social_complete"),
]

