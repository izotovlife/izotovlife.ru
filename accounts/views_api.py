# Путь: accounts/views_api.py
# Назначение: whoami / me / dashboard (лёгкие JSON-вьюхи, без ломки вашей логики).

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers_lite import UserLiteSerializer  # лёгкий сериализатор


class WhoAmIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            return Response({"is_authenticated": True, "user": UserLiteSerializer(request.user).data})
        return Response({"is_authenticated": False, "user": None})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserLiteSerializer(request.user).data)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "user": UserLiteSerializer(user).data,
            "counters": {"articles_total": 0, "articles_published": 0, "articles_draft": 0},
            "permissions": {
                "is_staff": bool(user.is_staff),
                "is_superuser": bool(getattr(user, "is_superuser", False)),
            },
        })
