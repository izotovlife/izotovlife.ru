# Путь: backend/news/views_suggest.py
# Назначение: Обработка формы "Предложить новость" (SuggestNewsView)
# Особенности:
#   ✅ Принимает POST-запросы с JSON и multipart/form-data
#   ✅ Поддержка файлов: image и video
#   ✅ Проверка капчи
#   ✅ Создает черновик импортированной новости
#   ✅ Автоопределение категории, slug, даты публикации
#   ✅ Авто-генерация уникального link для предложенных новостей
#   ✅ Возвращает JSON с результатом или ошибкой

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ImportedNews, Category
from django.utils import timezone
from unidecode import unidecode
from django.utils.text import slugify
import re
import uuid
import requests

# Настройки капчи (например, Google reCAPTCHA v2)
RECAPTCHA_SECRET_KEY = "ВАШ_СЕКРЕТНЫЙ_КЛЮЧ_RECAPTCHA"

class SuggestNewsView(APIView):
    """
    API для отправки новости пользователем.
    Поддерживает:
    - title (обязательный)
    - summary (опционально)
    - category (опционально, slug категории)
    - image (опционально, файл)
    - video (опционально, файл)
    - recaptcha_token (обязательный)
    """

    def post(self, request, *args, **kwargs):
        data = request.data

        # 🔹 Проверка обязательного поля title
        title = data.get("title")
        if not title:
            return Response({"detail": "Поле 'title' обязательно"}, status=status.HTTP_400_BAD_REQUEST)

        # 🔹 Проверка капчи
        recaptcha_token = data.get("recaptcha_token")
        if not recaptcha_token:
            return Response({"detail": "Капча обязательна"}, status=status.HTTP_400_BAD_REQUEST)

        recaptcha_response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": RECAPTCHA_SECRET_KEY, "response": recaptcha_token}
        ).json()

        if not recaptcha_response.get("success"):
            return Response({"detail": "Неверная капча"}, status=status.HTTP_400_BAD_REQUEST)

        summary = data.get("summary", "")
        category_slug = data.get("category")

        # 🔹 Определяем категорию
        category = None
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
            except Category.DoesNotExist:
                pass

        # 🔹 Создаем уникальный slug
        base_slug = slugify(unidecode(title))[:60] or str(timezone.now().timestamp())[:8]
        base_slug = re.sub(r"-+", "-", base_slug)
        new_slug = base_slug
        counter = 1
        while ImportedNews.objects.filter(slug=new_slug).exists():
            new_slug = f"{base_slug}-{counter}"
            counter += 1

        # 🔹 Генерация уникального link
        link = data.get("link")
        if not link:
            link = str(uuid.uuid4())

        # 🔹 Загружаемые файлы
        image_file = request.FILES.get("image")  # django ImageField
        video_file = request.FILES.get("video")  # django FileField для видео

        # 🔹 Создаем черновик новости
        news = ImportedNews.objects.create(
            title=title,
            summary=summary,
            category=category,
            slug=new_slug,
            link=link,
            published_at=timezone.now(),
            image=image_file or None,
            video=video_file or None,
        )

        return Response({
            "detail": "Новость успешно предложена",
            "id": news.id,
            "slug": news.slug,
            "seo_path": news.seo_path,
        }, status=status.HTTP_201_CREATED)
