import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


@pytest.fixture
def api_client():
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
def auth_client(api_client, user):
    api_client.force_login(user)
    return api_client
