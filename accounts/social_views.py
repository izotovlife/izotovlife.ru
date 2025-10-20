# Путь: news_aggregator/accounts/social_views.py
# Назначение: После успешной соц-авторизации (через allauth) пользователь залогинен СЕССИОННО.
# Здесь мы выпускаем SimpleJWT токены, отправляем их в окно-родителя (SPA) через postMessage и закрываем popup.

from django.utils.html import escape
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

class SocialCompleteView(View):
    def get(self, request):
        # Если нет сессионной авторизации — отправим на стандартный логин allauth
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/accounts/login/")

        refresh = RefreshToken.for_user(request.user)
        access = str(refresh.access_token)
        refresh_token = str(refresh)

        # Безопасный origin: берём FRONTEND_BASE_URL, а в DEBUG допускаем "*"
        origin = getattr(settings, "FRONTEND_BASE_URL", "").rstrip("/")
        if not origin and getattr(settings, "DEBUG", False):
            origin = "*"

        html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Авторизация</title></head>
<body>
<script>
try {{
  const payload = {{
    type: "social-auth",
    access: "{escape(access)}",
    refresh: "{escape(refresh_token)}"
  }};
  if (window.opener && !window.opener.closed) {{
    window.opener.postMessage(payload, "{escape(origin)}");
  }}
}} catch (e) {{}}
window.close();
</script>
Успешная авторизация. Это окно можно закрыть.
</body></html>"""
        return HttpResponse(html)
