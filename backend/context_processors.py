# backend/context_processors.py
# Назначение: передаёт SITE_DOMAIN в шаблоны (например для robots.txt).
# Путь: backend/context_processors.py

from django.conf import settings

def site_domain(request):
    return {"SITE_DOMAIN": settings.SITE_DOMAIN}
