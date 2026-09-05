"""Tests for site management, tokens, preferences, and misc views."""

import json
from datetime import date

import pytest

from core.models import Host
from core.api import parse_log_line, _normalize_domain

pytestmark = pytest.mark.django_db


class TestAccountEditView:
    def test_requires_auth(self, client):
        assert client.post("/account_edit").status_code == 401

    def test_updates_prefs_and_sites(self, client, user, host):
        other = Host.objects.create(user=user, name="remove-me.com")
        client.force_login(user)
        resp = client.post(
            "/account_edit",
            {
                "utcoffset": "-2",
                "usesites": "true",
                "mail": "new@example.com",
                "sites": "example.com\nhttps://www.newsite.org/\n",
            },
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.timezone == -2
        assert user.email == "new@example.com"
        assert user.prefs["usesites"] is True
        names = set(Host.objects.filter(user=user).values_list("name", flat=True))
        assert names == {"example.com", "newsite.org"}
        assert not Host.objects.filter(pk=other.pk).exists()

    def test_invalid_utcoffset(self, client, user):
        client.force_login(user)
        resp = client.post("/account_edit", {"utcoffset": "nope"})
        assert resp.status_code == 400


class TestDeleteSiteView:
    def test_requires_auth(self, client):
        assert client.post("/delete_site").status_code == 401

    def test_requires_selected_site(self, client, user, host):
        client.force_login(user)
        resp = client.post("/delete_site")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "no site selected"

    def test_deletes_site_and_counts(self, client, user, host, counts):
        user.prefs = {"site": "example.com"}
        user.save()
        client.force_login(user)
        assert client.post("/delete_site").status_code == 200
        assert not Host.objects.filter(pk=host.pk).exists()
        assert not counts.exists()

    def test_no_such_site(self, client, user, host):
        user.prefs = {"site": "missing.com"}
        user.save()
        client.force_login(user)
        assert client.post("/delete_site").status_code == 400


class TestShareTokens:
    def test_reset_token(self, client, user):
        client.force_login(user)
        resp = client.post("/reset_token")
        assert resp.status_code == 200
        token = json.loads(resp.content)["token"]
        user.refresh_from_db()
        assert user.share_token == token

    def test_delete_token(self, client, user):
        user.share_token = "sometoken"
        user.save()
        client.force_login(user)
        assert client.post("/delete_token").status_code == 200
        user.refresh_from_db()
        assert user.share_token == ""

    def test_requires_auth(self, client):
        assert client.post("/reset_token").status_code == 401
        assert client.post("/delete_token").status_code == 401


class TestPreferences:
    def test_set_pref_site(self, client, user):
        client.force_login(user)
        assert client.get("/set_pref_site", {"site": "example.com"}).status_code == 200
        user.refresh_from_db()
        assert user.prefs["site"] == "example.com"

    def test_set_pref_site_requires_auth(self, client):
        assert client.get("/set_pref_site", {"site": "x"}).status_code == 401

    def test_set_pref_range(self, client, user):
        client.force_login(user)
        assert client.get("/set_pref_range", {"range": "last30"}).status_code == 200
        user.refresh_from_db()
        assert user.prefs["range"] == "last30"

    def test_set_pref_range_invalid(self, client, user):
        client.force_login(user)
        resp = client.get("/set_pref_range", {"range": "bogus"})
        assert resp.status_code == 400


class TestLangView:
    def test_region_tag_returns_country(self, client):
        resp = client.get("/lang", HTTP_ACCEPT_LANGUAGE="de-DE,de;q=0.9")
        assert resp.content == b"DE"

    def test_plain_tag(self, client):
        assert client.get("/lang", HTTP_ACCEPT_LANGUAGE="ru").content == b"RU"

    def test_empty_header_defaults_to_en(self, client):
        assert client.get("/lang").content == b"EN"

    def test_wildcard_ignored(self, client):
        assert client.get("/lang", HTTP_ACCEPT_LANGUAGE="*").content == b"EN"


class TestSubscribedView:
    def test_requires_auth(self, client):
        resp = client.post("/subscribed", {"subscription_id": "I-ABC123"})
        assert resp.status_code == 401

    def test_missing_subscription_id(self, client, user):
        client.force_login(user)
        assert client.post("/subscribed", {}).status_code == 400

    def test_stores_subscription_id(self, client, user):
        client.force_login(user)
        assert client.post("/subscribed", {"subscription_id": "I-ABC123"}).status_code == 200
        user.refresh_from_db()
        assert user.prefs["subscription_id"] == "I-ABC123"

    def test_accepts_json_body(self, client, user):
        client.force_login(user)
        resp = client.post(
            "/subscribed",
            data=json.dumps({"subscription_id": "I-JSON"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.prefs["subscription_id"] == "I-JSON"


class TestNewsletterRegisterView:
    def test_requires_mail(self, client):
        assert client.post("/newsletter_register", {}).status_code == 400

    def test_ok(self, client):
        assert client.post("/newsletter_register", {"mail": "a@b.com"}).status_code == 200


class TestGuestAccess:
    """Dashboard-data endpoints accept ?user=<uuid>&token=<share_token>."""

    def test_guest_with_valid_token_sees_data(self, client, user, host, counts):
        user.share_token = "tok"
        user.save()
        resp = client.get("/query", {"site": "example.com", "user": str(user.uuid), "token": "tok"})
        assert json.loads(resp.content)["visits"]["pageview"]["/home"] == 13

    def test_guest_with_bad_token_is_unauthorized(self, client, user, host):
        user.share_token = "tok"
        user.save()
        resp = client.get("/query", {"site": "example.com", "user": str(user.uuid), "token": "wrong"})
        assert resp.status_code == 401

    def test_guest_with_unknown_uuid_is_unauthorized(self, client):
        resp = client.get(
            "/query",
            {"site": "example.com", "user": "00000000-0000-0000-0000-000000000000", "token": "tok"},
        )
        assert resp.status_code == 401


class TestParseLogLine:
    def test_full_line(self):
        entry = parse_log_line("[2026-09-04 12:34:56] DE https://google.com/ Firefox Windows")
        assert entry == {
            "timestamp": "2026-09-04 12:34:56",
            "date": "2026-09-04",
            "time": "12:34:56",
            "country": "de",
            "referrer": "https://google.com/",
            "device": "Firefox",
            "platform": "Windows",
            "extra": "",
        }

    def test_missing_fields_become_empty(self):
        entry = parse_log_line("[2026-09-04 12:34:56] - - Mobile")
        assert entry["country"] == ""
        assert entry["referrer"] == ""
        assert entry["device"] == "Mobile"
        assert entry["platform"] == ""
        assert entry["extra"] == ""

    def test_extra_parts(self):
        entry = parse_log_line("[2026-09-04 12:34:56] US - Desktop Linux extra stuff")
        assert entry["extra"] == "extra stuff"

    def test_bad_timestamp_falls_back_to_splitting(self):
        entry = parse_log_line("[not-a-date] US - - -")
        assert entry["date"] == "not-a-date"
        assert entry["time"] == ""

    def test_no_bracket_returns_none(self):
        assert parse_log_line("2026-09-04 nope") is None

    def test_too_few_parts_returns_none(self):
        assert parse_log_line("[2026-09-04 12:34:56] only") is None

    def test_country_lowercased(self):
        assert parse_log_line("[2026-09-04 12:34:56] US - -")["country"] == "us"


def test_normalize_domain():
    assert _normalize_domain("https://www.example.com/") == "example.com"
    assert _normalize_domain("http://example.com") == "example.com"
    assert _normalize_domain("example.com") == "example.com"


def test_local_date_uses_hours():
    # The tracker and frontend treat utcoffset as whole hours; the backend
    # must not interpret it as minutes (the unit mismatch used to bucket
    # visits into the wrong day away from UTC).
    from datetime import timedelta

    from django.utils import timezone as dj_timezone

    from core.api import _local_date

    now = dj_timezone.now()
    assert _local_date(2) == (now + timedelta(hours=2)).date()
    assert _local_date(-2) == (now - timedelta(hours=2)).date()
    # clamped like the tracker (parseUTCOffset in handler.go)
    assert _local_date(600) == (now + timedelta(hours=14)).date()
    assert _local_date(-600) == (now - timedelta(hours=12)).date()