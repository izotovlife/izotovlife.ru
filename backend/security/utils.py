# backend/security/utils.py

import secrets
from django.core.cache import cache

TOKEN_TTL_SECONDS = 600  # 10 минут (можно менять в settings при желании)


def _make_token() -> str:
    """Генерация безопасного одноразового токена."""
    return secrets.token_urlsafe(32)


def _cache_set_token(token: str, data: dict) -> None:
    """Сохраняем токен в кэш с TTL."""
    cache.set(token, data, timeout=TOKEN_TTL_SECONDS)


def _cache_get_token(token: str) -> dict | None:
    """Проверка токена в кэше."""
    return cache.get(token)


def _cache_invalidate_token(token: str) -> None:
    """Удаляем токен (например, после использования)."""
    cache.delete(token)

