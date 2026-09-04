import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def client():
    from django.test import Client

    return Client()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="testpass123",
        timezone=0,
    )


@pytest.fixture
def host(db, user):
    from core.models import Host

    return Host.objects.create(user=user, name="example.com")


@pytest.fixture
def counts(db, host):
    from datetime import date, timedelta

    from core.models import Count

    today = date.today()
    yesterday = today - timedelta(days=1)
    Count.objects.create(host=host, date=today, category="pageview", item="/home", total=10)
    Count.objects.create(host=host, date=today, category="pageview", item="/about", total=5)
    Count.objects.create(host=host, date=yesterday, category="pageview", item="/home", total=3)
    Count.objects.create(host=host, date=today, category="click", item="button1", total=2)
    return Count.objects.all()