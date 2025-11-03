# Путь: backend/rssfeed/monkeypatch.py
# Назначение: Прозрачная подмена feedparser.parse — если первый аргумент похож на URL,
#             то качаем байты через rssfeed.net.get_rss_bytes и только потом парсим.
#             Существующий код, где вызывается feedparser.parse(URL), трогать не нужно.
import logging
import re
from typing import Any

import feedparser  # type: ignore

from .net import get_rss_bytes, DEFAULT_UA

log = logging.getLogger(__name__)

_URL_RE = re.compile(r"^(https?:)?//", re.I)

_original_parse = feedparser.parse  # сохраним оригинал

def _patched_parse(thing: Any, *args, **kwargs):
    try:
        if isinstance(thing, str) and _URL_RE.match(thing):
            headers = kwargs.pop("request_headers", None) or {
                "User-Agent": DEFAULT_UA,
                "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
            }
            data, enc, meta = get_rss_bytes(thing)
            return _original_parse(data, *args, **kwargs)
        return _original_parse(thing, *args, **kwargs)
    except Exception:
        log.exception("feedparser.parse() patched path fell back to original")
        return _original_parse(thing, *args, **kwargs)

if getattr(feedparser.parse, "_izotovlife_patched", False) is not True:
    feedparser.parse = _patched_parse  # type: ignore
    setattr(feedparser.parse, "_izotovlife_patched", True)
    log.info("feedparser.parse patched by rssfeed.monkeypatch")
