# Путь: news/views_suggest.py
# Назначение: обработка формы "Предложить новость" и отправка письма редакции IzotovLife.
# Особенности:
#   ✅ Полностью независима от JWT и CSRF (csrf_exempt, authentication_classes = []).
#   ✅ Работает даже с axios без withCredentials.
#   ✅ Возвращает {"ok": true} при успехе.

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils.html import strip_tags
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, throttling, serializers
import re


# --- Сериалайзер формы ---
class SuggestNewsSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=50, allow_blank=True, required=False)
    message = serializers.CharField()
    website = serializers.CharField(max_length=100, allow_blank=True, required=False)

    def validate_message(self, value):
        value = value.strip()
        if len(value) < 15:
            raise serializers.ValidationError("Опишите новость подробнее (минимум 15 символов).")
        return value


# --- Ограничения частоты ---
class BurstThrottle(throttling.UserRateThrottle):
    scope = "suggest_burst"


class SustainedThrottle(throttling.UserRateThrottle):
    scope = "suggest_sustained"


# --- Основной обработчик ---
@method_decorator(csrf_exempt, name="dispatch")
class SuggestNewsView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # ✅ Полностью убираем JWT и Session
    throttle_classes = [BurstThrottle, SustainedThrottle]

    def post(self, request, *args, **kwargs):
        print("✅ SuggestNewsView POST получен (CSRF отключен)")  # отладка

        serializer = SuggestNewsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # honeypot
        if data.get("website"):
            return Response({"ok": True})

        # поля
        first_name = data["first_name"].strip()
        last_name = data["last_name"].strip()
        email = data["email"].strip()
        phone = (data.get("phone") or "").strip()
        message = data["message"].strip()

        # письмо
        subject = f"[IzotovLife] Предложение новости от {first_name} {last_name}"
        to_email = getattr(settings, "SUGGEST_NEWS_EMAIL_TO", "izotovlife@yandex.ru")

        html = (
            f"<h2>Предложение новости</h2>"
            f"<p><b>Имя:</b> {first_name}<br>"
            f"<b>Фамилия:</b> {last_name}<br>"
            f"<b>Email:</b> {email}<br>"
            f"<b>Телефон:</b> {phone or '-'}<br></p>"
            f"<hr><div style='white-space:pre-wrap;font-family:system-ui'>{message}</div>"
        )

        try:
            mail = EmailMessage(
                subject=subject,
                body=html,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@izotovlife.local"),
                to=[to_email],
                reply_to=[email],
            )
            mail.content_subtype = "html"
            mail.send(fail_silently=False)
        except Exception as e:
            print(f"Ошибка при отправке письма: {e}")
            return Response({"ok": False, "error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"ok": True}, status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        """Для теста: GET /api/news/suggest/ возвращает OK"""
        return Response({"detail": "SuggestNewsView работает (GET ok)."})
