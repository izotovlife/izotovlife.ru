# backend/news/api_views.py
# Эндпоинты для новостей, погоды и валют
import os
try:  # pragma: no cover - optional dependency for external APIs
    import requests  # type: ignore
except Exception:  # pragma: no cover - tests run without requests installed
    requests = None  # type: ignore
from django.http import JsonResponse
from .models import News

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

def short_news(request):
    """Возвращает последние 10 коротких новостей"""
    qs = News.objects.order_by("-created_at")[:10]
    data = [{"id": n.id, "title": n.title} for n in qs]
    return JsonResponse(data, safe=False)

def weather(request):
    """Реальные данные погоды через OpenWeather"""
    if not OPENWEATHER_API_KEY:
        return JsonResponse({
            "city": "Москва",
            "temp": 20,
            "description": "Тестовые данные (нет ключа OpenWeather)"
        })

    city = "Moscow"  # можно параметризовать
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    if requests is None:
        return JsonResponse({"error": "requests library not installed"})

    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        result = {
            "city": data["name"],
            "temp": round(data["main"]["temp"]),
            "description": data["weather"][0]["description"].capitalize(),
        }
    except Exception as e:
        result = {"error": str(e)}
    return JsonResponse(result)


def currency(request):
    """Курсы валют (USD, EUR) через exchangerate.host"""
    url = "https://api.exchangerate.host/latest?base=RUB&symbols=USD,EUR"
    if requests is None:
        return JsonResponse({"error": "requests library not installed"})

    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        result = {
            "USD": round(1 / data["rates"]["USD"], 2),  # сколько рублей за доллар
            "EUR": round(1 / data["rates"]["EUR"], 2),  # сколько рублей за евро
        }
    except Exception as e:
        result = {"error": str(e)}
    return JsonResponse(result)
