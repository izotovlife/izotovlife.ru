# Путь: news_aggregator/accounts/views_redirects.py
# Назначение: Перенаправить /accounts/login/ и /accounts/signup/ на роуты фронтенда.
# Ничего не трогает в allauth — просто «перекрывает» конкретные URL до include(allauth.urls).

from django.conf import settings
from django.shortcuts import redirect
from django.views import View

class FrontendLoginRedirectView(View):
    def get(self, request, *args, **kwargs):
        url = getattr(settings, "FRONTEND_LOGIN_URL", "/login")
        return redirect(url)

class FrontendSignupRedirectView(View):
    def get(self, request, *args, **kwargs):
        base = getattr(settings, "FRONTEND_BASE_URL", "")
        url = base + "/register" if base else "/register"
        return redirect(url)
