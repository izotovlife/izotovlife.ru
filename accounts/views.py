# backend/accounts/views.py
# Назначение: Вьюхи аутентификации (логин, профиль, регистрация, активация, восстановление пароля)
# Путь: backend/accounts/views.py

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView

from django.contrib.auth import get_user_model
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .serializers import (
    MyTokenObtainPairSerializer,
    AuthorDetailSerializer,
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

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


# ===== НОВЫЕ ВЬЮХИ =====

class RegisterView(APIView):
    """
    POST /api/auth/register/
    Регистрация пользователя, отправка email для активации.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(is_active=False)
            # Генерация ссылки активации
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = f"http://localhost:8000/api/auth/activate/{uid}/{token}/"

            # Рендерим письмо
            html_content = render_to_string("emails/activation_email.html", {
                "user": user,
                "activation_link": activation_link,
                "project_name": "IzotovLife",
            })

            msg = EmailMultiAlternatives(
                subject="Активация аккаунта IzotovLife",
                body="Пожалуйста, активируйте аккаунт.",
                from_email="noreply@izotovlife.ru",
                to=[user.email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            return Response({"detail": "Пользователь создан. Проверьте почту для активации."},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccountView(APIView):
    """
    GET /api/auth/activate/<uidb64>/<token>/
    Активация аккаунта по email.
    """
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"detail": "Ссылка недействительна."}, status=400)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            # после активации редиректим на фронт
            return redirect("http://localhost:3001/login")
        else:
            return Response({"detail": "Ссылка недействительна или устарела."}, status=400)


class PasswordResetRequestView(APIView):
    """
    POST /api/auth/password-reset/
    Запрос на восстановление пароля (отправка email).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Пользователь с таким email не найден."}, status=404)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"http://localhost:3001/reset-password/{uid}/{token}/"

        html_content = render_to_string("emails/reset_password_email.html", {
            "user": user,
            "reset_link": reset_link,
            "project_name": "IzotovLife",
        })

        msg = EmailMultiAlternatives(
            subject="Восстановление пароля IzotovLife",
            body="Ссылка для сброса пароля.",
            from_email="noreply@izotovlife.ru",
            to=[user.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        return Response({"detail": "Письмо для восстановления отправлено."}, status=200)


class PasswordResetConfirmView(APIView):
    """
    POST /api/auth/password-reset-confirm/<uidb64>/<token>/
    Подтверждение сброса пароля.
    """
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data["password"]

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"detail": "Ссылка недействительна."}, status=400)

        if default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response({"detail": "Пароль успешно изменён."}, status=200)
        else:
            return Response({"detail": "Ссылка недействительна или устарела."}, status=400)
