import pytest
from datetime import date, timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from counts.models import Count, Host


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

    # Create multiple counts for different metrics/values
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


class TestHostViewSet:
    """Test host: user a cannot see hosts of user b but its own host"""

    def test_user_can_see_own_hosts(self, api_client, user, host):
        api_client.force_authenticate(user=user)
        url = reverse("host-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "example.com"

    def test_user_cannot_see_other_users_hosts(
        self, api_client, user, host, other_user, other_host
    ):
        api_client.force_authenticate(user=user)
        url = reverse("host-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert "other.com" not in [h["name"] for h in response.data]

    def test_unauthenticated_cannot_access_hosts(self, api_client):
        url = reverse("host-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestQueryView:
    """Test query: user cannot see data from a different user"""

    def test_user_can_query_own_data(self, api_client, user, host, counts):
        api_client.force_authenticate(user=user)
        url = reverse("query")
        response = api_client.get(url, {"site": "example.com"})

        assert response.status_code == status.HTTP_200_OK
        assert "pageview" in response.data
        assert response.data["pageview"]["/home"] == 13  # 10 + 3 summed
        assert response.data["pageview"]["/about"] == 5
        assert response.data["click"]["button1"] == 2

    def test_user_cannot_query_other_users_data(
        self, api_client, user, host, other_user, other_host, other_counts
    ):
        api_client.force_authenticate(user=user)
        url = reverse("query")
        response = api_client.get(url, {"site": "other.com"})

        # other.com belongs to other_user, not user
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_query_with_date_filters(self, api_client, user, host, counts):
        api_client.force_authenticate(user=user)
        today = date.today()
        yesterday = today - timedelta(days=1)

        url = reverse("query")
        response = api_client.get(
            url,
            {
                "site": "example.com",
                "start_date": today.isoformat(),
                "end_date": today.isoformat(),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        # Only today's data should be included
        assert "pageview" in response.data
        assert response.data["pageview"]["/home"] == 10  # Only today's count
        assert response.data["pageview"]["/about"] == 5
        assert response.data["click"]["button1"] == 2

    def test_query_with_start_date_only(self, api_client, user, host, counts):
        api_client.force_authenticate(user=user)
        yesterday = date.today() - timedelta(days=1)

        url = reverse("query")
        response = api_client.get(
            url,
            {
                "site": "example.com",
                "start_date": yesterday.isoformat(),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        # Both yesterday and today's data should be included
        assert response.data["pageview"]["/home"] == 13  # 3 + 10
        assert response.data["pageview"]["/about"] == 5
        assert response.data["click"]["button1"] == 2

    def test_query_with_end_date_only(self, api_client, user, host, counts):
        api_client.force_authenticate(user=user)
        yesterday = date.today() - timedelta(days=1)

        url = reverse("query")
        response = api_client.get(
            url,
            {
                "site": "example.com",
                "end_date": yesterday.isoformat(),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        # Only yesterday's data should be included
        assert "pageview" in response.data
        assert response.data["pageview"]["/home"] == 3  # Only yesterday
        assert "/about" not in response.data.get("pageview", {})

    def test_entries_with_same_metric_and_value_summed(self, api_client, user, host):
        api_client.force_authenticate(user=user)

        # Create multiple counts with same metric/value on different days
        today = date.today()
        yesterday = today - timedelta(days=1)
        day_before = yesterday - timedelta(days=1)

        Count.objects.create(
            host=host, date=today, metric="pageview", value="/home", count=10
        )
        Count.objects.create(
            host=host, date=yesterday, metric="pageview", value="/home", count=5
        )
        Count.objects.create(
            host=host, date=day_before, metric="pageview", value="/home", count=3
        )

        # Create a different value for same metric
        Count.objects.create(
            host=host, date=today, metric="pageview", value="/about", count=7
        )

        url = reverse("query")
        response = api_client.get(url, {"site": "example.com"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["pageview"]["/home"] == 18  # 10 + 5 + 3
        assert response.data["pageview"]["/about"] == 7

    def test_unauthenticated_cannot_query(self, api_client):
        url = reverse("query")
        response = api_client.get(url, {"site": "example.com"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_query_returns_empty_for_no_data(self, api_client, user, host):
        api_client.force_authenticate(user=user)
        url = reverse("query")
        response = api_client.get(url, {"site": "example.com"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {}

