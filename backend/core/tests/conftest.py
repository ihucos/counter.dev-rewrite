import pytest
from datetime import date, timedelta
from rest_framework.test import APIClient
from django.core.cache import cache as django_cache
from django.conf import settings
from django.contrib.auth import get_user_model
from redis import Redis
import re

from core.models import Count, Host


User = get_user_model()


def _get_worker_id(request):
    workerinput = getattr(request.config, "workerinput", None)
    if workerinput is not None:
        return workerinput["workerid"]
    return "master"


@pytest.fixture(scope="session")
def redis_db_number(request):
    """Return a unique Redis DB number per xdist worker.

    When running without xdist, all tests share DB 0.
    When running with xdist, each worker gets its own DB (gw0→DB1, gw1→DB2, …)
    so parallel test executions don't interfere with each other.
    """
    worker_id = _get_worker_id(request)

    # If running sequentially (without xdist), default to DB 0
    if worker_id == "master":
        return 0

    # Extract the integer from 'gw0', 'gw1', etc.
    match = re.search(r"\d+", worker_id)
    if match:
        # Add 1 so gw0 uses DB 1, gw1 uses DB 2, etc. (leaving DB 0 clean)
        return int(match.group()) + 1
    return 0


@pytest.fixture(scope="function")
def redis(redis_db_number):
    # Override the CACHES setting so that Django's cache (and thus ingress
    # command) connects to the same Redis DB as this worker's test fixtures.
    # This enables parallel test execution with pytest-xdist.
    cache_location = f"redis://localhost:6379/{redis_db_number}"
    settings.CACHES["default"]["LOCATION"] = cache_location

    # Close and recreate the Django cache backend so it picks up the
    # new location.  We delete the 'default' connection from the
    # CacheHandler's Local storage; the next access will re-create it
    # using the updated settings.
    handler = django_cache._connections
    try:
        delattr(handler._connections, django_cache._alias)
    except AttributeError:
        pass

    # Create a raw Redis client connected to this worker's DB
    client = Redis(host="localhost", port=6379, db=redis_db_number)

    yield client

    # Clean up only this worker's DB after each test.
    client.flushdb()


@pytest.fixture(autouse=True)
def clean_cache(redis):
    # Only flush this worker's DB, not all databases (which would interfere
    # with other xdist workers running in parallel).
    redis.flushdb()
    yield
    redis.flushdb()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    u = User.objects.create_user(
        username="testuser",
        password="testpass123",
    )
    u.profile.timezone = 0
    u.save()
    return u


@pytest.fixture
def other_user(db):
    u = User.objects.create_user(
        username="otheruser",
        password="otherpass123",
    )
    u.profile.timezone = 0
    u.save()
    return u


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
