"""Tasks for news app."""

from datetime import timedelta
from django.utils import timezone
from celery import shared_task

from .models import News


@shared_task
def recalculate_top_news():
    """Recalculate top news based on view counts."""
    now = timezone.now()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    day_top = News.objects.filter(
        is_moderated=True, created_at__gte=day_ago
    ).order_by("-views_count")[:10]
    week_top = News.objects.filter(
        is_moderated=True, created_at__gte=week_ago
    ).order_by("-views_count")[:10]

    top_ids = {n.id for n in day_top} | {n.id for n in week_top}

    News.objects.update(is_popular=False)
    News.objects.filter(id__in=top_ids).update(is_popular=True)
