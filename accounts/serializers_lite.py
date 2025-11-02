# Путь: accounts/serializers_lite.py
# Назначение: лёгкий сериализатор пользователя (чтобы не зависеть от вашего большого serializers.py).

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class UserLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_staff", "is_active"]
