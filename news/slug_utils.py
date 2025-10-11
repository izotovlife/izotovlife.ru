# Путь: backend/news/slug_utils.py
# Назначение: Транслитерация RU→LAT и безопасная генерация уникальных slug для категорий (и не только).

from django.utils.text import slugify
from unidecode import unidecode

def slugify_ru(text: str) -> str:
    """
    Примеры:
      'Лента новостей' -> 'lenta-novostei'
      'В мире'         -> 'v-mire'
      'Наука & техника'-> 'nauka-tekhnika'
    """
    if not text:
        return ""
    base = unidecode(str(text))
    return slugify(base, allow_unicode=False)

def make_unique(base_slug: str, exists) -> str:
    """
    Обеспечивает уникальность: base, base-2, base-3, ...
    exists(slug)->bool: функция «занят ли такой slug».
    """
    base = (base_slug or "category").strip("-")
    candidate = base
    n = 2
    while exists(candidate):
        candidate = f"{base}-{n}"
        n += 1
    return candidate
