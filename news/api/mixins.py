# backend/news/api/mixins.py
# Назначение: Миксин для DRF ViewSet, автоматически отфильтровывает «пустые» новости.
# Как использовать: у ваших ViewSet добавьте первым родителем NonEmptyNewsMixin.
# Пример:
#   class ImportedNewsViewSet(NonEmptyNewsMixin, ModelViewSet): ...
# Путь: backend/news/api/mixins.py

from rest_framework import exceptions
from ..utils.content_filters import filter_nonempty

class NonEmptyNewsMixin:
    """
    Оборачивает get_queryset: исключает новости без содержимого.
    Ничего не меняет в сериализаторах/маршрутах.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        try:
            return filter_nonempty(qs)
        except Exception as e:
            # Если что-то пошло не так, лучше честно сообщить 500, чем вернуть мусор
            raise exceptions.APIException(f"Content filter failure: {e}")
