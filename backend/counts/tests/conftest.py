import pytest
from datetime import date, timedelta
from rest_framework.test import APIClient
from django.core.cache import CacheHandler

from accounts.models import User
from counts.models import Count, Host


@pytest.fixture
def redis():
    """Return a test Redis connection using the test database (db 5)."""

    return CacheHandler(
        {
            "default": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": "redis://redis:6379/5",
            }
        }
    )["default"]._cache.get_client()


@pytest.fixture(autouse=True)
def clean_cache(redis):
    yield
    # Sanity check
    assert redis.connection_pool.connection_kwargs["db"] != 0, "Refusing to flush db 0"
    redis.flushall()


@pytest.fixture(autouse=True)
def global_test_settings(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": "redis://redis:6379/5",  # Use db number 5,
        }
    }


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
        host=host, date=today, metric="pageview", value="/home", count=10
    )
    Count.objects.create(
        host=host, date=today, metric="pageview", value="/about", count=5
    )
    Count.objects.create(
        host=host, date=yesterday, metric="pageview", value="/home", count=3
    )
    Count.objects.create(
        host=host, date=today, metric="click", value="button1", count=2
    )
    return Count.objects.all()


@pytest.fixture
def other_counts(db, other_host):
    today = date.today()
    Count.objects.create(
        host=other_host, date=today, metric="pageview", value="/other", count=100
    )
    return Count.objects.all()
