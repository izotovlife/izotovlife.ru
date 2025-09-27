# backend/accounts/serializers.py
# Назначение: Сериализаторы пользователей (JWT, публичный профиль, регистрация, восстановление пароля).
# Путь: backend/accounts/serializers.py

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import exceptions, serializers
from news.models import Article

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


# ===== НОВЫЕ СЕРИАЛИЗАТОРЫ =====

class RegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации нового пользователя.
    Пароль хэшируется автоматически.
    """
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        user = User(
            username=validated_data["username"],
            email=validated_data["email"],
        )
        user.set_password(validated_data["password"])
        user.is_active = False  # по умолчанию аккаунт не активен, пока не подтвердит email
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Сериализатор для запроса восстановления пароля.
    Проверяет наличие email.
    """
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Сериализатор для подтверждения сброса пароля.
    Проверяет корректность нового пароля.
    """
    password = serializers.CharField(write_only=True, min_length=8)
