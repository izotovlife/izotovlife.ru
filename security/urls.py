# Путь: backend/security/urls.py
# Назначение: Маршруты security — API входа, одноразовая «дверь», блокировка /admin/.

from django.urls import path
from django.http import HttpResponseNotFound
from .views import admin_session_login, admin_token_gate

def admin_block(request):
    # Любой прямой заход на /admin/ → 404, чтобы не светить путь админки
    return HttpResponseNotFound("<h1>Not Found</h1>")

urlpatterns = [
    # ✅ API для фронта: POST /api/security/admin-session-login/
    path("api/security/admin-session-login/", admin_session_login, name="admin_session_login"),

    # ✅ Одноразовая «дверь»: GET /admin/<token>/
    path("admin/<str:token>/", admin_token_gate, name="admin_token_gate"),

    # ✅ Жёсткая блокировка /admin/
    path("admin/", admin_block, name="admin_block"),
]




