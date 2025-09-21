# backend/moderation/views.py
# Назначение: API редактора — список на модерации, действия опубликовать/вернуть.
# Путь: backend/moderation/views.py

from rest_framework import permissions, status, views
from rest_framework.response import Response
from django.utils import timezone
from news.models import Article
from .serializers import ModerationArticleSerializer

class IsEditor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_editor() or request.user.is_superuser or request.user.is_staff)

class QueueView(views.APIView):
    permission_classes = [IsEditor]

    def get(self, request):
        items = Article.objects.filter(status='PENDING').order_by('created_at')
        data = ModerationArticleSerializer(items, many=True).data
        return Response({'items': data})

class ReviewView(views.APIView):
    permission_classes = [IsEditor]

    def post(self, request, article_id):
        action = request.data.get('action')  # 'publish' | 'revise'
        notes = request.data.get('notes', '')
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return Response({'detail': 'Не найдено'}, status=404)

        if action == 'publish':
            article.status = 'PUBLISHED'
            article.published_at = timezone.now()
            article.editor_notes = notes
            article.save()
            return Response({'status':'PUBLISHED'})

        if action == 'revise':
            article.status = 'NEEDS_REVISION'
            article.editor_notes = notes
            article.save()
            return Response({'status':'NEEDS_REVISION'})

        return Response({'detail':'Некорректное действие'}, status=400)
