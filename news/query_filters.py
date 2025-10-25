# Путь: backend/news/query_filters.py
# Назначение: Утилиты для фильтрации новостей по «содержательности» текста.
# Использование: подключаем в вьюхах ленты для ImportedNews, чтобы отсечь элементы,
# у которых есть только картинка и заголовок (описание/текст пустые или слишком короткие).

from django.conf import settings
from django.db.models import Value, CharField
from django.db.models.functions import Coalesce, Length

DEFAULT_MIN_CHARS = 120  # разумный минимум «живого» текста

def only_with_meaningful_text(qs, min_chars: int | None = None, summary_field="summary", content_field="content"):
    """
    Фильтрует queryset так, чтобы оставались только элементы с
    достаточной длиной текста (summary или content).
    - Если summary пуст, используем content.
    - Поля должны быть текстовыми; если у вас другое имя поля — передайте параметрами.
    - По умолчанию порог берём из settings.RSS_MIN_TEXT_CHARS или 120.
    """
    threshold = min_chars or getattr(settings, "RSS_MIN_TEXT_CHARS", DEFAULT_MIN_CHARS)

    # Сформируем «эффективный текст»: summary -> content -> ''.
    # CharField важен для корректной типизации Coalesce.
    effective_text = Coalesce(
        summary_field,
        content_field,
        Value("", output_field=CharField()),
        output_field=CharField(),
    )

    return qs.annotate(_text_len=Length(effective_text)).filter(_text_len__gte=threshold)
