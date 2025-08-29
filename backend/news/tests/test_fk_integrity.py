import pytest
from django.core.management import call_command
from django.db import connection
from rest_framework.test import APIClient

from news.models import News


def create_broken_news():
    news = News.objects.create(
        title="Broken",
        source_type="rss",
        is_moderated=True,
        author_id=999999,
    )
    # manually set a non-existent category id
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute(
            "UPDATE news_news SET category_id = ? WHERE id = ?",
            [999999, news.id],
        )
        cursor.execute("PRAGMA foreign_keys=ON")
    news.refresh_from_db()
    return news


@pytest.mark.django_db
def test_list_handles_missing_author_category():
    create_broken_news()
    client = APIClient()
    response = client.get("/api/news/")
    assert response.status_code == 200
    item = response.json()["results"][0]
    assert item["author"] is None
    assert item["category"] is None


@pytest.mark.django_db
def test_popular_handles_missing_fk():
    create_broken_news()
    client = APIClient()
    response = client.get("/api/news/popular/")
    assert response.status_code == 200
    item = response.json()[0]
    assert item["author"] is None
    assert item["category"] is None


@pytest.mark.django_db
def test_detail_handles_missing_fk():
    news = create_broken_news()
    client = APIClient()
    response = client.get(f"/api/news/{news.id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["author"] is None
    assert data["category"] is None
    news.refresh_from_db()
    assert news.views_count == 1


@pytest.mark.django_db
def test_fix_command_nullifies_broken_fks():
    news = create_broken_news()
    call_command("fix_news_fk_integrity")
    news.refresh_from_db()
    assert news.author is None
    assert news.category is None
