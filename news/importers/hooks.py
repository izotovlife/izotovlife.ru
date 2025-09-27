# backend/news/importers/hooks.py
# Назначение: Гейт (сторож) для импортёров. Не даёт сохранять новости «только с заголовком».
# Что умеет:
#   • Извлекает текст из известных полей (content/body/full_text/description/summary/text).
#   • Чистит HTML, считает символы и слова.
#   • Общие пороги (min_chars, min_words) и per-domain настройки (можно задавать строгость по источникам).
#   • Опционально — требовать валидную картинку (не заглушку).
#   • Чёрный список доменов (не импортировать совсем).
# Использование:
#   from news.importers.hooks import validate_before_save, SkipEmptyNews
#   ...
#   try:
#       validate_before_save(raw_dict)    # бросит SkipEmptyNews, если нельзя импортировать
#       ImportedNews.objects.create(**raw_dict)
#   except SkipEmptyNews as e:
#       logger.info(str(e))               # пропускаем запись
# Путь: backend/news/importers/hooks.py

import re
import html
from urllib.parse import urlparse
from typing import Tuple, Optional

try:
    # Не обязателен. Если есть Django settings — можно переопределять пороги через него.
    from django.conf import settings  # type: ignore
except Exception:  # pragma: no cover
    settings = None  # на случай, если модуль дергают вне Django

# Поля, из которых берём текст (в порядке приоритета)
TEXT_FIELDS_ORDER = ("content", "body", "full_text", "description", "summary", "text")

# --- БАЗОВЫЕ НАСТРОЙКИ (можно поправить под себя) ---

DEFAULT_MIN_CHARS = 280     # минимальное число символов «чистого» текста
DEFAULT_MIN_WORDS = 40      # минимальное число слов
DEFAULT_REQUIRE_IMAGE = False  # требовать валидную картинку (не заглушку)

# Заглушки/битые изображения (под вашу статику)
PLACEHOLDER_SUBSTRINGS = (
    "default_news.svg",
    "/static/img/default_news.svg",
)

# Чёрный список доменов — ничего не импортируем
BLOCKED_DOMAINS = {
    # "t.me",  # пример: телеграм-линки как источник не нужны
}

# Настройки по доменам (перекрывают дефолты)
# Примеры:
#   "example.com": {"min_chars": 500, "min_words": 70, "require_image": True}
PER_DOMAIN_POLICIES = {
    # "ria.ru": {"min_chars": 400, "min_words": 60},
    # "lenta.ru": {"require_image": True},
}

# Опционально — переопределение из Django settings (если заданы)
if settings and hasattr(settings, "NEWS_GUARD"):
    cfg = getattr(settings, "NEWS_GUARD") or {}
    DEFAULT_MIN_CHARS = cfg.get("default_min_chars", DEFAULT_MIN_CHARS)
    DEFAULT_MIN_WORDS = cfg.get("default_min_words", DEFAULT_MIN_WORDS)
    DEFAULT_REQUIRE_IMAGE = cfg.get("default_require_image", DEFAULT_REQUIRE_IMAGE)
    BLOCKED_DOMAINS.update(set(cfg.get("blocked_domains", [])))
    PER_DOMAIN_POLICIES.update(cfg.get("per_domain_policies", {}))


class SkipEmptyNews(Exception):
    """Сигнальное исключение: запись нужно пропустить (мало текста/нет контента/заблокированный домен)."""


def _first_nonempty_text(raw: dict) -> Optional[str]:
    for key in TEXT_FIELDS_ORDER:
        val = raw.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return None


def _strip_html(s: str) -> str:
    # очень простая чистка HTML → текст, без внешних зависимостей
    s = html.unescape(s)
    s = re.sub(r"<script[\s\S]*?</script>", " ", s, flags=re.I)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _word_count(s: str) -> int:
    if not s:
        return 0
    return len([w for w in s.split(" ") if w])


def _extract_domain(raw: dict) -> Optional[str]:
    for key in ("original_url", "source_url", "link", "url"):
        val = raw.get(key)
        if not isinstance(val, str) or not val.strip():
            continue
        try:
            host = urlparse(val).hostname or ""
            host = host.lower().lstrip(".")
            if host.startswith("www."):
                host = host[4:]
            if host:
                return host
        except Exception:
            continue
    return None


def _has_valid_image(raw: dict) -> bool:
    for key in ("image", "cover_image", "preview_image", "thumbnail"):
        val = raw.get(key)
        if not val:
            continue
        s = str(val)
        if not any(ph in s for ph in PLACEHOLDER_SUBSTRINGS):
            return True
    return False


def _resolved_policy(domain: Optional[str]) -> Tuple[int, int, bool]:
    """
    Возвращает (min_chars, min_words, require_image) с учётом per-domain.
    """
    min_chars = DEFAULT_MIN_CHARS
    min_words = DEFAULT_MIN_WORDS
    require_image = DEFAULT_REQUIRE_IMAGE
    if domain and domain in PER_DOMAIN_POLICIES:
        p = PER_DOMAIN_POLICIES[domain] or {}
        min_chars = int(p.get("min_chars", min_chars))
        min_words = int(p.get("min_words", min_words))
        require_image = bool(p.get("require_image", require_image))
    return min_chars, min_words, require_image


def validate_before_save(raw: dict,
                         min_chars: Optional[int] = None,
                         min_words: Optional[int] = None,
                         require_image: Optional[bool] = None):
    """
    Главный сторож: бросает SkipEmptyNews с пояснением, если запись не проходит правила.

    Параметры можно не задавать — возьмутся дефолты и/или per-domain политика.
    """
    if not isinstance(raw, dict):
        raise SkipEmptyNews("Пропуск: некорректный формат данных (ожидался dict).")

    domain = _extract_domain(raw)
    if domain in BLOCKED_DOMAINS:
        raise SkipEmptyNews(f"Пропуск: домен {domain} в чёрном списке.")

    # Пороговые значения (domain-override → явные аргументы → дефолты)
    p_min_chars, p_min_words, p_require_image = _resolved_policy(domain)
    min_chars = int(min_chars if min_chars is not None else p_min_chars)
    min_words = int(min_words if min_words is not None else p_min_words)
    require_image = bool(require_image if require_image is not None else p_require_image)

    # Достаём текст
    raw_text = _first_nonempty_text(raw) or ""
    clean_text = _strip_html(raw_text)
    n_chars = len(clean_text)
    n_words = _word_count(clean_text)

    # Проверка картинки (если требуется)
    if require_image and not _has_valid_image(raw):
        raise SkipEmptyNews("Пропуск: требовалась валидная картинка, но её нет (или это заглушка).")

    # Порог по тексту
    if n_chars < min_chars or n_words < min_words:
        raise SkipEmptyNews(
            f"Пропуск: недостаточно текста (символов {n_chars}/{min_chars}, слов {n_words}/{min_words})."
        )

    # Всё ок — ничего не возвращаем (не бросаем исключение)

