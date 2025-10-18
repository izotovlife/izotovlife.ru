# Путь: backend/accounts/tokens.py
# Назначение: Генератор безопасных токенов для подтверждения e-mail (активации учётной записи).
# Используется во время регистрации для формирования ссылки вида:
#   /api/auth/registration/confirm/<uidb64>/<token>/

from django.contrib.auth.tokens import PasswordResetTokenGenerator

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    Надёжный генератор токенов на основе встроенного механизма Django.
    Привязывает токен к пользователю и его полям, так что подделка невозможна.
    """
    def _make_hash_value(self, user, timestamp):
        # В хеш добавляем is_active, чтобы новый токен менялся после активации
        return f"{user.pk}{timestamp}{user.is_active}"

account_activation_token = AccountActivationTokenGenerator()
