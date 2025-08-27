# backend/backend/middleware.py
import random, string
from django.conf import settings
from django.shortcuts import redirect

def generate_admin_url():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=16))

class DynamicAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.dynamic_admin_url = None

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_superuser:
            if not request.session.get("admin_url"):
                request.session["admin_url"] = generate_admin_url()
            settings.DYNAMIC_ADMIN_URL = request.session["admin_url"]
        return self.get_response(request)
