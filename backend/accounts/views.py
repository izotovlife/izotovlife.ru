# ===== ФАЙЛ: backend/accounts/views.py =====
# НАЗНАЧЕНИЕ: Регистрация, профиль и единая точка входа для авторов и администратора.

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone

from backend.views_security import _make_token, _cache_set_token, TOKEN_TTL_SECONDS
from .serializers import UserSerializer, RegisterSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class ProfileView(generics.RetrieveAPIView):
    """Профиль текущего авторизованного пользователя"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LoginView(APIView):
    """
    Универсальная точка входа:
      - обычным пользователям возвращает JWT-токены,
      - суперпользователю выдаёт одноразовую ссылку в админку.
    """

    permission_classes = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            return Response(
                {"detail": "Username and password required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_superuser:
            token = _make_token()
            _cache_set_token(
                token,
                {"user_id": user.id, "created": timezone.now().isoformat()},
            )
            return Response(
                {
                    "admin_url": f"/admin/{token}/",
                    "expires_in": TOKEN_TTL_SECONDS,
                }
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {"access": str(refresh.access_token), "refresh": str(refresh)}
        )
