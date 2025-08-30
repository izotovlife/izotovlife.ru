"""URL routes for the aggregator API."""

from django.urls import path

from .views import ItemView, SourceView


urlpatterns = [
    path("items/", ItemView.as_view(), name="aggregator-item-list"),
    path("sources/", SourceView.as_view(), name="aggregator-source-list"),
]

