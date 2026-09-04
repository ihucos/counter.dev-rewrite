import re

import pytest
from datetime import date, timedelta

from django.core.cache import cache as django_cache
from django.conf import settings
from django.contrib.auth import get_user_model
from redis import Redis

from core.models import Count, Host

User = get_user_model()


def _get_worker_id(request):
    workerinput = getattr(request.config, "workerinput", None)
    if workerinput is not None:
        return workerinput["workerid"]
    return "master"


@pytest.fixture(scope="session")
def redis_db_number(request):
    """Return a unique Redis DB number per xdist worker."""
    worker_id = _get_worker_id(request)
    if worker_id == "master":
        return 0
    match = re.search(r"\d+", worker_id)
    if match:
        return int(match.group()) + 1
    return 0


@pytest.fixture(scope="function")
def redis(redis_db_number):
    # Point Django's cache at this worker's Redis DB so the sync command and
    # views read the same data as these fixtures.
    settings.CACHES["default"]["LOCATION"] = f"redis://localhost:6379/{redis_db_number}"
    handler = django_cache._connections
    try:
        delattr(handler._connections, django_cache._alias)
    except AttributeError:
        pass

    client = Redis(host="localhost", port=6379, db=redis_db_number)
    yield client
    client.flushdb()


@pytest.fixture(autouse=True)
def clean_cache(redis):
    redis.flushdb()
    yield
    redis.flushdb()


@pytest.fixture
def client():
    from django.test import Client

    return Client()


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