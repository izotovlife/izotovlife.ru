# backend/accounts/views.py
# Назначение: Вьюхи аутентификации (логин, профиль) и публичные страницы авторов.
# Путь: backend/accounts/views.py

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from django.contrib.auth import get_user_model

from .serializers import MyTokenObtainPairSerializer, AuthorDetailSerializer

User = get_user_model()


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Авторизация пользователя. Возвращает JWT-токены.
    """
    permission_classes = [AllowAny]
    serializer_class = MyTokenObtainPairSerializer


class MeView(APIView):
    """
    GET /api/auth/me/
    Возвращает информацию о текущем пользователе.
    Для всех пользователей добавляет redirect_url для фронта.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        data = {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": getattr(u, "role", None),
            "photo": getattr(u, "photo", None),
            "bio": getattr(u, "bio", ""),
            "is_superuser": u.is_superuser,
        }

        # ✅ правильная проверка с учётом enums
        if u.is_superuser:
            data["redirect_url"] = "/admin/"
        elif getattr(u, "role", None) == User.Roles.AUTHOR:
            data["redirect_url"] = "/author/dashboard"
        elif getattr(u, "role", None) == User.Roles.EDITOR:
            data["redirect_url"] = "/editor/dashboard"
        elif getattr(u, "role", None) == User.Roles.ADMIN:
            data["redirect_url"] = "/admin/"
        else:
            data["redirect_url"] = "/"

        return Response(data)


class AuthorDetailView(APIView):
    """
    GET /api/authors/<id>/
    Публичная страница автора: фото, имя, био, список статей.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk, role=User.Roles.AUTHOR)
        except User.DoesNotExist:
            return Response({"detail": "Автор не найден"}, status=404)
        serializer = AuthorDetailSerializer(user, context={"request": request})
        return Response(serializer.data)
