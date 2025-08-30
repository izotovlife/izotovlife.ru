"""API views for aggregator items and sources."""

from datetime import date

from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

from .models import Item, Source
from .serializers import ItemSerializer, SourceSerializer


class DefaultPagination(PageNumberPagination):
    """Simple page-number pagination."""

    page_size = 20


class ItemView(ListAPIView):
    """List items with optional filtering."""

    serializer_class = ItemSerializer
    pagination_class = DefaultPagination
    queryset = Item.objects.select_related("source").order_by(
        "-published_at", "-id"
    )

    def get_queryset(self):  # pragma: no cover - thin wrapper
        qs = super().get_queryset()
        params = self.request.query_params

        source_param = params.get("source")
        if source_param:
            if source_param.isdigit():
                qs = qs.filter(source_id=int(source_param))
            else:
                qs = qs.filter(source__url=source_param)

        q = params.get("q")
        if q:
            qs = qs.filter(title__icontains=q)

        category = params.get("category")
        if category:
            qs = qs.filter(category__iexact=category)

        date_from = params.get("date_from")
        if date_from:
            try:
                qs = qs.filter(published_at__date__gte=date.fromisoformat(date_from))
            except ValueError:
                pass

        date_to = params.get("date_to")
        if date_to:
            try:
                qs = qs.filter(published_at__date__lte=date.fromisoformat(date_to))
            except ValueError:
                pass

        return qs


class SourceView(ListAPIView):
    """List feed sources."""

    serializer_class = SourceSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):  # pragma: no cover - thin wrapper
        qs = Source.objects.all()
        if not self.request.query_params.get("all"):
            qs = qs.filter(is_active=True)
        return qs.order_by("title")

