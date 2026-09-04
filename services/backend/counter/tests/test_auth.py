"""Integration tests for the documented API (docs/api.md)."""

import json
from urllib.parse import quote

import pytest
from django.core import mail
from django.contrib.auth import get_user_model

User = get_user_model()

from core.models import Host

pytestmark = pytest.mark.django_db


def messages(response):
    """Parse the SSE messages until the stream is exhausted or a dump arrives.

    The dump stream repeats every 15s, so stop once the first dump arrives.
    """
    out = []
    buffer = ""
    for chunk in response.streaming_content:
        buffer += chunk.decode()
        while "\n\n" in buffer:
            part, buffer = buffer.split("\n\n", 1)
            part = part.strip()
            if part.startswith("data: "):
                message = json.loads(part[len("data: "):])
                out.append(message)
                if message["type"] == "dump":
                    return out
    return out


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
        assert resp.content.decode() == "user already exists"


class TestLogin:
    def test_login_sets_session(self, client, user):
        resp = client.post("/login", {"user": "testuser", "password": "testpass123"})
        assert resp.status_code == 200
        assert client.session.get("_auth_user_id") == str(user.id)

    def test_login_wrong_password(self, client, user):
        resp = client.post("/login", {"user": "testuser", "password": "nope"})
        assert resp.status_code == 400
        assert resp.content.decode() == "wrong password"

    def test_login_unknown_user(self, client):
        resp = client.post("/login", {"user": "ghost", "password": "nope"})
        assert resp.status_code == 400
        assert resp.content.decode() == "no such user"


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


class TestAccountEdit:
    def test_account_edit(self, client, user):
        client.force_login(user)
        resp = client.post(
            "/account_edit",
            {"utcoffset": -60, "usesites": "true", "sites": "example.com\nwww.foo.bar/", "mail": "a@b.c"},
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.timezone == -60
        assert user.email == "a@b.c"
        assert user.prefs["usesites"] is True
        names = sorted(Host.objects.filter(user=user).values_list("name", flat=True))
        assert names == ["example.com", "foo.bar"]

    def test_account_edit_removes_deleted_sites(self, client, user):
        client.force_login(user)
        Host.objects.create(user=user, name="old.com")
        resp = client.post("/account_edit", {"utcoffset": 0, "usesites": "false", "sites": "new.com", "mail": ""})
        assert resp.status_code == 200
        names = list(Host.objects.filter(user=user).values_list("name", flat=True))
        assert names == ["new.com"]


class TestDeleteUser:
    def test_delete_user(self, client, user, host):
        client.force_login(user)
        resp = client.post("/delete_user")
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
    def test_delete_site_removes_selected_site_and_counts(self, client, user, host, counts):
        client.force_login(user)
        prefs = dict(user.prefs)
        prefs["site"] = "example.com"
        user.prefs = prefs
        user.save()
        resp = client.post("/delete_site")
        assert resp.status_code == 200
        assert not Host.objects.filter(name="example.com").exists()

    def test_delete_site_without_selection(self, client, user):
        client.force_login(user)
        assert client.post("/delete_site").status_code == 400


class TestShareToken:
    def test_reset_and_delete_token(self, client, user):
        client.force_login(user)
        resp = client.post("/reset_token")
        assert resp.status_code == 200
        token = json.loads(resp.content)["token"]
        user.refresh_from_db()
        assert user.share_token == token

        resp = client.post("/delete_token")
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.share_token == ""


class TestPrefs:
    def test_set_pref_site(self, client, user):
        client.force_login(user)
        resp = client.get("/set_pref_site?example.com")
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.prefs["site"] == "example.com"

    def test_set_pref_range(self, client, user):
        client.force_login(user)
        assert client.get("/set_pref_range?last7").status_code == 200
        user.refresh_from_db()
        assert user.prefs["range"] == "last7"

    def test_set_pref_range_invalid(self, client, user):
        client.force_login(user)
        assert client.get("/set_pref_range?nope").status_code == 400


class TestDump:
    def test_nouser(self, client):
        resp = client.get("/dump")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/event-stream"
        assert messages(resp)[0]["type"] == "nouser"

    def test_dump_signed_in(self, client, user, host, counts):
        client.force_login(user)
        resp = client.get("/dump?utcoffset=60")
        signedin, dump = messages(resp)[:2]
        assert signedin["type"] == "signedin"
        assert dump["type"] == "dump"
        sites = dump["payload"]["sites"]
        assert sites["example.com"]["visits"]["day"]["pageview"]["/home"] == 10
        assert sites["example.com"]["visits"]["yesterday"]["pageview"]["/home"] == 3
        assert dump["payload"]["meta"]["utcoffset"] == 60

    def test_dump_guest_access(self, client, user, host, counts):
        user.share_token = "tok123"
        user.save()
        resp = client.get(f"/dump?user={user.uuid}&token=tok123")
        dump = messages(resp)[1]
        assert "example.com" in dump["payload"]["sites"]

    def test_dump_guest_wrong_token(self, client, user, host):
        user.share_token = "tok123"
        user.save()
        resp = client.get(f"/dump?user={user.uuid}&token=bad")
        assert messages(resp)[0]["type"] == "nouser"

    def test_dump_custom_range(self, client, user, host, counts):
        client.force_login(user)
        from datetime import date, timedelta

        to = date.today()
        frm = to - timedelta(days=6)
        resp = client.get(f"/dump?from={frm}&to={to}")
        dump = messages(resp)[1]
        visits = dump["payload"]["sites"]["example.com"]["visits"]
        assert visits["custom"]["pageview"]["/home"] == 13


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
        assert user.prefs["subscription_id"] == "P-123"

    def test_subscribed_form(self, client, user):
        client.force_login(user)
        assert client.post("/subscribed", {"subscription_id": "P-456"}).status_code == 200
        user.refresh_from_db()
        assert user.prefs["subscription_id"] == "P-456"