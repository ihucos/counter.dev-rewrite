import pytest
from django.urls import reverse
from rest_framework import status

from core.models import Host


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

    def test_empty_hosts_list_when_user_has_no_hosts(self, api_client, user):
        """A user with no hosts gets an empty list."""
        api_client.force_authenticate(user=user)
        url = reverse("host-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_user_can_retrieve_own_host(self, api_client, user, host):
        """A user can retrieve a single host by its pk."""
        api_client.force_authenticate(user=user)
        url = reverse("host-detail", kwargs={"pk": host.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "example.com"

    def test_user_cannot_retrieve_other_users_host(
        self, api_client, user, other_user, other_host
    ):
        """A user gets a 404 when trying to retrieve another user's host."""
        api_client.force_authenticate(user=user)
        url = reverse("host-detail", kwargs={"pk": other_host.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_nonexistent_host_returns_404(self, api_client, user):
        """A user gets a 404 when the host does not exist."""
        api_client.force_authenticate(user=user)
        url = reverse("host-detail", kwargs={"pk": 9999})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_cannot_retrieve_host(self, api_client, host):
        """An unauthenticated user cannot retrieve a host."""
        url = reverse("host-detail", kwargs={"pk": host.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_not_allowed(self, api_client, user):
        """POST is not allowed on the read-only viewset."""
        api_client.force_authenticate(user=user)
        url = reverse("host-list")
        response = api_client.post(url, {"name": "new.com"}, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_update_not_allowed(self, api_client, user, host):
        """PUT is not allowed on the read-only viewset."""
        api_client.force_authenticate(user=user)
        url = reverse("host-detail", kwargs={"pk": host.pk})
        response = api_client.put(url, {"name": "changed.com"}, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_partial_update_not_allowed(self, api_client, user, host):
        """PATCH is not allowed on the read-only viewset."""
        api_client.force_authenticate(user=user)
        url = reverse("host-detail", kwargs={"pk": host.pk})
        response = api_client.patch(url, {"name": "changed.com"}, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_not_allowed(self, api_client, user, host):
        """DELETE is not allowed on the read-only viewset."""
        api_client.force_authenticate(user=user)
        url = reverse("host-detail", kwargs={"pk": host.pk})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
