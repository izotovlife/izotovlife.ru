# Путь: backend/news/utils/image_tools.py
# Назначение: Утилиты для безопасной загрузки, ресайза/кадра и кодирования изображений.
# Особенности:
#   - fetch_image(): аккуратно тянет внешнее изображение с таймаутами и проверкой Content-Type
#   - resize_fit(): режимы "cover" и "contain" с центрированием
#   - make_placeholder(): генерирует плейсхолдер (Pillow) с текстом (например, название категории/новости)
#   - encode_image(): кодирует в WEBP/JPEG/PNG
#   - get_thumbnail_bytes(): единая точка — вернуть байты готового превью или плейсхолдера
#   - простое кэширование “плохих” урлов через Django cache, чтобы не ддосить источники

import io
import math
from typing import Optional, Tuple

import requests
from PIL import Image, ImageDraw, ImageFont
from django.core.cache import cache

SAFE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
UA = "IzotovLifeThumbnailer/1.0 (+https://izotovlife.ru)"
BAD_CACHE_TTL = 6 * 60 * 60        # 6 часов
OK_CACHE_TTL = 60 * 60             # 1 час
DEFAULT_BG = (10, 15, 26)          # темно-синий фон под плейсхолдер
DEFAULT_FG = (230, 235, 245)

def fetch_image(url: str, timeout: float = 4.0) -> Image.Image:
    """
    Скачивает изображение по URL, валидирует заголовки. Исключение -> считаем “плохим” урлом.
    """
    bad_key = f"img_bad:{url}"
    if cache.get(bad_key):
        raise ValueError("cached bad image")

    try:
        resp = requests.get(
            url,
            stream=True,
            timeout=timeout,
            headers={"User-Agent": UA, "Accept": "image/*"},
        )
        resp.raise_for_status()
        ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype not in SAFE_TYPES:
            raise ValueError(f"unsupported content-type: {ctype}")

        content = resp.content
        img = Image.open(io.BytesIO(content))
        # приводим к RGB для унификации кодирования
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        return img

    except Exception:
        cache.set(bad_key, True, BAD_CACHE_TTL)
        raise


def resize_fit(img: Image.Image, w: int, h: int, fit: str = "cover", bg=DEFAULT_BG) -> Image.Image:
    """
    Приведение к нужному размеру. fit="cover" — обрезаем края, fit="contain" — добавляем поля.
    """
    w = max(1, int(w))
    h = max(1, int(h))
    fit = (fit or "cover").lower()

    if fit == "contain":
        canvas = Image.new("RGB", (w, h), color=bg)
        img_ratio = img.width / img.height
        box_ratio = w / h
        if img_ratio > box_ratio:
            # ограничиваем шириной
            new_w = w
            new_h = max(1, int(w / img_ratio))
        else:
            new_h = h
            new_w = max(1, int(h * img_ratio))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        x = (w - new_w) // 2
        y = (h - new_h) // 2
        canvas.paste(resized, (x, y))
        return canvas

    # cover - обрежем излишки
    img_ratio = img.width / img.height
    box_ratio = w / h
    if img_ratio > box_ratio:
        # изображение “шире” — режем по ширине
        new_h = h
        new_w = max(1, int(h * img_ratio))
    else:
        new_w = w
        new_h = max(1, int(w / img_ratio))
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    # центрируем и кропим
    left = (new_w - w) // 2
    top = (new_h - h) // 2
    right = left + w
    bottom = top + h
    return resized.crop((left, top, right, bottom))


def _fit_font(draw: ImageDraw.ImageDraw, text: str, box_w: int, box_h: int) -> ImageFont.FreeTypeFont:
    """
    Подбирает примерный размер шрифта под прямоугольник.
    Используем встроенный PIL-шрифт, чтобы не таскать TTF.
    """
    # PIL-шрифт без TTF — моноширинный, размер примерим эвристикой:
    # ширина символа ~0.6 * size, высота строки ~1.2 * size
    # хотим, чтобы строка вместилась по ширине и по высоте.
    if not text:
        text = "Нет изображения"
    words = text.strip()
    if len(words) > 64:
        words = words[:64] + "…"

    # попробуем несколько размеров
    for size in range(72, 8, -2):
        font = ImageFont.load_default()
        # load_default не масштабируется; эмулируем через коэффициенты отрисовки
        # Поэтому ограничимся простым подсчётом, чтобы не уходить в сложность.
        # Визуально поджимаем шрифт количеством строк.
        lines = []
        line = ""
        for ch in words:
            if len(line) > 16 and ch == " ":
                lines.append(line)
                line = ""
            else:
                line += ch
        if line:
            lines.append(line)

        calc_h = int(len(lines) * (size * 1.2))
        calc_w = int(min(0.6 * size * max(len(l) for l in lines), box_w * 0.9))
        if calc_w <= box_w and calc_h <= box_h:
            return font

    return ImageFont.load_default()


def make_placeholder(w: int, h: int, text: Optional[str] = None,
                     bg=DEFAULT_BG, fg=DEFAULT_FG) -> Image.Image:
    """
    Генерирует простой плейсхолдер (фон + текст по центру).
    """
    w = max(1, int(w))
    h = max(1, int(h))
    img = Image.new("RGB", (w, h), color=bg)
    draw = ImageDraw.Draw(img)

    title = (text or "Нет изображения").strip()
    # примитивная центровка: разобьём на 2–3 строки
    words = title.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + 1 + len(word) > 16:
            lines.append(current.strip())
            current = word
        else:
            current += " " + word if current else word
    if current:
        lines.append(current.strip())
    if not lines:
        lines = ["Нет", "изображения"]

    # высчитаем вертикальные позиции
    line_height = max(14, int(h * 0.12))
    total_height = len(lines) * line_height + (len(lines) - 1) * int(line_height * 0.25)
    y = (h - total_height) // 2

    for line in lines:
        # ширина символа ~0.6*line_height
        est_w = int(len(line) * line_height * 0.6)
        x = (w - est_w) // 2
        draw.text((x, y), line, fill=fg)
        y += int(line_height * 1.25)

    return img


def encode_image(img: Image.Image, fmt: str = "webp", quality: int = 82) -> Tuple[bytes, str]:
    """
    Кодирует изображение в указанный формат (webp/jpeg/png).
    Возвращает (bytes, content_type).
    """
    fmt = (fmt or "webp").lower()
    if fmt == "png":
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue(), "image/png"
    if fmt == "jpg" or fmt == "jpeg":
        buf = io.BytesIO()
        img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=max(1, min(95, int(quality or 82))), optimize=True, progressive=True)
        return buf.getvalue(), "image/jpeg"

    # webp по умолчанию
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=max(1, min(100, int(quality or 82))))
    return buf.getvalue(), "image/webp"


def get_thumbnail_bytes(src: Optional[str], w: int, h: int,
                        fit: str = "cover", fmt: str = "webp", quality: int = 82,
                        text: Optional[str] = None) -> Tuple[bytes, str]:
    """
    Универсальная точка: получаем байты готового превью или плейсхолдера.
    Всегда возвращает валидную картинку и content-type.
    """
    if not src:
        ph = make_placeholder(w, h, text=text)
        return encode_image(ph, fmt=fmt, quality=quality)

    try:
        img = fetch_image(src)
        img = resize_fit(img, w, h, fit=fit)
        return encode_image(img, fmt=fmt, quality=quality)
    except Exception:
        ph = make_placeholder(w, h, text=text)
        return encode_image(ph, fmt=fmt, quality=quality)
