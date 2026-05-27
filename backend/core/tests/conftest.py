import pytest
from datetime import date, timedelta
from rest_framework.test import APIClient
from django.core.cache import CacheHandler

from users.models import User
from core.models import Count, Host
from django.core.cache import cache


@pytest.fixture
def redis(settings):
    """Return a test Redis connection using the test database (db 5)."""
    return cache._cache.get_client()


@pytest.fixture(autouse=True)
def clean_cache(redis):
    redis.flushall()
    yield
    redis.flushall()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        password="testpass123",
        timezone=0,
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username="otheruser",
        password="otherpass123",
        timezone=0,
    )


@pytest.fixture
def host(db, user):
    return Host.objects.create(user=user, name="example.com")


@pytest.fixture
def other_host(db, other_user):
    return Host.objects.create(user=other_user, name="other.com")


@pytest.fixture
def counts(db, host):
    today = date.today()
    yesterday = today - timedelta(days=1)

    Count.objects.create(
        host=host, date=today, category="pageview", item="/home", total=10
    )
    Count.objects.create(
        host=host, date=today, category="pageview", item="/about", total=5
    )
    Count.objects.create(
        host=host, date=yesterday, category="pageview", item="/home", total=3
    )
    Count.objects.create(
        host=host, date=today, category="click", item="button1", total=2
    )
    return Count.objects.all()
