# Путь: backend/news/views_suggest.py
# Назначение: Обработка формы "Предложить новость" (SuggestNewsView) в рамках существующего приложения news.
# Особенности:
#   ✅ Принимает POST с JSON и multipart/form-data (фото/видео)
#   ✅ Поддерживает ключи файлов: image / image_file / photo и video / video_file
#   ✅ reCAPTCHA v2/v3: серверная проверка, без хардкода секрета (берём из settings)
#   ✅ Уникальный slug (slugify + unidecode) с защитой от коллизий
#   ✅ Категория: из slug, иначе 'bez-kategorii' (если есть), иначе None
#   ✅ Уникальный link (user://suggestion/<uuid4>) для безопасной идентификации
#   ✅ Сохранение только тех полей ImportedNews, которые реально существуют
#   ✅ Возвращает { ok, id, slug, detail_url } или осмысленную 4xx-ошибку

from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from unidecode import unidecode
import requests
import uuid
import re

# Импортируй свои модели. Если у тебя другие пути — поправь импорт.
from .models import ImportedNews, Category

RECAPTCHA_VERIFY_URL = getattr(settings, "RECAPTCHA_VERIFY_URL", "https://www.google.com/recaptcha/api/siteverify")
RECAPTCHA_SECRET_KEY = getattr(settings, "RECAPTCHA_SECRET_KEY", "")

# Ключи, которые может прислать фронт
IMG_KEYS = ("image", "image_file", "photo")
VID_KEYS = ("video", "video_file")
CAPTCHA_KEYS = ("recaptcha_token", "g-recaptcha-response", "recaptcha", "captcha")


def _pick_file(request_files, keys):
    """Возвращает первый непустой файл по списку ключей."""
    for k in keys:
        f = request_files.get(k)
        if f:
            return f
    return None


def _pick_value(data, keys):
    """Возвращает первое непустое значение по списку ключей."""
    for k in keys:
        v = data.get(k)
        if v:
            return v
    return None


def _slugify_title(title: str, limit: int = 60) -> str:
    base = slugify(unidecode(title or ""))[:limit] or str(int(timezone.now().timestamp()))
    base = re.sub(r"-+", "-", base).strip("-")
    return base or "suggestion"


def _unique_slug(base: str) -> str:
    slug = base
    i = 1
    while ImportedNews.objects.filter(slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug


def _resolve_category(slug: str | None):
    """Возвращает Category или None. Если не дали slug — попробуем 'bez-kategorii'."""
    if slug:
        try:
            return Category.objects.get(slug=str(slug).strip().lower())
        except Category.DoesNotExist:
            pass
    # Попробуем дефолтную «без категории», если заведена
    try:
        return Category.objects.get(slug="bez-kategorii")
    except Category.DoesNotExist:
        return None


def _verify_recaptcha(token: str, remote_ip: str | None = None):
    """
    Проверяем reCAPTCHA v2/v3. Возвращает (ok: bool, err: dict|None, meta: dict).
    Для v3 учитываем score (порог 0.3).
    """
    if not RECAPTCHA_SECRET_KEY:
        # Ключ не настроен — считаем, что проверка отключена (в DEV), не падаем.
        return True, None, {"disabled": True}

    if not token:
        return False, {"detail": "captcha token required"}, None

    try:
        resp = requests.post(
            RECAPTCHA_VERIFY_URL,
            data={"secret": RECAPTCHA_SECRET_KEY, "response": token, "remoteip": remote_ip},
            timeout=5,
        )
        data = resp.json()
    except Exception:
        return False, {"detail": "captcha verification error"}, None

    if not data.get("success"):
        return False, {"detail": "captcha failed", "raw": data}, None

    # v3: есть score/action — применим простой порог
    score = data.get("score")
    if score is not None and float(score) < 0.3:
        return False, {"detail": "captcha score too low", "score": score}, None

    return True, None, {"score": score, "action": data.get("action")}


class SuggestNewsView(APIView):
    """
    API для пользовательских предложений новости.
    Поддерживаемые поля (любые из):
      - title (обязательно)
      - summary / message (одно из, необязательно)
      - category (slug категории, необязательно)
      - image | image_file | photo (файл-изображение, необязательно)
      - video | video_file (файл-видео, необязательно)
      - recaptcha_token | g-recaptcha-response | recaptcha | captcha (обязательно, если настроен секрет)
      - link (необязательно; если не дан — сгенерируем уникальный)
      - phone / email / first_name / last_name (если присланы — можно сохранить позже в отдельную модель)
    """
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    authentication_classes = []  # анонимам разрешаем
    permission_classes = []

    def post(self, request, *args, **kwargs):
        data = request.data

        # --- 1) Заголовок
        title = (data.get("title") or "").strip()
        if not title:
            return Response({"detail": "Поле 'title' обязательно"}, status=status.HTTP_400_BAD_REQUEST)

        # --- 2) reCAPTCHA
        token = _pick_value(data, CAPTCHA_KEYS)
        ok, err, meta = _verify_recaptcha(token, request.META.get("REMOTE_ADDR"))
        if not ok:
            return Response(err, status=status.HTTP_400_BAD_REQUEST)

        # --- 3) Summary / message
        summary = (data.get("summary") or data.get("message") or "").strip()
        if summary and len(summary) > 5000:
            summary = summary[:5000] + "…"

        # --- 4) Категория
        category_slug = (data.get("category") or "").strip().lower() or None
        category = _resolve_category(category_slug)

        # --- 5) Файлы
        image_file = _pick_file(request.FILES, IMG_KEYS)
        video_file = _pick_file(request.FILES, VID_KEYS)

        # (мягкие лимиты — по желанию)
        if hasattr(image_file, "size") and image_file.size > 10 * 1024 * 1024:  # 10 MB
            return Response({"image": "Слишком большой файл изображения (>10MB)."}, status=status.HTTP_400_BAD_REQUEST)
        if hasattr(video_file, "size") and video_file.size > 150 * 1024 * 1024:  # 150 MB
            return Response({"video": "Слишком большой видеофайл (>150MB)."}, status=status.HTTP_400_BAD_REQUEST)

        # --- 6) Уникальный slug
        base = _slugify_title(title)
        new_slug = _unique_slug(base)

        # --- 7) Уникальный link (без коллизий с реальными ссылками)
        link = (data.get("link") or "").strip()
        if not link:
            # безопасный "виртуальный" линк — не пересечётся с реальными URL источников
            link = f"user://suggestion/{uuid.uuid4()}"

        # --- 8) Сохранение (только существующие поля модели)
        fields = {
            "title": title,
            "summary": summary or "",
            "slug": new_slug,
            "link": link,
            "published_at": timezone.now(),  # черновик — но дата пригодится для сортировки
        }
        if category is not None and hasattr(ImportedNews, "category"):
            fields["category"] = category
        if image_file is not None and hasattr(ImportedNews, "image"):
            fields["image"] = image_file
        if video_file is not None and hasattr(ImportedNews, "video"):
            fields["video"] = video_file

        news = ImportedNews.objects.create(**fields)

        # --- 9) Соберём удобный detail_url для фронта
        # Если в модели есть свойство seo_path — используем его, иначе короткий роут /news/<slug>/
        detail_url = None
        if hasattr(news, "seo_path") and getattr(news, "seo_path"):
            detail_url = news.seo_path
        else:
            detail_url = f"/news/{news.slug}/"

        payload = {
            "ok": True,
            "id": news.id,
            "slug": news.slug,
            "detail_url": detail_url,
        }
        if meta and settings.DEBUG:
            # В проде не светим score/action, а в DEBUG чуть поможем себе
            payload["captcha"] = meta

        return Response(payload, status=status.HTTP_201_CREATED)
