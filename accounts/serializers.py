# Путь: backend/accounts/serializers.py
# Назначение: Сериализаторы пользователей (JWT, публичный профиль, регистрация, восстановление пароля).
# В этом файле уже были:
#   - MyTokenObtainPairSerializer — логин по username/email (JWT) + краткая инфо о пользователе
#   - PublicAuthorSerializer / PublicArticleSerializer / AuthorDetailSerializer — публичные профили/статьи
#   - RegisterSerializer — базовая регистрация (username, email, password) с is_active=False
#   - PasswordResetRequestSerializer — запрос на восстановление пароля по email
#   - PasswordResetConfirmSerializer — подтверждение сброса пароля
#
# Что Я ДОБАВИЛ, НИЧЕГО НЕ УДАЛЯЯ (кроме исправления явной ошибки/мусора в конце файла):
#   ✅ Сделал username НЕОБЯЗАТЕЛЬНЫМ (required=False, allow_blank=True).
#   ✅ Добавил генерацию уникального username, если занято (чтобы не словить IntegrityError/500).
#   ✅ Обернул создание пользователя от коллизий username.
#   ✅ Оставил остальной код без изменений.
#   ⛔ Исправление: удалён случайный текст «дополни файл…» который ломал синтаксис файла.

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password  # ✅ проверка сложности пароля
from django.db import IntegrityError  # ✅ для страховки от коллизий username
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import exceptions, serializers
from news.models import Article
import random  # ✅ для генерации уникального username
import string  # ✅ для генерации уникального username

User = get_user_model()


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Позволяет логиниться как по username, так и по email.
    Возвращает access/refresh + краткую информацию о пользователе.
    """

    def validate(self, attrs):
        raw_username = self.context["request"].data.get("username")
        raw_email = self.context["request"].data.get("email")
        password = self.context["request"].data.get("password")

        if not password or not (raw_username or raw_email):
            raise exceptions.ValidationError("Укажите логин (или email) и пароль.")

        user = None
        if raw_username:
            user = User.objects.filter(username__iexact=raw_username).first()
            if not user and "@" in raw_username:
                user = User.objects.filter(email__iexact=raw_username).first()
        elif raw_email:
            user = User.objects.filter(email__iexact=raw_email).first()

        if not user or not user.check_password(password):
            raise exceptions.AuthenticationFailed("Неверный логин или пароль.")

        attrs["username"] = user.get_username()
        data = super().validate(attrs)

        data["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": getattr(user, "role", None),
            "photo": user.photo,
            "bio": user.bio,
            "admin_redirect": "/api/security/admin-session-login/" if user.is_superuser else None,
        }
        return data


class PublicAuthorSerializer(serializers.ModelSerializer):
    """Публичный профиль автора"""

    class Meta:
        model = User
        fields = ["id", "username", "photo", "bio"]


class PublicArticleSerializer(serializers.ModelSerializer):
    """Краткий сериализатор статьи для страницы автора"""

    class Meta:
        model = Article
        fields = ["id", "title", "slug", "cover_image", "published_at"]


class AuthorDetailSerializer(serializers.ModelSerializer):
    """Публичный профиль автора + список его опубликованных статей"""
    articles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "photo", "bio", "articles"]

    def get_articles(self, obj):
        from news.models import Article
        qs = Article.objects.filter(author=obj, status=Article.Status.PUBLISHED)
        return PublicArticleSerializer(qs, many=True).data


# ===== НОВЫЕ СЕРИАЛИЗАТОРЫ (РАСШИРЕНО, НИЧЕГО НЕ УДАЛЕНО) =====

class RegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации нового пользователя.
    Пароль хэшируется автоматически.
    ДОПОЛНЕНО:
      - first_name и last_name
      - нормализация e-mail (нижний регистр, trim)
      - проверка уникальности e-mail и username
      - если username не передан — используем e-mail как основу и подбираем уникальный username
      - is_active=False (ожидание подтверждения e-mail)
    """
    # ✅ username можно не присылать
    username = serializers.CharField(required=False, allow_blank=True, max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name"]

    def validate_email(self, value):
        email = (value or "").strip().lower()
        if not email:
            raise serializers.ValidationError("Укажите e-mail.")
        # Проверка уникальности e-mail
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Пользователь с таким e-mail уже зарегистрирован.")
        return email

    def validate_username(self, value):
        """
        Username может быть пустым — тогда мы подставим e-mail в create().
        Если передан — проверим уникальность без учёта регистра.
        """
        username = (value or "").strip()
        if username and User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("Пользователь с таким логином уже существует.")
        return username

    def validate_password(self, value):
        """
        Проверяем сложность пароля согласно настройкам Django (AUTH_PASSWORD_VALIDATORS).
        """
        validate_password(value)
        return value

    # ✅ Генерация уникального username на основе базы
    def _unique_username(self, base: str) -> str:
        base = (base or "").strip() or "user"
        # Обрежем базу под возможные суффиксы
        base = base[:150]
        candidate = base
        for _ in range(50):
            if not User.objects.filter(username__iexact=candidate).exists():
                return candidate
            suffix = "-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
            candidate = (base[:150 - len(suffix)]) + suffix
        # fallback
        return "user-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))

    def create(self, validated_data):
        email = validated_data.get("email").strip().lower()
        raw_username = (validated_data.get("username") or "").strip() or email
        # если прислали e-mail — берём часть до @ как базу username
        base_username = raw_username.split("@")[0] if "@" in raw_username else raw_username
        username = self._unique_username(base_username)

        password = validated_data["password"]
        first_name = (validated_data.get("first_name") or "").strip()
        last_name = (validated_data.get("last_name") or "").strip()

        try:
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            user.set_password(password)
            user.is_active = False  # по умолчанию аккаунт не активен, пока не подтвердит email
            user.save()
            return user
        except IntegrityError:
            # маловероятно (мы уже подбираем уникальный username), но вернём понятную ошибку
            raise serializers.ValidationError({"username": "Не удалось подобрать уникальный логин, попробуйте ещё раз."})


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Сериализатор для запроса восстановления пароля.
    Проверяет корректность email-формата и нормализует его.
    Намеренно НЕ раскрывает, существует ли пользователь с таким e-mail (во избежание user enumeration).
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        return (value or "").strip().lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Сериализатор для подтверждения сброса пароля.
    Проверяет корректность нового пароля.
    Если во вьюхе вы отправляете два поля (password и password2) — мы их сравним.
    Если отправляете только password — сравнение пропускается.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    # Необязательное поле — если фронт пришлёт, проверим совпадение
    password2 = serializers.CharField(write_only=True, required=False, allow_blank=True, min_length=8)

    def validate(self, attrs):
        pwd = attrs.get("password")
        pwd2 = attrs.get("password2")
        # Проверка валидаторов Django
        validate_password(pwd)
        # Если прислали подтверждение — проверим совпадение
        if pwd2 is not None and pwd2 != "":
            if pwd != pwd2:
                raise serializers.ValidationError({"password2": "Пароли не совпадают."})
        return attrs
