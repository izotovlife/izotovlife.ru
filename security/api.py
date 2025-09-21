# backend/security/api.py
# Назначение: API для генерации одноразового admin_url для суперпользователя.
# Путь: backend/security/api.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.urls import reverse
from django.utils import timezone

from .models import AdminSessionToken

class AdminSessionLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not user.is_superuser:
            return Response({"detail": "Доступ запрещён"}, status=403)

        token = AdminSessionToken.objects.create(user=user, created_at=timezone.now())
        admin_url = reverse("security:admin_entrypoint", args=[str(token.token)])
        return Response({"admin_url": admin_url})
