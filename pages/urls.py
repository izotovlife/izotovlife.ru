# backend/pages/urls.py
# Назначение: Роутинг для API статических страниц.

from django.urls import path
from .views import PageDetailView, PageListView

urlpatterns = [
    path("", PageListView.as_view(), name="pages_list"),
    path("<slug:slug>/", PageDetailView.as_view(), name="page_detail"),
]
