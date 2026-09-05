"""Tests for the /dump SSE endpoint (docs/api.md)."""

import json
from datetime import date

import pytest
from django.contrib.auth import get_user_model

from core.models import Count, Host

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

    def test_buckets_carry_all_tracker_categories(self, client, user, host, counts):
        # The dashboard's components read every dimension unconditionally;
        # ranges/days without data must come back with empty maps, not
        # missing keys.
        client.force_login(user)
        resp = client.get("/dump")
        sites = first_dump(resp)["sites"]
        expected = {
            "lang", "ref", "page", "date", "weekday", "platform",
            "browser", "device", "country", "screen", "hour",
        }
        for range_, bucket in sites["example.com"]["visits"].items():
            assert expected <= set(bucket), f"{range_} misses categories"

    def test_yesterday_bucket_empty_but_present(self, client, user, host, counts):
        client.force_login(user)
        resp = client.get("/dump")
        bucket = first_dump(resp)["sites"]["example.com"]["visits"]["yesterday"]
        assert bucket["pageview"] == {"/home": 3}
        assert bucket["ref"] == {}

    def test_guest_dump_is_sessionless(self, client, user, host, counts):
        user.share_token = "tok"
        user.save()
        resp = client.get("/dump", {"user": str(user.uuid), "token": "tok"})
        payload = first_dump(resp)
        assert payload["meta"]["sessionless"] is True
        assert payload["meta"]["demo"] is False

    def test_session_dump_is_not_sessionless(self, client, user, host):
        client.force_login(user)
        resp = client.get("/dump")
        payload = first_dump(resp)
        assert payload["meta"]["sessionless"] is False
        assert payload["meta"]["demo"] is False

    def test_dump_includes_share_token(self, client, user, host):
        user.share_token = "tok"
        user.save()
        client.force_login(user)
        resp = client.get("/dump")
        assert first_dump(resp)["user"]["token"] == "tok"


class TestDemoDump:
    def test_demo_access_without_session(self, client, user, host, counts):
        # The landing page's "Live demo" link points at dashboard.html?demo=1;
        # it must work without any session as long as the demo account exists.
        demo = User.objects.create_user(username="demo", password="x")
        demo_host = Host.objects.create(user=demo, name="counter.dev")
        Count.objects.create(host=demo_host, date=date.today(), category="ref", item="https://google.com/", total=7)

        resp = client.get("/dump", {"demo": "1"})
        payload = first_dump(resp)
        assert payload["meta"]["demo"] is True
        assert payload["meta"]["sessionless"] is True
        assert payload["user"]["id"] == "demo"
        assert payload["sites"]["counter.dev"]["visits"]["day"]["ref"]["https://google.com/"] == 7

    def test_demo_without_account_is_nouser(self, client):
        resp = client.get("/dump", {"demo": "1"})
        for chunk in resp.streaming_content:
            assert "nouser" in chunk.decode()
            return
        raise AssertionError("no message")