# backend/accounts/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

from .serializers import UserSerializer, RegisterSerializer
from backend.views_security import _make_token, _cache_set_token, TOKEN_TTL_SECONDS

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Просмотр и редактирование профиля текущего пользователя.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SuperuserAdminLinkView(APIView):
    """Создание одноразовой ссылки в админку для суперпользователя."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if not user.is_superuser:
            return Response({"error": "Not a superuser"}, status=403)

        token = _make_token()
        _cache_set_token(token, {
            "user_id": user.id,
            "created": timezone.now().isoformat(),
        })

        # Адрес бэкенда берём из settings или по умолчанию 127.0.0.1:8000
        backend_base = getattr(settings, "BACKEND_BASE_URL", "http://127.0.0.1:8000")
        url = f"{backend_base}/admin/{token}/"

        return Response({"url": url, "expires_in": TOKEN_TTL_SECONDS})
