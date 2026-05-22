from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status

from counts.models import Count


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