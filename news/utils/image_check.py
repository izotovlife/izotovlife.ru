# Путь: backend/news/utils/image_check.py
# Назначение: Утилиты проверки доступности изображения по URL (HEAD/GET с таймаутами).
# Особенности:
#   - Безопасная проверка: сначала HEAD, при 405/403 — пробуем GET (stream, без загрузки тела).
#   - Таймауты короткие, чтобы не «виснуть» на плохих хостах.
#   - Возвращает True/False, не бросает исключения наружу.

import contextlib
import requests


DEFAULT_TIMEOUT = (3.5, 6.0)  # (connect, read)


def _head_ok(url: str, timeout=DEFAULT_TIMEOUT) -> bool:
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout)
        return 200 <= resp.status_code < 400
    except Exception:
        return False


def _get_ok(url: str, timeout=DEFAULT_TIMEOUT) -> bool:
    try:
        with contextlib.closing(requests.get(url, stream=True, allow_redirects=True, timeout=timeout)) as resp:
            return 200 <= resp.status_code < 400
    except Exception:
        return False


def is_image_url_alive(url: str) -> bool:
    """
    Возвращает True, если по URL отвечает сервер 2xx/3xx.
    """
    if not url or not isinstance(url, str):
        return False
    # Сначала HEAD (быстро и дёшево)
    if _head_ok(url):
        return True
    # Некоторые CDN/сайты режут HEAD — даём второй шанс через GET stream
    return _get_ok(url)
