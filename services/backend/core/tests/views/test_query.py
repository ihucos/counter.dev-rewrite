from datetime import date, timedelta

from core.models import Count


class TestQueryView:
    """Test query: user cannot see data from a different user"""

    def test_user_can_query_own_data(self, auth_client, user, host, counts):
        response = auth_client.get("/api/core/query/", {"site": "example.com"})

        assert response.status_code == 200
        data = response.json()
        assert "pageview" in data
        assert data["pageview"]["/home"] == 13  # 10 + 3 summed
        assert data["pageview"]["/about"] == 5
        assert data["click"]["button1"] == 2

    def test_user_cannot_query_other_users_data(
        self, auth_client, user, host, other_user, other_host, counts
    ):
        response = auth_client.get("/api/core/query/", {"site": "other.com"})

        # other.com belongs to other_user, not user
        assert response.status_code == 404

    def test_query_with_date_filters(self, auth_client, user, host, counts):
        today = date.today()
        yesterday = today - timedelta(days=1)

        response = auth_client.get(
            "/api/core/query/",
            {
                "site": "example.com",
                "start_date": today.isoformat(),
                "end_date": today.isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Only today's data should be included
        assert "pageview" in data
        assert data["pageview"]["/home"] == 10  # Only today's count
        assert data["pageview"]["/about"] == 5
        assert data["click"]["button1"] == 2

    def test_query_with_start_date_only(self, auth_client, user, host, counts):
        yesterday = date.today() - timedelta(days=1)

        response = auth_client.get(
            "/api/core/query/",
            {
                "site": "example.com",
                "start_date": yesterday.isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Both yesterday and today's data should be included
        assert data["pageview"]["/home"] == 13  # 3 + 10
        assert data["pageview"]["/about"] == 5
        assert data["click"]["button1"] == 2

    def test_query_with_end_date_only(self, auth_client, user, host, counts):
        yesterday = date.today() - timedelta(days=1)

        response = auth_client.get(
            "/api/core/query/",
            {
                "site": "example.com",
                "end_date": yesterday.isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Only yesterday's data should be included
        assert data["pageview"]["/home"] == 3  # Only yesterday
        assert "/about" not in data.get("pageview", {})

    def test_entries_with_same_category_and_item_summed(self, auth_client, user, host):
        # Create multiple counts with same category/item on different days
        today = date.today()
        yesterday = today - timedelta(days=1)
        day_before = yesterday - timedelta(days=1)

        Count.objects.create(
            host=host, date=today, category="pageview", item="/home", total=10
        )
        Count.objects.create(
            host=host, date=yesterday, category="pageview", item="/home", total=5
        )
        Count.objects.create(
            host=host, date=day_before, category="pageview", item="/home", total=3
        )

        # Create a different item for same category
        Count.objects.create(
            host=host, date=today, category="pageview", item="/about", total=7
        )

        response = auth_client.get("/api/core/query/", {"site": "example.com"})

        assert response.status_code == 200
        data = response.json()
        assert data["pageview"]["/home"] == 18  # 10 + 5 + 3
        assert data["pageview"]["/about"] == 7

    def test_unauthenticated_cannot_query(self, api_client):
        response = api_client.get("/api/core/query/", {"site": "example.com"})
        assert response.status_code == 403

    def test_query_returns_empty_for_no_data(self, auth_client, user, host):
        response = auth_client.get("/api/core/query/", {"site": "example.com"})

        assert response.status_code == 200
        assert response.json() == {}
