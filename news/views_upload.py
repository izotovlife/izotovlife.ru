# backend/news/views_upload.py
# Назначение: Загрузка изображений для редактора Quill с уникальными именами.
# Путь: backend/news/views_upload.py

import os
import uuid
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


@api_view(["POST"])
@permission_classes([IsAuthenticated])  # доступ только авторизованным
def upload_image(request):
    """
    POST /api/news/upload-image/
    Принимает файл (FormData: image), сохраняет и возвращает URL.
    """
    file = request.FILES.get("image")
    if not file:
        return JsonResponse({"error": "Файл не найден"}, status=400)

    # Генерируем уникальное имя файла
    ext = os.path.splitext(file.name)[1].lower()  # расширение (.jpg, .png)
    fname = f"{uuid.uuid4().hex}{ext}"

    # Сохраняем в папку media/articles/
    save_path = os.path.join("articles", fname)
    full_path = default_storage.save(save_path, file)

    # Формируем URL (например: /media/articles/uuid.png)
    url = settings.MEDIA_URL + full_path

    return JsonResponse({"url": url})

