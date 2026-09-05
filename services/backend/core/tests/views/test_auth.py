"""Tests for authentication and account views."""

import pytest
from django.core import mail

from core.models import Host

pytestmark = pytest.mark.django_db


class TestLoginView:
    def test_login_success(self, client, user):
        resp = client.post("/login", {"user": "testuser", "password": "testpass123"})
        assert resp.status_code == 200
        assert resp.content == b"ok"
        assert client.session["_auth_user_id"] == str(user.pk)

    def test_login_missing_fields(self, client, user):
        assert client.post("/login", {"user": "testuser"}).status_code == 400
        assert client.post("/login", {}).status_code == 400

    def test_login_no_such_user(self, client):
        resp = client.post("/login", {"user": "nobody", "password": "pw"})
        assert resp.status_code == 400
        assert resp.content == b"no such user"

    def test_login_wrong_password(self, client, user):
        resp = client.post("/login", {"user": "testuser", "password": "wrong"})
        assert resp.status_code == 400
        assert resp.content == b"wrong password"


class TestRegisterView:
    def test_register_success(self, client):
        resp = client.post(
            "/register",
            {"user": "newuser", "password": "pw123456", "mail": "n@example.com", "utcoffset": "2"},
        )
        assert resp.status_code == 200
        assert resp.content == b"ok"
        from counter.models import User
        account = User.objects.get(username="newuser")
        assert account.email == "n@example.com"
        assert account.timezone == 2

    def test_register_logs_user_in(self, client):
        client.post("/register", {"user": "newuser", "password": "pw123456"})
        resp = client.post("/reset_token")
        assert resp.status_code == 200  # authenticated endpoints now work

    def test_register_missing_fields(self, client):
        assert client.post("/register", {"user": "x"}).status_code == 400

    def test_register_duplicate_user(self, client, user):
        resp = client.post("/register", {"user": "testuser", "password": "pw123456"})
        assert resp.status_code == 400
        assert resp.content == b"user already exists"

    def test_register_invalid_utcoffset(self, client):
        resp = client.post(
            "/register", {"user": "x", "password": "pw", "utcoffset": "abc"}
        )
        assert resp.status_code == 400
        assert resp.content == b"invalid utcoffset"


class TestRecoverView:
    def test_recover_sends_mail(self, client, user, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        user.email = "me@example.com"
        user.save()
        resp = client.post("/recover", {"mail": "me@example.com", "user": "testuser"})
        assert resp.status_code == 200
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["me@example.com"]
        assert "testuser" in mail.outbox[0].body

    def test_recover_unknown_account_sends_nothing(self, client):
        resp = client.post("/recover", {"mail": "me@example.com", "user": "testuser"})
        assert resp.status_code == 200
        assert len(mail.outbox) == 0

    def test_recover_missing_fields(self, client):
        assert client.post("/recover", {"mail": "me@example.com"}).status_code == 400


class TestDeleteUserView:
    def test_requires_auth(self, client):
        assert client.post("/delete_user").status_code == 403

    def test_deletes_account_and_hosts(self, client, user, host):
        client.force_login(user)
        assert client.post("/delete_user").status_code == 200
        assert not Host.objects.filter(pk=host.pk).exists()


class TestFeedbackView:
    def test_requires_feedback(self, client):
        assert client.post("/feedback", {}).status_code == 400
        assert client.post("/feedback", {"feedback": ""}).status_code == 400

    def test_sends_feedback(self, client, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        resp = client.post(
            "/feedback", {"feedback": "great tool", "contact": "me@example.com"}
        )
        assert resp.status_code == 200
        assert len(mail.outbox) == 1
        assert "great tool" in mail.outbox[0].body
        assert "me@example.com" in mail.outbox[0].body