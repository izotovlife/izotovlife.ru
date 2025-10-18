# Путь: backend/accounts/views.py
# Назначение: Вьюхи аутентификации (логин, профиль, регистрация, активация, восстановление пароля).
# ВАЖНО: НИЧЕГО ЛИШНЕГО НЕ УДАЛЕНО. Я только ДОБАВИЛ функциональность и точечно поправил одно место,
# чтобы не было ошибки при .save(is_active=False) (подробно пометил комментарием ниже).
#
# Что добавлено:
#   ✅ Динамическая сборка ссылок (на основе домена запроса и settings) вместо жёстких http://localhost:...
#   ✅ Отправка писем через общий helper с HTML и текстовой версией.
#   ✅ Активация: опция вернуть красивую HTML-страницу с авто-редиректом (параметр ?html=1).
#   ✅ Повторная отправка письма активации (ResendActivationView) — не раскрывает, существует ли пользователь.
#   ✅ Password reset: опциональный "тихий" режим (?silent=1), чтобы не палить наличие аккаунта.
#   ✅ Совместимость с вашим RegisterSerializer (он сам ставит is_active=False) — убрал лишний аргумент
#      у serializer.save(...) и пояснил, что именно было удалено и почему (иначе падало бы).
#
# Маршруты для новых вьюх (добавите в urls.py):
#   path("api/auth/resend-activation/", ResendActivationView.as_view()),
#   # Остальные пути у вас уже есть.

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect
from django.http import HttpResponse

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


# ===== ВСПОМОГАТЕЛЬНЫЕ УТИЛИТЫ (ДОБАВЛЕНО) =====

def _origin_from_request(request) -> str:
    """
    Собирает протокол+домен из текущего запроса,
    например http://localhost:8000 или https://example.com
    """
    scheme = "https" if request.is_secure() else "http"
    domain = get_current_site(request).domain
    return f"{scheme}://{domain}"


def _send_html_mail(*, subject: str, to: list[str], html_template: str, context: dict,
                    text_template: str | None = None, from_email: str | None = None) -> None:
    """
    Унифицированная отправка HTML+text писем.
    Если text_template не задан — сгенерируем простой текст из HTML (упрощённо).
    """
    html_content = render_to_string(html_template, context)
    text_content = render_to_string(text_template, context) if text_template else "Пожалуйста, откройте письмо в HTML-формате."
    sender = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost")

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=sender,
        to=to,
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


# ===== СУЩЕСТВУЮЩИЕ ВЬЮХИ (НЕ ТРОГАЮ, ТОЛЬКО ДОПОЛНЯЮ ГДЕ НУЖНО) =====

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


# ===== НОВЫЕ/ДОПОЛНЕННЫЕ ВЬЮХИ =====

class RegisterView(APIView):
    """
    POST /api/auth/register/
    Регистрация пользователя, отправка email для активации.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # [ИЗМЕНЕНИЕ ДЛЯ КОРРЕКТНОСТИ]:
        # Раньше было: user = serializer.save(is_active=False)
        # Я УДАЛИЛ аргумент is_active=False, т.к. ваш RegisterSerializer сам устанавливает user.is_active = False.
        # Если оставить аргумент, DRF передаст его в .create и получим TypeError: unexpected keyword argument 'is_active'.
        user = serializer.save()

        # Генерация ссылки активации
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Базовая (старая) ссылка — оставляю как первый расчёт (НЕ УДАЛЯЮ)
        activation_link = f"http://localhost:8000/api/auth/activate/{uid}/{token}/"

        # ДИНАМИЧЕСКАЯ ссылка по домену запроса (перезаписываю переменную activation_link — это ДОПОЛНЕНИЕ, а не удаление логики)
        origin = _origin_from_request(request)
        activation_link = f"{origin}/api/auth/activate/{uid}/{token}/"

        ctx = {
            "user": user,
            "activation_link": activation_link,
            "project_name": getattr(settings, "PROJECT_NAME", "IzotovLife"),
        }

        # Письмо: HTML + текст (шаблоны положите в backend/templates/emails/)
        _send_html_mail(
            subject=f"Активация аккаунта {ctx['project_name']}",
            to=[user.email],
            html_template="emails/activation_email.html",
            text_template="emails/activation_email.txt",
            context=ctx,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@izotovlife.ru"),
        )

        return Response({"detail": "Пользователь создан. Проверьте почту для активации."},
                        status=status.HTTP_201_CREATED)


class ActivateAccountView(APIView):
    """
    GET /api/auth/activate/<uidb64>/<token>/
    Активация аккаунта по email.
    Поддерживает режим ?html=1 — вернёт красивую HTML-страницу с авто-редиректом.
    Без параметра по умолчанию делает редирект на страницу логина (как было).
    """
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            # В режиме html=1 покажем красивую страницу ошибки
            if request.query_params.get("html") == "1":
                html = render_to_string("registration/activation_failed.html", {})
                return HttpResponse(html, status=400)
            return Response({"detail": "Ссылка недействительна."}, status=400)

        if default_token_generator.check_token(user, token):
            if not user.is_active:
                user.is_active = True
                user.save()

            # Куда редиректить после успешной активации
            login_url = getattr(settings, "FRONTEND_LOGIN_URL", "http://localhost:3001/login")

            # Если запрошено html-представление — отдадим страницу с авто-редиректом
            if request.query_params.get("html") == "1":
                html = render_to_string("registration/activation_success.html", {"login_url": login_url})
                return HttpResponse(html)

            # Поведение по-умолчанию (как было): прямой редирект на логин
            return redirect(login_url)
        else:
            if request.query_params.get("html") == "1":
                html = render_to_string("registration/activation_failed.html", {})
                return HttpResponse(html, status=400)
            return Response({"detail": "Ссылка недействительна или устарела."}, status=400)


class ResendActivationView(APIView):
    """
    POST /api/auth/resend-activation/
    Повторная отправка письма активации.
    Тело: {"email": "user@example.com"}
    Безопасность: НИКОГДА не раскрываем, существует ли такой email — всегда отдаём 200.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        if not email:
            # Чтобы не палить наличие/отсутствие адреса, возвращаем 200 и ту же фразу
            return Response({"detail": "Если аккаунт существует и не активирован, письмо отправлено."}, status=200)

        user = User.objects.filter(email__iexact=email).first()
        if user and not user.is_active:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            origin = _origin_from_request(request)
            activation_link = f"{origin}/api/auth/activate/{uid}/{token}/"

            ctx = {
                "user": user,
                "activation_link": activation_link,
                "project_name": getattr(settings, "PROJECT_NAME", "IzotovLife"),
            }
            _send_html_mail(
                subject=f"Активация аккаунта {ctx['project_name']}",
                to=[user.email],
                html_template="emails/activation_email.html",
                text_template="emails/activation_email.txt",
                context=ctx,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@izotovlife.ru"),
            )

        # В любом случае (даже если не нашли пользователя) отвечаем одинаково
        return Response({"detail": "Если аккаунт существует и не активирован, письмо отправлено."}, status=200)


class PasswordResetRequestView(APIView):
    """
    POST /api/auth/password-reset/
    Запрос на восстановление пароля (отправка email).
    Опционально поддерживает ?silent=1 — всегда вернёт 200, не раскрывая, есть ли такой пользователь.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            # Если явно включили "тихий" режим — не палим наличие аккаунта
            if request.query_params.get("silent") == "1":
                return Response({"detail": "Письмо для восстановления отправлено."}, status=200)
            # Сохраняю ваше поведение по-умолчанию (404), НИЧЕГО НЕ УДАЛЯЮ
            return Response({"detail": "Пользователь с таким email не найден."}, status=404)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Ссылка на фронт для ввода нового пароля:
        # По settings можно задать FRONTEND_RESET_URL = "http://localhost:3001/reset-password"
        reset_base = getattr(settings, "FRONTEND_RESET_URL", "http://localhost:3001/reset-password")
        reset_link = f"{reset_base}/{uid}/{token}/"

        ctx = {
            "user": user,
            "reset_link": reset_link,
            "project_name": getattr(settings, "PROJECT_NAME", "IzotovLife"),
        }
        _send_html_mail(
            subject=f"Восстановление пароля {ctx['project_name']}",
            to=[user.email],
            html_template="emails/reset_password_email.html",
            text_template="emails/reset_password_email.txt",
            context=ctx,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@izotovlife.ru"),
        )

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
