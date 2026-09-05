"""Integration tests for the documented API (docs/api.md)."""

import json
from datetime import date, timedelta
from urllib.parse import quote

import pytest
from django.core import mail
from django.contrib.auth import get_user_model

User = get_user_model()

from core.models import Count, Host

pytestmark = pytest.mark.django_db


class TestRegister:
    def test_register(self, client):
        resp = client.post(
            "/register",
            {"user": "newuser", "mail": "new@example.com", "password": "Str0ng!Pass", "utcoffset": 120},
        )
        assert resp.status_code == 200
        user = User.objects.get(username="newuser")
        assert user.email == "new@example.com"
        assert user.timezone == 120
        # registration signs the user in
        assert client.session.get("_auth_user_id") == str(user.id)

    def test_register_duplicate_user(self, client, user):
        resp = client.post("/register", {"user": "testuser", "password": "x" * 8, "utcoffset": 0})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "user already exists"


class TestLogin:
    def test_login_sets_session(self, client, user):
        resp = client.post("/login", {"user": "testuser", "password": "testpass123"})
        assert resp.status_code == 200
        assert client.session.get("_auth_user_id") == str(user.id)

    def test_login_wrong_password(self, client, user):
        resp = client.post("/login", {"user": "testuser", "password": "nope"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "wrong password"

    def test_login_unknown_user(self, client):
        resp = client.post("/login", {"user": "ghost", "password": "nope"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "no such user"


class TestRecover:
    def test_recover_sends_mail(self, client, user):
        resp = client.post("/recover", {"mail": "testuser@example.com", "user": "testuser"})
        assert resp.status_code == 200
        assert len(mail.outbox) == 1
        assert "testuser" in mail.outbox[0].body

    def test_recover_wrong_mail_is_still_ok(self, client, user):
        resp = client.post("/recover", {"mail": "wrong@example.com", "user": "testuser"})
        assert resp.status_code == 200
        assert not mail.outbox


class TestAccountUpdate:
    def test_account_update(self, client, user):
        client.force_login(user)
        resp = client.put(
            "/account",
            {"timezone": -60, "use_sites": "true", "email": "a@b.c"},
            content_type="application/json",
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.timezone == -60
        assert user.email == "a@b.c"
        assert user.use_sites is True

    def test_account_create_site(self, client, user):
        client.force_login(user)
        resp = client.put("/account", {"timezone": 0, "email": ""}, content_type="application/json")
        assert resp.status_code == 200
        resp = client.post("/sites", {"name": "www.foo.bar/"}, content_type="application/json")
        assert resp.status_code == 201
        names = sorted(Host.objects.filter(user=user).values_list("name", flat=True))
        assert names == ["foo.bar"]

    def test_account_update_prefs(self, client, user, host):
        client.force_login(user)
        resp = client.put("/account", {"selected_site": "example.com", "date_range": "last7"}, content_type="application/json")
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.selected_site == host
        assert user.date_range == "last7"

    def test_account_update_invalid_range(self, client, user):
        client.force_login(user)
        assert client.put("/account", {"date_range": "nope"}, content_type="application/json").status_code == 400


class TestDeleteAccount:
    def test_delete_account(self, client, user, host):
        client.force_login(user)
        resp = client.delete("/account")
        assert resp.status_code == 200
        assert not User.objects.filter(username="testuser").exists()
        assert not Host.objects.filter(name="example.com").exists()


class TestFeedback:
    def test_feedback(self, client, user):
        resp = client.post("/feedback", {"feedback": "hello", "contact": "me@example.com"})
        assert resp.status_code == 200
        assert "hello" in mail.outbox[0].body

    def test_feedback_missing(self, client):
        assert client.post("/feedback", {}).status_code == 400


class TestDeleteSite:
    def test_delete_site_removes_site_and_counts(self, client, user, host, counts):
        client.force_login(user)
        resp = client.delete("/sites/example.com")
        assert resp.status_code == 204
        assert not Host.objects.filter(name="example.com").exists()

    def test_delete_site_missing(self, client, user):
        client.force_login(user)
        assert client.delete("/sites/nope.com").status_code == 404

    def test_delete_site_clears_selection(self, client, user, host, counts):
        user.selected_site = host
        user.save()
        client.force_login(user)
        assert client.delete("/sites/example.com").status_code == 204
        user.refresh_from_db()
        assert user.selected_site is None


class TestShareToken:
    def test_rotate_and_revoke_token(self, client, user):
        client.force_login(user)
        resp = client.put("/account/share_token")
        assert resp.status_code == 200
        token = json.loads(resp.content)["token"]
        user.refresh_from_db()
        assert user.share_token == token

        resp = client.delete("/account/share_token")
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.share_token == ""


class TestAccountState:
    def test_account_returns_promoted_state(self, client, user, host):
        client.force_login(user)
        user.selected_site = host
        user.date_range = "last7"
        user.save()
        body = client.get("/account").json()
        assert body["user"]["selected_site"] == "example.com"
        assert body["user"]["date_range"] == "last7"
        assert body["user"]["use_sites"] is False


class TestAccount:
    def test_account_not_signed_in(self, client):
        resp = client.get("/account")
        assert resp.status_code == 401

    def test_account_signed_in(self, client, user, host):
        client.force_login(user)
        resp = client.get("/account?utcoffset=60")
        body = json.loads(resp.content)
        assert body["user"]["id"] == "testuser"
        assert body["user"]["uuid"] == str(user.uuid)
        assert body["user"]["selected_site"] == ""
        assert body["user"]["date_range"] == "day"
        assert body["user"]["use_sites"] is False
        assert body["user"]["timezone"] == 0
        assert body["meta"] == {"utcoffset": 60, "sessionless": False, "demo": False}

    def test_account_guest_access(self, client, user, host):
        user.share_token = "tok123"
        user.save()
        resp = client.get(f"/account?user={user.uuid}&token=tok123")
        body = json.loads(resp.content)
        assert body["user"]["id"] == "testuser"
        assert body["meta"]["sessionless"] is True
        assert body["meta"]["demo"] is False

    def test_account_guest_wrong_token(self, client, user, host):
        user.share_token = "tok123"
        user.save()
        assert client.get(f"/account?user={user.uuid}&token=bad").status_code == 401

    def test_account_demo_access(self, client, user, host):
        User.objects.create_user(username="demo", password="x")
        resp = client.get("/account?demo=1")
        body = json.loads(resp.content)
        assert body["meta"]["demo"] is True
        assert body["meta"]["sessionless"] is True


class TestQuery:
    def test_query_not_signed_in(self, client, host):
        assert client.get("/query?site=example.com").status_code == 401

    def test_query_signed_in(self, client, user, host, counts):
        client.force_login(user)
        resp = client.get("/query?site=example.com")
        body = json.loads(resp.content)
        assert body["site"] == "example.com"
        # Open-ended: the default window covers all seeded counts.
        assert body["visits"]["pageview"]["/home"] == 13
        assert body["visits"]["click"]["button1"] == 2
        # Every category is present so the frontend never reads undefined
        # dimensions.
        for category in [
            "lang", "ref", "page", "date", "weekday", "platform",
            "browser", "device", "country", "screen", "hour",
        ]:
            assert category in body["visits"]

    def test_query_bounded_range(self, client, user, host, counts):
        client.force_login(user)
        today = date.today()
        resp = client.get(f"/query?site=example.com&start={today}&end={today}")
        body = json.loads(resp.content)
        assert body["visits"]["pageview"]["/home"] == 10
        assert body["visits"]["click"] == {"button1": 2}

    def test_query_missing_end(self, client, user, host, counts):
        client.force_login(user)
        yesterday = date.today() - timedelta(days=1)
        resp = client.get(f"/query?site=example.com&start={yesterday}")
        body = json.loads(resp.content)
        assert body["visits"]["pageview"]["/home"] == 13

    def test_query_missing_start(self, client, user, host, counts):
        client.force_login(user)
        yesterday = date.today() - timedelta(days=1)
        resp = client.get(f"/query?site=example.com&end={yesterday}")
        body = json.loads(resp.content)
        assert body["visits"]["pageview"]["/home"] == 3

    def test_query_invalid_date(self, client, user, host, counts):
        client.force_login(user)
        resp = client.get("/query?site=example.com&start=nope")
        assert resp.status_code == 400

    def test_query_unknown_site(self, client, user):
        client.force_login(user)
        assert client.get("/query?site=other.com").status_code == 400

    def test_query_guest_access(self, client, user, host, counts):
        user.share_token = "tok123"
        user.save()
        resp = client.get(f"/query?site=example.com&user={user.uuid}&token=tok123")
        body = json.loads(resp.content)
        assert body["visits"]["pageview"]["/home"] == 13

    def test_query_guest_wrong_token(self, client, user, host):
        user.share_token = "tok123"
        user.save()
        resp = client.get(f"/query?site=example.com&user={user.uuid}&token=bad")
        assert resp.status_code == 401

    def test_query_demo_access(self, client, user, host, counts):
        demo = User.objects.create_user(username="demo", password="x")
        demo_host = Host.objects.create(user=demo, name="demo.example")
        Count.objects.create(host=demo_host, date=date.today(), category="pageview", item="/home", total=7)
        resp = client.get("/query?site=demo.example&demo=1")
        body = json.loads(resp.content)
        assert body["site"] == "demo.example"
        assert body["visits"]["pageview"]["/home"] == 7


class TestSites:
    def test_sites_not_signed_in(self, client):
        resp = client.get("/sites")
        assert resp.status_code == 401

    def test_sites_signed_in(self, client, user, host):
        Host.objects.create(user=user, name="other.com")
        client.force_login(user)
        resp = client.get("/sites")
        body = json.loads(resp.content)
        assert body == [
            {"name": "example.com", "hide": True},
            {"name": "other.com", "hide": True},
        ]

    def test_site_retrieve(self, client, user, host):
        client.force_login(user)
        resp = client.get("/sites/example.com")
        assert json.loads(resp.content)["name"] == "example.com"

    def test_sites_guest_access(self, client, user, host):
        user.share_token = "tok123"
        user.save()
        resp = client.get(f"/sites?user={user.uuid}&token=tok123")
        assert resp.status_code == 200
        assert [s["name"] for s in json.loads(resp.content)] == ["example.com"]

    def test_sites_demo_access(self, client, user, host):
        User.objects.create_user(username="demo", password="x")
        assert client.get("/sites?demo=1").status_code == 200

    def test_sites_write_methods(self, client, user, host):
        client.force_login(user)
        # The sites resource is full CRUD on the user->sites relation.
        assert client.post("/sites", {"name": "nope.com"}).status_code == 201
        assert client.put("/sites/example.com", {"name": "example.com"}, content_type="application/json").status_code == 200
        assert client.delete("/sites/example.com").status_code == 204


class TestMisc:
    def test_lang(self, client):
        resp = client.get("/lang", HTTP_ACCEPT_LANGUAGE="ru-RU,ru;q=0.9,en;q=0.8")
        assert resp.content.decode() == "RU"

    def test_lang_plain(self, client):
        resp = client.get("/lang", HTTP_ACCEPT_LANGUAGE="en")
        assert resp.content.decode() == "EN"

    def test_newsletter_register(self, client):
        assert client.post("/newsletter_register", {"mail": "a@b.c"}).status_code == 200
        assert client.post("/newsletter_register").status_code == 400

    def test_subscribed_json(self, client, user):
        client.force_login(user)
        resp = client.post("/subscribed", json.dumps({"subscription_id": "P-123"}), content_type="application/json")
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.subscription_id == "P-123"

    def test_subscribed_form(self, client, user):
        client.force_login(user)
        assert client.post("/subscribed", {"subscription_id": "P-456"}).status_code == 200
        user.refresh_from_db()
        assert user.subscription_id == "P-456"