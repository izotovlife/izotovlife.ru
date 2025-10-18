# Путь: backend/news/views_media.py
# Назначение: Прокси-ресайзер изображений. Делает миниатюры (WebP/JPEG/AVIF*), кэширует на диске,
#             защищает от SSRF (публичные IP), ставит Cache-Control/ETag/Last-Modified, умеет 304,
#             и — НОВОЕ — аккуратнее ходит к источнику: проставляет Referer хоста и пробует https при сбое http.
# Использование: /api/media/thumbnail/?src=<url_or_media_path>&w=480&h=270&fmt=webp&q=82&fit=cover
# Совместимость: ничего существующего НЕ удаляет. Только расширяет возможности скачивания.
# Обновления:
#   ✅ _make_headers(src): добавлен корректный Referer (схема+хост) и UA — меньше анти-хотлинк 403
#   ✅ _download_to_bytes: если http дал 403/404/415 — пробуем https (и наоборот), прежде чем сдаёмся
#   ✅ Остальная логика (ETag/304/Last-Modified/UnsharpMask/AVIF→WEBP fallback/SSRF) — без изменений

import hashlib
import io
import mimetypes
import os
import re
import time
import socket
from urllib.parse import urlparse, unquote

from django.conf import settings
from django.http import (
    FileResponse,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
)
from django.views.decorators.http import require_GET

from PIL import Image, ImageOps, ImageFilter
import requests
import ipaddress

# --- Настройки/пути кэша ---
MEDIA_CACHE_DIR = os.path.join(getattr(settings, "MEDIA_ROOT", "media"), "cache", "thumbs")
os.makedirs(MEDIA_CACHE_DIR, exist_ok=True)

# --- Базовые лимиты/качество ---
DEFAULT_QUALITY = 82
MAX_W, MAX_H = 4096, 2160
MAX_ORIGINAL_BYTES = 10 * 1024 * 1024  # 10MB
REQUEST_TIMEOUT = (6.0, 12.0)  # (connect, read)

# --- Простейшая защита от SSRF: запрещаем приватные/loopback адреса ---
_PRIVATE_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _is_safe_url(url: str) -> bool:
    try:
        u = urlparse(url)
        if u.scheme not in ("http", "https", ""):
            return False
        if not u.netloc:
            # относительные пути к MEDIA считаем безопасными здесь (проверим позже)
            return True
        # DNS → IP и проверка сетей
        infos = socket.getaddrinfo(u.hostname, None)
        ips = {info[4][0] for info in infos}
        for ip in ips:
            ip_obj = ipaddress.ip_address(ip)
            if any(ip_obj in n for n in _PRIVATE_NETS):
                return False
        return True
    except Exception:
        return False


def _make_headers(src_url: str) -> dict:
    """
    Собираем заголовки для запроса к источнику:
    - адекватный User-Agent
    - Referer на хост источника (многие борются с hotlink'ом и требуют реферер)
    """
    try:
        u = urlparse(src_url)
        referer = f"{u.scheme}://{u.netloc}/" if u.scheme and u.netloc else ""
    except Exception:
        referer = ""
    headers = {
        "User-Agent": "IzotovLife-ThumbProxy/1.0 (+https://izotovlife.ru)",
    }
    if referer:
        headers["Referer"] = referer
    return headers


def _download_to_bytes_once(url: str, timeout=REQUEST_TIMEOUT, max_bytes=MAX_ORIGINAL_BYTES) -> bytes:
    """Один заход загрузки. Поднимает исключение при любой проблеме."""
    headers = _make_headers(url)
    with requests.get(url, stream=True, timeout=timeout, headers=headers, allow_redirects=True) as r:
        r.raise_for_status()
        ct = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if not ct.startswith("image/"):
            # Иногда отдают HTML-заглушку / SVG без image/* — пробовать дальше смысла нет
            raise ValueError(f"content-type not image: {ct or 'unknown'}")
        total = 0
        bio = io.BytesIO()
        for chunk in r.iter_content(64 * 1024):
            if not chunk:
                continue
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("image too large")
            bio.write(chunk)
        return bio.getvalue()


def _flip_scheme(url: str) -> str | None:
    """Меняем http↔https, если возможно."""
    try:
        u = urlparse(url)
        if u.scheme == "http":
            return url.replace("http://", "https://", 1)
        if u.scheme == "https":
            return url.replace("https://", "http://", 1)
    except Exception:
        pass
    return None


def _download_to_bytes(url: str, timeout=REQUEST_TIMEOUT, max_bytes=MAX_ORIGINAL_BYTES) -> bytes:
    """
    Скачиваем картинку (стримом), ограничиваем размер, проверяем Content-Type.
    NEW: если первый заход не удался по типичным сетевым причинам (403/404/415/SSLError) —
         пробуем альтернативную схему (http↔https).
    """
    try:
        return _download_to_bytes_once(url, timeout=timeout, max_bytes=max_bytes)
    except Exception as e:
        msg = str(getattr(e, "args", [e])[0]).lower()
        try_alt = any(code in msg for code in ("403", "404", "415", "ssl", "certificate", "forbidden", "not found"))
        alt = _flip_scheme(url) if try_alt else None
        if alt:
            return _download_to_bytes_once(alt, timeout=timeout, max_bytes=max_bytes)
        raise


def _open_image_from_source(src: str) -> Image.Image:
    """Открываем PIL.Image из URL или MEDIA-файла, учитываем EXIF-ориентацию."""
    if re.match(r"^https?://", src or ""):
        if not _is_safe_url(src):
            raise ValueError("unsafe url")
        raw = _download_to_bytes(src)
        im = Image.open(io.BytesIO(raw))
        im = ImageOps.exif_transpose(im)
        return im

    # относительный путь внутри MEDIA_ROOT
    media_root = getattr(settings, "MEDIA_ROOT", "")
    if not media_root:
        raise FileNotFoundError("MEDIA_ROOT is not configured")
    abs_path = os.path.join(media_root, src.lstrip("/"))
    if not os.path.isfile(abs_path):
        raise FileNotFoundError("file not found")
    im = Image.open(abs_path)
    im = ImageOps.exif_transpose(im)
    return im


def _build_cache_key(src: str, w: int, h: int, q: int, fmt: str, fit: str, sharpen: int) -> str:
    hsh = hashlib.md5(f"{src}|{w}|{h}|{q}|{fmt}|{fit}|{sharpen}".encode("utf-8")).hexdigest()
    return hsh


def _send_file_cached(cache_path: str, etag: str):
    """Готовим FileResponse c корректными кэш-заголовками и 304 при If-None-Match."""
    resp = FileResponse(open(cache_path, "rb"), content_type=mimetypes.guess_type(cache_path)[0] or "image/webp")
    resp["Cache-Control"] = "public, max-age=31536000, immutable"  # 1 год
    resp["ETag"] = etag
    try:
        mtime = os.path.getmtime(cache_path)
        resp["Last-Modified"] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(mtime))
    except Exception:
        pass
    resp["X-Thumb-Cache"] = "HIT"
    return resp


@require_GET
def thumbnail_proxy(request):
    """
    Пример: /api/media/thumbnail/?src=https%3A%2F%2Fsite%2Fpic.jpg&w=480&h=270&fmt=webp&q=82&fit=cover&sharpen=1
    fit: cover | contain
    fmt: webp | jpeg | jpg | png | avif (если доступен)
    sharpen: 0..2 (0=нет, 1=умеренно, 2=сильнее)
    """
    src_raw = (request.GET.get("src") or "").strip()
    if not src_raw:
        return HttpResponseBadRequest("src required")

    # Мягко раскодируем src (вдруг он процентизирован)
    try:
        src = unquote(src_raw)
    except Exception:
        src = src_raw

    # размеры
    try:
        w = max(1, min(int(request.GET.get("w", "480")), MAX_W))
        h = max(1, min(int(request.GET.get("h", "270")), MAX_H))
    except Exception:
        return HttpResponseBadRequest("bad size")

    # формат
    fmt = (request.GET.get("fmt") or "webp").lower()
    if fmt not in ("webp", "jpeg", "jpg", "png", "avif"):
        fmt = "webp"
    # качество
    q = request.GET.get("q")
    try:
        q = int(q) if q is not None else DEFAULT_QUALITY
        q = max(40, min(q, 95))
    except Exception:
        q = DEFAULT_QUALITY

    # подрезка/вписывание
    fit = (request.GET.get("fit") or "cover").lower()
    if fit not in ("cover", "contain"):
        fit = "cover"

    # резкость
    try:
        sharpen = int(request.GET.get("sharpen", "1"))
        sharpen = max(0, min(sharpen, 2))
    except Exception:
        sharpen = 1

    cache_key = _build_cache_key(src, w, h, q, fmt, fit, sharpen)
    ext = ".webp" if fmt == "webp" else ".jpg" if fmt in ("jpg", "jpeg") else f".{fmt}"
    cache_path = os.path.join(MEDIA_CACHE_DIR, cache_key + ext)

    # 304 Not Modified по If-None-Match
    inm = (request.headers.get("If-None-Match") or "").strip()
    if os.path.isfile(cache_path):
        if inm and inm == cache_key:
            resp = HttpResponse(status=304)
            resp["ETag"] = cache_key
            resp["Cache-Control"] = "public, max-age=31536000, immutable"
            try:
                mtime = os.path.getmtime(cache_path)
                resp["Last-Modified"] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(mtime))
            except Exception:
                pass
            resp["X-Thumb-Cache"] = "HIT-304"
            return resp
        return _send_file_cached(cache_path, cache_key)

    # Генерация нового
    try:
        im = _open_image_from_source(src)

        # выбор цветового режима (сохраняем альфа где возможно)
        has_alpha = (im.mode in ("RGBA", "LA")) or ("transparency" in im.info)
        target_mode = "RGBA" if (fmt in ("png", "webp", "avif") and has_alpha) else "RGB"
        if target_mode == "RGB" and has_alpha:
            # композит по белому для JPEG
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[-1])
            im = bg
        else:
            im = im.convert(target_mode)

        # ресайз
        if fit == "cover":
            im = ImageOps.fit(im, (w, h), method=Image.LANCZOS, bleed=0.0, centering=(0.5, 0.5))
        else:
            im.thumbnail((w, h), Image.LANCZOS)

        # лёгкая резкость
        if sharpen == 1:
            im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=130, threshold=2))
        elif sharpen >= 2:
            im = im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=160, threshold=2))

        # сериализация
        os.makedirs(MEDIA_CACHE_DIR, exist_ok=True)
        buf = io.BytesIO()
        save_fmt = "WEBP" if fmt == "webp" else "JPEG" if fmt in ("jpg", "jpeg") else fmt.upper()
        save_kwargs = {"quality": q}

        if save_fmt == "WEBP":
            save_kwargs.update({"method": 6})
        if save_fmt == "AVIF":
            try:
                im.save(buf, save_fmt, **save_kwargs)
            except Exception:
                buf = io.BytesIO()
                save_fmt = "WEBP"
                save_kwargs = {"quality": q, "method": 6}
                im.save(buf, save_fmt, **save_kwargs)
        else:
            im.save(buf, save_fmt, **save_kwargs)

        data = buf.getvalue()
        with open(cache_path, "wb") as f:
            f.write(data)

        resp = HttpResponse(data, content_type=mimetypes.guess_type(cache_path)[0] or "image/webp")
        resp["Cache-Control"] = "public, max-age=31536000, immutable"
        resp["ETag"] = cache_key
        try:
            mtime = os.path.getmtime(cache_path)
            resp["Last-Modified"] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(mtime))
        except Exception:
            pass
        resp["X-Thumb-Cache"] = "MISS"
        return resp

    except FileNotFoundError as e:
        return HttpResponseNotFound(str(e))
    except ValueError as e:
        msg = str(e)
        if "too large" in msg:
            return HttpResponse(status=413, content=msg)  # Payload Too Large
        return HttpResponseBadRequest(f"thumbnail error: {msg}")
    except Exception as e:
        return HttpResponseBadRequest(f"thumbnail error: {e}")
