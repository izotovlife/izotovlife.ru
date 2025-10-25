# backend/news/image_proxy.py
# Описание: Вспомогательные функции для безопасного скачивания внешних изображений и кэширования оригиналов.

import hashlib
import mimetypes
import os
from urllib.parse import urlparse

import requests
from django.conf import settings

ALLOWED_SCHEMES = {"http", "https"}

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8"), usedforsecurity=False).hexdigest()

def safe_ext_from_ct(content_type: str, fallback: str = "jpg") -> str:
    if not content_type:
        return fallback
    ct = content_type.split(";")[0].strip().lower()
    if ct == "image/jpeg":
        return "jpg"
    if ct == "image/png":
        return "png"
    if ct == "image/webp":
        return "webp"
    if ct == "image/avif":
        return "avif"
    if ct == "image/gif":
        return "gif"
    # Попробуем по mimetypes
    ext = mimetypes.guess_extension(ct) or ""
    if ext.startswith("."):
        ext = ext[1:]
    return ext or fallback

def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def cached_original_path_for(url: str) -> str:
    key = sha1(url)
    folder = os.path.join(settings.THUMB_CACHE_DIR, "orig")
    ensure_dir(folder)
    # расширение определим после скачивания по Content-Type
    return os.path.join(folder, key)

def download_original(url: str) -> str:
    """
    Скачивает внешнюю картинку (если ещё не скачана) в кэш и возвращает путь к файлу.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError("URL scheme not allowed")

    base_path = cached_original_path_for(url)
    # проверим, не лежит ли уже файл с любым известным расширением
    for ext in ("jpg", "jpeg", "png", "webp", "avif", "gif"):
        probe = f"{base_path}.{ext}"
        if os.path.exists(probe) and os.path.getsize(probe) > 0:
            return probe

    # качаем
    r = requests.get(url, timeout=getattr(settings, "THUMB_REQUEST_TIMEOUT", (5, 10)), stream=True)
    r.raise_for_status()

    max_bytes = getattr(settings, "THUMB_MAX_ORIGINAL_BYTES", 8 * 1024 * 1024)
    total = 0
    chunks = []
    for chunk in r.iter_content(8192):
        if chunk:
            total += len(chunk)
            if total > max_bytes:
                r.close()
                raise ValueError("Original image too large")
            chunks.append(chunk)

    content = b"".join(chunks)
    ext = safe_ext_from_ct(r.headers.get("Content-Type"), "jpg")
    final_path = f"{base_path}.{ext}"
    with open(final_path, "wb") as f:
        f.write(content)
    return final_path
