"""Tests for the /dump SSE endpoint (docs/api.md)."""

import json

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

pytestmark = pytest.mark.django_db


def first_dump(response):
    for chunk in response.streaming_content:
        for part in chunk.decode().split("\n\n"):
            part = part.strip()
            if part.startswith("data: "):
                message = json.loads(part[len("data: "):])
                if message["type"] == "dump":
                    return message["payload"]
    raise AssertionError("no dump message")


class TestDump:
    def test_dump_includes_username(self, client, user):
        # The frontend navbar fills "Hi <username>!" from dump.user.id.
        client.force_login(user)
        resp = client.get("/dump")
        assert first_dump(resp)["user"]["id"] == user.username

    def test_user_sees_own_data(self, client, user, host, counts):
        client.force_login(user)
        resp = client.get("/dump")
        sites = first_dump(resp)["sites"]
        assert "pageview" in sites["example.com"]["visits"]["day"]
        assert sites["example.com"]["visits"]["day"]["pageview"]["/home"] == 10
        assert sites["example.com"]["visits"]["yesterday"]["pageview"]["/home"] == 3

    def test_user_cannot_see_other_users_data(
        self, client, user, host, other_user, other_host, counts
    ):
        client.force_login(user)
        resp = client.get("/dump")
        sites = first_dump(resp)["sites"]
        assert list(sites) == ["example.com"]