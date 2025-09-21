# backend/news/pagination.py
# Назначение: Кастомный пагинатор для новостной ленты с поддержкой DRF-формата.
# Путь: backend/news/pagination.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class NewsFeedPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
        })

