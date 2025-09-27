# backend/news/utils/content_filters.py
# Назначение: Проверки «есть ли у новости содержимое» + утилиты для queryset.
# Обновлено:
#   • Строгие проверки с очисткой HTML.
#   • Быстрые аннотации для queryset (без очистки HTML).
#   • ДОБАВЛЕН совместимый псевдоним has_text_dict(...) → вызывает строгую проверку,
#     чтобы старые импорты в проекте не ломались.
# Путь: backend/news/utils/content_filters.py

from __future__ import annotations

import html as _html
import re
from typing import Dict, Optional, List

from django.db.models import (
    F,
    Value,
    CharField,
    QuerySet,
    IntegerField,
    BooleanField,
    Case,
    When,
)
from django.db.models.functions import Coalesce, Trim, Length

# Кандидаты на текстовые поля (разные модели/импортёры используют разные имена)
TEXT_FIELDS_ORDER: tuple[str, ...] = (
    "content", "body", "full_text", "description", "summary", "text",
)

# ────────────────────────────────────────────────────────────────────────────────
# Строгие проверки (Python): чистим HTML → считаем символы/слова.
# ────────────────────────────────────────────────────────────────────────────────

def _strip_html(s: str) -> str:
    """Грубая очистка HTML → плоский текст (без зависимостей)."""
    if not isinstance(s, str):
        return ""
    s = _html.unescape(s)
    s = re.sub(r"<script[\s\S]*?</script>", " ", s, flags=re.I)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)           # вырезаем все теги
    s = s.replace("\xa0", " ")                # NBSP → пробел
    s = re.sub(r"\s+", " ", s)               # схлопываем пробелы
    return s.strip()

def _first_text_value_from_dict(data: Dict) -> Optional[str]:
    for k in TEXT_FIELDS_ORDER:
        v = data.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return None

def has_text_dict_strict(data: Dict, *, min_chars: int = 1, min_words: int = 1) -> bool:
    """
    Строгая проверка «сырых» данных (до сохранения).
    Учитывает очистку HTML и &nbsp;.
    """
    raw = _first_text_value_from_dict(data) or ""
    clean = _strip_html(raw)
    if len(clean) < min_chars:
        return False
    if min_words > 0:
        words = [w for w in clean.split(" ") if w]
        if len(words) < min_words:
            return False
    return True

def instance_to_dict(instance) -> Dict:
    data: Dict = {}
    for field in instance._meta.get_fields():
        if hasattr(field, "attname"):
            data[field.attname] = getattr(instance, field.attname, None)
    return data

def instance_has_text_strict(instance, *, min_chars: int = 1, min_words: int = 1) -> bool:
    return has_text_dict_strict(instance_to_dict(instance), min_chars=min_chars, min_words=min_words)

# Совместимость с прежним кодом: старое имя функции.
# НЕ удаляйте — пусть остаётся для других модулей, если они его импортировали раньше.
def has_text_dict(data: Dict) -> bool:
    return has_text_dict_strict(data, min_chars=1, min_words=1)

# ────────────────────────────────────────────────────────────────────────────────
# Быстрые аннотации для QuerySet (без очистки HTML; для грубой фильтрации на БД)
# ────────────────────────────────────────────────────────────────────────────────

def _present_text_fields(model) -> List[str]:
    model_fields = {f.name for f in model._meta.get_fields() if hasattr(f, "name")}
    return [name for name in TEXT_FIELDS_ORDER if name in model_fields]

def _coalesce_text_expr(model):
    fields = _present_text_fields(model)
    if fields:
        coalesced = Coalesce(*[F(name) for name in fields],
                             Value("", output_field=CharField()),
                             output_field=CharField())
    else:
        coalesced = Value("", output_field=CharField())
    return Trim(coalesced)

def annotate_has_text(qs: QuerySet) -> QuerySet:
    """
    Аннотирует:
      _concat_text — склеенный текст с Trim
      _text_len    — длина
      has_text     — True, если длина > 0
    Важно: не учитывает теговую «пустоту» (<br/>, &nbsp;). Для абсолютной точности используйте строгий режим в Python.
    """
    expr = _coalesce_text_expr(qs.model)
    qs = qs.annotate(_concat_text=expr)
    qs = qs.annotate(_text_len=Length(F("_concat_text"), output_field=IntegerField()))
    qs = qs.annotate(
        has_text=Case(
            When(_text_len__gt=0, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
    )
    return qs

def filter_nonempty(qs: QuerySet) -> QuerySet:
    """Быстрый фильтр: только записи с длиной текста > 0 (без очистки HTML)."""
    return annotate_has_text(qs).filter(has_text=True)
