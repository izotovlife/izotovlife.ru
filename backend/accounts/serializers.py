# backend/accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор профиля пользователя (просмотр/редактирование).
    """

    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    photo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "photo",
            "bio",
            "is_staff",
            "is_superuser",   # 👈 добавили сюда!
        ]
        read_only_fields = (
            "id",
            "username",
            "is_staff",
            "is_superuser",   # 👈 и сюда
            "email",
        )

    def update(self, instance, validated_data):
        """
        Доп. поведение:
        - Если фронт хочет очистить фото, можно передать photo=null (JSON) или не передавать поле вовсе.
        """
        if "photo" in self.initial_data and self.initial_data.get("photo") in (None, "null", ""):
            instance.photo.delete(save=False)
            validated_data.pop("photo", None)

        return super().update(instance, validated_data)


class RegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор регистрации нового автора.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password2 = serializers.CharField(write_only=True, required=True)

    photo = serializers.ImageField(required=False, allow_null=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password2",
            "first_name",
            "last_name",
            "photo",
            "bio",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        return User.objects.create_user(**validated_data)
