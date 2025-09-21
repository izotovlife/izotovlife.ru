# backend/accounts/models.py
# Назначение: Кастомная модель пользователя с ролями, фото и био.
# Путь: backend/accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        AUTHOR = 'AUTHOR', 'Автор'
        EDITOR = 'EDITOR', 'Редактор'
        ADMIN = 'ADMIN', 'Администратор'

    role = models.CharField(max_length=16, choices=Roles.choices, default=Roles.AUTHOR)
    photo = models.URLField(blank=True, default="")  # аватар автора
    bio = models.TextField(blank=True, default="")   # краткое описание

    def is_author(self):
        return self.role == self.Roles.AUTHOR

    def is_editor(self):
        return self.role == self.Roles.EDITOR

    def is_admin(self):
        return self.is_superuser or self.role == self.Roles.ADMIN

    def __str__(self):
        return self.username
