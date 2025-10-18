# backend/news/api_media.py
# Назначение: Прокси-миниатюры для картинок в новостях, чтобы фронту было куда стучаться.
# URL: GET /api/media/thumbnail/?src=<url>&w=800&h=450&fit=cover&fmt=webp&q=82
# Реализация: делаем безопасный redirect на images.weserv.nl (лёгко и быстро).
# Если хотите реальную обработку через Pillow — можно позже, но сейчас важно убрать 404/400.

from urllib.parse import urlencode
from django.http import HttpResponseBadRequest, HttpResponseRedirect

WESERV = "https://images.weserv.nl/"

def thumbnail_proxy(request):
    src = request.GET.get('src')
    if not src:
        return HttpResponseBadRequest("src param is required")

    # Параметры (w/h/fit/fmt/q) пробрасываем как есть
    params = {}
    for k in ('w', 'h', 'fit', 'fmt', 'q', 'we', 'il', 'output'):
        v = request.GET.get(k)
        if v:
            params[k] = v

    # weserv ожидает param "url" (без протокола можно, но с протоколом тоже ок)
    q = {'url': src}
    q.update(params)

    # Пример: https://images.weserv.nl/?url=<src>&w=800&h=450&fit=cover&output=webp&q=82
    redirect_url = f"{WESERV}?{urlencode(q)}"
    return HttpResponseRedirect(redirect_url)
