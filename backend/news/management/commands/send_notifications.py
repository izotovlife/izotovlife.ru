from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from accounts.models import Subscription
from news.models import News


class Command(BaseCommand):
    help = "Send latest news emails to category subscribers"

    def handle(self, *args, **options):
        for sub in Subscription.objects.select_related('user', 'category'):
            if not sub.user.email:
                continue
            latest = (
                News.objects.filter(category=sub.category, is_moderated=True)
                .order_by('-created_at')
                .first()
            )
            if not latest:
                continue
            send_mail(
                subject=f"Новость в категории {sub.category.name}",
                message=latest.title,
                from_email=None,
                recipient_list=[sub.user.email],
                fail_silently=True,
            )
            self.stdout.write(f"Sent to {sub.user.email}")
