# Путь: backend/image_guard/utils.py
# Назначение: Низкоуровневая проверка изображений по URL/файлу. Быстро, без лишнего трафика.

from __future__ import annotations

import os
import mimetypes
from dataclasses import dataclass
from io import BytesIO
from urllib.parse import urlparse

import requests
from PIL import Image, ImageFile


# Чтобы Pillow мог распознать неполные потоки, не требуя докачки всего файла
ImageFile.LOAD_TRUNCATED_IMAGES = True


@dataclass
class ImageCheckResult:
    ok: bool
    reason: str = ""
    status_code: int | None = None
    content_type: str | None = None
    width: int | None = None
    height: int | None = None
    bytes_read: int = 0
    url: str | None = None
    path: str | None = None


DEFAULT_TIMEOUT = (4, 10)  # (connect, read) seconds
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "ru,en;q=0.9",
}


def _sniff_pillow(img_bytes: bytes) -> tuple[int | None, int | None]:
    """
    Быстро «подсматриваем» размеры, не докачивая полный файл.
    Возвращает (width, height) или (None, None), если не удалось.
    """
    try:
        parser = ImageFile.Parser()
        parser.feed(img_bytes)
        im = parser.close()
        if getattr(im, "size", None):
            return im.size
    except Exception:
        pass
    try:
        im = Image.open(BytesIO(img_bytes))
        return im.size
    except Exception:
        return (None, None)


def is_url(value: str) -> bool:
    try:
        p = urlparse(value)
        return p.scheme in ("http", "https")
    except Exception:
        return False


def check_remote_image(
    url: str,
    min_width: int = 80,
    min_height: int = 80,
    max_bytes: int = 512 * 1024,  # считываем до 512КБ
) -> ImageCheckResult:
    """
    Проверяет доступность и валидность удалённой картинки по URL без полной докачки.
    Условия валидности:
      - HTTP < 400
      - Content-Type image/* (SVG пропускаем по заголовку)
      - Первые считанные байты распознаются как изображение Pillow
      - Размеры >= min_width/min_height (если удалось распознать)
    """
    try:
        with requests.get(
            url, stream=True, timeout=DEFAULT_TIMEOUT, headers=DEFAULT_HEADERS, allow_redirects=True
        ) as r:
            status = r.status_code
            ctype = r.headers.get("Content-Type", "")
            if status >= 400:
                return ImageCheckResult(False, f"HTTP {status}", status_code=status, content_type=ctype, url=url)

            # SVG: часто приходит как корректная картинка, Pillow её не открывает — пропускаем по типу
            if "image/svg" in ctype:
                return ImageCheckResult(True, "SVG content-type", status_code=status, content_type=ctype, url=url)

            if not ctype.startswith("image/"):
                # Иногда прокси отдают HTML-заглушку 200 OK — это не картинка
                # Пробуем всё равно дочитать немного и понюхать Pillow
                pass

            buf = BytesIO()
            bytes_read = 0
            chunk_size = 16384
            for chunk in r.iter_content(chunk_size=chunk_size):
                if not chunk:
                    break
                buf.write(chunk)
                bytes_read += len(chunk)
                if bytes_read >= max_bytes:
                    break

            data = buf.getvalue()
            w, h = _sniff_pillow(data)
            if w is None or h is None:
                return ImageCheckResult(False, "Не похоже на изображение", status_code=status, content_type=ctype, bytes_read=bytes_read, url=url)

            if (w < min_width) or (h < min_height):
                return ImageCheckResult(False, f"Слишком маленькое изображение {w}x{h}", status_code=status, content_type=ctype, width=w, height=h, bytes_read=bytes_read, url=url)

            return ImageCheckResult(True, "OK", status_code=status, content_type=ctype, width=w, height=h, bytes_read=bytes_read, url=url)
    except requests.RequestException as e:
        return ImageCheckResult(False, f"Network error: {e}", url=url)
    except Exception as e:
        return ImageCheckResult(False, f"Error: {e}", url=url)


def check_local_image(
    path: str,
    min_width: int = 80,
    min_height: int = 80,
) -> ImageCheckResult:
    """Проверка локального файла (если у вас ImageField с реальными файлами на диске)."""
    try:
        if not os.path.exists(path):
            return ImageCheckResult(False, "Файл не найден", path=path)
        with Image.open(path) as im:
            w, h = im.size
            if (w < min_width) or (h < min_height):
                return ImageCheckResult(False, f"Слишком маленькое изображение {w}x{h}", width=w, height=h, path=path)
        # content-type по расширению
        ctype = mimetypes.guess_type(path)[0] or "image/*"
        return ImageCheckResult(True, "OK", content_type=ctype, path=path)
    except Exception as e:
        return ImageCheckResult(False, f"Pillow error: {e}", path=path)


def pick_image_attr(instance) -> str | None:
    """
    Находит подходящее поле с картинкой у объекта новости.
    Пытается по популярным именам, ничего не удаляет.
    """
    candidates = ["image", "image_url", "cover", "thumbnail", "top_image", "photo"]
    for name in candidates:
        if hasattr(instance, name):
            val = getattr(instance, name)
            # ImageFieldFile -> берём .url
            if hasattr(val, "url"):
                return name
            # Строка URL
            if isinstance(val, str) and val.strip():
                return name
    return None
