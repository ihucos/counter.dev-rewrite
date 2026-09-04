import json
from datetime import date, timedelta
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone

from core.models import Count, Host
from counter.models import Feedback, NewsletterSubscriber

User = get_user_model()


@pytest.fixture
def signed_up(db):
    return User.objects.create_user(
        username="newuser",
        email="new@example.com",
        password="s3cretpass",
        timezone=0,
    )


class TestLoginRegister:
    def test_login_success_sets_session(self, api_client, signed_up):
        response = api_client.post("/login", {"user": "newuser", "password": "s3cretpass"})
        assert response.status_code == 200
        assert "_authuser" in api_client.cookies or api_client.session.session_key

    def test_login_failure_returns_plain_text_error(self, api_client, signed_up):
        response = api_client.post("/login", {"user": "newuser", "password": "wrong"})
        assert response.status_code == 403
        assert "Wrong username or password" in response.content.decode()

    def test_register_creates_user_and_logs_in(self, api_client, db):
        response = api_client.post(
            "/register",
            {
                "user": "brandnew",
                "mail": "b@example.com",
                "password": "s3cretpass",
                "utcoffset": "120",
            },
        )
        assert response.status_code == 200
        user = User.objects.get(username="brandnew")
        assert user.email == "b@example.com"
        assert user.timezone == 120
        assert user.check_password("s3cretpass")

    def test_register_duplicate_username_rejected(self, api_client, signed_up):
        response = api_client.post(
            "/register",
            {"user": "newuser", "password": "s3cretpass", "utcoffset": "0"},
        )
        assert response.status_code == 400
        assert "already taken" in response.content.decode()


class TestRecover:
    def test_recover_sends_mail(self, api_client, signed_up):
        response = api_client.post(
            "/recover", {"mail": "new@example.com", "user": "newuser"}
        )
        assert response.status_code == 200
        assert len(mail.outbox) == 1
        assert "reset" in mail.outbox[0].body.lower()

    def test_recover_no_match_errors(self, api_client, signed_up):
        response = api_client.post("/recover", {"mail": "x@example.com", "user": "newuser"})
        assert response.status_code == 400


class TestAccountEdit:
    def test_updates_prefs_mail_and_timezone(self, auth_client, user):
        response = auth_client.post(
            "/account_edit",
            {
                "utcoffset": "60",
                "usesites": "1",
                "sites": "a.com\nb.com",
                "mail": "changed@example.com",
            },
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.timezone == 60
        assert user.email == "changed@example.com"
        assert user.prefs["usesites"] is True
        assert user.prefs["sites"] == "a.com\nb.com"

    def test_password_change(self, auth_client, user):
        response = auth_client.post(
            "/account_edit",
            {
                "utcoffset": "0",
                "usesites": "",
                "sites": "",
                "mail": user.email,
                "current_password": "testpass123",
                "new_password": "brandnewpass99",
                "repeat_new_password": "brandnewpass99",
            },
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.check_password("brandnewpass99")

    def test_password_change_wrong_current(self, auth_client, user):
        response = auth_client.post(
            "/account_edit",
            {
                "utcoffset": "0",
                "usesites": "",
                "sites": "",
                "mail": user.email,
                "current_password": "wrong",
                "new_password": "brandnewpass99",
                "repeat_new_password": "brandnewpass99",
            },
        )
        assert response.status_code == 400

    def test_requires_login(self, api_client):
        response = api_client.post("/account_edit", {"utcoffset": "0"})
        assert response.status_code == 403


class TestDeleteUserAndSite:
    def test_delete_user(self, api_client, user):
        api_client.force_login(user)
        response = api_client.post("/delete_user", {"confirmUser": user.username})
        assert response.status_code == 200
        assert not User.objects.filter(username=user.username).exists()

    def test_delete_user_confirm_mismatch(self, api_client, user):
        api_client.force_login(user)
        response = api_client.post("/delete_user", {"confirmUser": "nope"})
        assert response.status_code == 400
        assert User.objects.filter(username=user.username).exists()

    def test_delete_site_removes_host_and_counts(self, api_client, user, host, counts):
        api_client.force_login(user)
        user.prefs["site"] = host.name
        user.save()
        response = api_client.post("/delete_site")
        assert response.status_code == 200
        assert not Host.objects.filter(name=host.name).exists()
        assert not Count.objects.exists()


class TestShareTokens:
    def test_reset_token_creates_token(self, auth_client, user):
        response = auth_client.post("/reset_token")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.share_token

    def test_delete_token_revokes(self, auth_client, user):
        user.share_token = "tok"
        user.save()
        response = auth_client.post("/delete_token")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.share_token is None


class TestPrefs:
    def test_set_pref_site(self, auth_client, user):
        response = auth_client.get("/set_pref_site", QUERY_STRING="example.com")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.prefs["site"] == "example.com"

    def test_set_pref_range(self, auth_client, user):
        response = auth_client.get("/set_pref_range", QUERY_STRING="last7")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.prefs["range"] == "last7"


class TestMisc:
    def test_feedback(self, db, api_client):
        response = api_client.post(
            "/feedback", {"feedback": "great tool", "contact": "me@example.com"}
        )
        assert response.status_code == 200
        assert Feedback.objects.filter(message="great tool").exists()

    def test_newsletter_register(self, db, api_client):
        response = api_client.post("/newsletter_register", {"mail": "n@example.com"})
        assert response.status_code == 200
        assert NewsletterSubscriber.objects.filter(mail="n@example.com").exists()

    def test_subscribed(self, auth_client, user):
        response = auth_client.post("/subscribed", {"subscription_id": "I-ABC123"})
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.subscription_id == "I-ABC123"

    def test_lang_from_accept_language(self, api_client):
        response = api_client.get("/lang", HTTP_ACCEPT_LANGUAGE="ru-RU,ru;q=0.9,en;q=0.8")
        assert response.status_code == 200
        assert response.content.decode() == "RU"

    def test_lang_default(self, api_client):
        response = api_client.get("/lang")
        assert response.content.decode() == "EN"


class TestDump:
    def _consume(self, response):
        """Collect SSE messages from the streaming response (no waiting on the loop)."""
        chunks = []
        for chunk in response.streaming_content:
            chunks.append(chunk.decode())
            if len(chunks) >= 4:
                break
        return chunks

    def test_unauthenticated_gets_nouser(self, api_client):
        response = api_client.get("/dump")
        chunk = next(response.streaming_content).decode()
        assert chunk.startswith("data: ")
        message = json.loads(chunk[len("data: "):])
        assert message["type"] == "nouser"

    def test_session_dump_payload_shape(self, api_client, user, host, counts):
        api_client.force_login(user)
        response = api_client.get("/dump?utcoffset=120")
        chunks = self._consume(response)
        types = [json.loads(c[len("data: "):])["type"] for c in chunks]
        assert types[0] == "signedin"
        assert types[1] == "dump"
        assert types[2] == "archive"

        dump = json.loads(chunks[1][len("data: "):])["payload"]
        assert dump["user"]["uuid"] == str(user.uuid)
        assert dump["user"]["id"] == user.username
        assert dump["user"]["isSubscribed"] is False
        assert dump["meta"]["sessionless"] is False
        assert "example.com" in dump["sites"]
        assert dump["sites"]["example.com"]["visits"]["day"]["pageview"]["/home"] == 10

        archive = json.loads(chunks[2][len("data: "):])["payload"]
        assert "-7:-2" in archive
        assert "-30:-2" in archive

    def test_guest_access_with_valid_token(self, api_client, user, host, counts):
        user.share_token = "guesttok"
        user.save()
        response = api_client.get(
            "/dump", {"user": str(user.uuid), "token": "guesttok"}
        )
        chunks = self._consume(response)
        dump = json.loads(chunks[1][len("data: "):])["payload"]
        assert dump["meta"]["sessionless"] is True

    def test_guest_access_with_invalid_token_is_nouser(self, api_client, user, host):
        user.share_token = "guesttok"
        user.save()
        response = api_client.get("/dump", {"user": str(user.uuid), "token": "bad"})
        chunk = next(response.streaming_content).decode()
        assert json.loads(chunk[len("data: "):])["type"] == "nouser"


class TestDaterangeQuery:
    def test_query_across_sites(self, api_client, user, host, counts):
        api_client.force_login(user)
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        response = api_client.get("/query", {"from": start, "to": end})
        assert response.status_code == 200
        data = response.json()
        assert data["example.com"]["pageview"]["/home"] == 13

    def test_guest_can_query(self, api_client, user, host, counts):
        user.share_token = "guesttok"
        user.save()
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        response = api_client.get(
            "/query",
            {"from": start, "to": end, "user": str(user.uuid), "token": "guesttok"},
        )
        assert response.status_code == 200
        assert response.json()["example.com"]["pageview"]["/home"] == 13

    def test_invalid_dates(self, api_client, user, host):
        api_client.force_login(user)
        response = api_client.get("/query", {"from": "nope", "to": "also-nope"})
        assert response.status_code == 400
