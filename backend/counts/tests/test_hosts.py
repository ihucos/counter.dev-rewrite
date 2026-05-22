import pytest
from django.urls import reverse
from rest_framework import status


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
        assert response.status_code == status.HTTP_403_FORBIDDEN--- a/backend/counts/tests/test_query.py
