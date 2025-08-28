from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('news', '0006_auto_20250826_2256'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='subscriptions', to=settings.AUTH_USER_MODEL)),
                ('category', models.ForeignKey(on_delete=models.CASCADE, related_name='subscribers', to='news.category')),
            ],
            options={
                'unique_together': {('user', 'category')},
            },
        ),
    ]
