from django.core.management import call_command
import pytest

from accounts.models import User
from .. import models
from ..management.commands.ingress import BadKeyError, Command


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_redis_key(redis, key, mapping):
    """Helper to set a Redis key with a mapping (hash)."""
    redis.hset(key, mapping=mapping)


# ---------------------------------------------------------------------------
# Fixtures – data
# ---------------------------------------------------------------------------

@pytest.fixture
def user_data():
    """Create all users referenced in the main ``redis_data`` fixture."""
    usernames = [
        "ApplePerson",
        "meisen",
        "eduard",
        "yum",
        "miako",
        "dora",
        "0x93",
        "supar",
        "Supb",
        "UPPERCASE",
        "miguel",
        "DancingRain",
        "valerie",
        "peter",
        "batho",
    ]
    for u in usernames:
        User.objects.get_or_create(username=u)
    return User.objects.filter(username__in=usernames)


@pytest.fixture
def host_data():
    """Create a pre-existing Host record for ApplePerson."""
    user, _ = User.objects.get_or_create(username="ApplePerson")
    return models.Host.objects.create(name="apple.store", user=user)


@pytest.fixture
def redis_data(redis):
    """Load a varied set of Redis keys that should be ingested correctly.

    All valid dates use the format YYYY-MM-DD.
    The last four keys are deliberately malformed and must be skipped.
    """
    entries = {
        "v:apple.store,ApplePerson,loc,2026-05-21": {"/": 2},
        "v:meisen.com,meisen,weekday,2026-05-21": {"4": 49},
        "v:long.sub.domain.ac.id,eduard,ref,2026-05-23": {
            "https://blog.com": 50,
            "https://b.it": 4,
        },
        "v:abcd.thisismemywebsitelong.blog,yum,loc,2026-05-22": {
            "/": 50,
            "/privacy.html": 20,
            "/blog": 31,
        },
        "v:bud.org,miako,lang,2026-05-23": {"de": 4, "en": 30},
        "v:blog.fas.pm,dora,ref,2026-05-22": {
            "http://example.com/page1.html": 3,
            "https://example.com/page2.html": 7,
        },
        "v:dash-dash.org,0x93,date,2026-05-23": {"2026-05-23": 50},
        "v:dash-3.reef.pl,dora,platform,2026-05-22": {"Android": 1},
        "v:chloe-miju.vercel.app,Supb,ref,2026-05-21": {"https://ab.co.uk": 4},
        "v:dacomic.co.ke,UPPERCASE,browser,2026-05-23": {"Chrome": 1, "Safari": 3},
        "v:sikalig.com.ua,miguel,screen,2026-05-22": {"1024x781": 2, "800x600": 5},
        "v:pepper-big-73e580.netlify.app,batho,screen,2026-05-21": {
            "1024x781": 2,
            "800x600": 1,
        },
        "v:mygitrep.github.io,DancingRain,browser,2026-05-22": {"Firefox": 1},
        "v:learntocook.com,valerie,platform,2026-05-22": {"Mobile": 5},
        # Malformed – these should be skipped by the command
        "v:learntocook.com,valerie,platform,all": {"foo": 1},
        "v:learntocook.com,valerie,platform,": {"foo": 1},
        "v:learntocook.com,,platform,2026-05-22": {"foo": 1},
        "v:,,,": {"foo": 1},
    }
    for key, mapping in entries.items():
        _set_redis_key(redis, key, mapping)
    return redis


# ---------------------------------------------------------------------------
# Tests – Command unit behaviour
# ---------------------------------------------------------------------------

class TestParseKey:
    """Direct tests of the ``_parse_key`` helper method."""

    def test_valid_key_returns_parsed_components(self):
        cmd = Command()
        result = cmd._parse_key(b"v:example.com,alice,pageview,2026-05-21")
        assert result == ("example.com", "alice", "pageview", "2026-05-21")

    def test_url_decoded_components(self):
        cmd = Command()
        result = cmd._parse_key(b"v:my%20site.com,hello%20world,loc,2026-08-01")
        assert result == ("my site.com", "hello world", "loc", "2026-08-01")

    def test_raises_for_non_utf8_bytes(self):
        cmd = Command()
        with pytest.raises(BadKeyError):
            cmd._parse_key(b"v:\xff\xfe")

    def test_raises_when_missing_prefix(self):
        cmd = Command()
        with pytest.raises(BadKeyError):
            cmd._parse_key(b"bad:prefix,user,metric,2026-01-01")

    def test_raises_when_too_few_fields(self):
        cmd = Command()
        with pytest.raises(BadKeyError):
            cmd._parse_key(b"v:onlyhost,user,loc")


class TestGetUniqueHosts:
    """Direct tests of the ``_get_unique_hosts`` helper."""

    def test_deduplicates_by_user_and_host(self):
        cmd = Command()
        records = [
            {"user_id": 1, "host": "a.com"},
            {"user_id": 1, "host": "a.com"},  # duplicate
            {"user_id": 1, "host": "b.com"},
            {"user_id": 2, "host": "a.com"},
        ]
        hosts = cmd._get_unique_hosts(records)
        assert len(hosts) == 3
        pairs = {(h.user_id, h.name) for h in hosts}
        assert pairs == {(1, "a.com"), (1, "b.com"), (2, "a.com")}


# ---------------------------------------------------------------------------
# Tests – Integration behaviour
# ---------------------------------------------------------------------------

class TestIngressCommand:
    """Integration tests for the ``ingress`` management command."""

    # --- Resilience ---

    def test_does_not_die_badly(self, db, user_data, host_data, redis_data):
        """All the fixture data is processed without raising an exception."""
        call_command("ingress")

    def test_does_not_die_on_empty_redis(self, db):
        """Running ingress when Redis is empty is harmless (no-op)."""
        call_command("ingress")
        assert models.Count.objects.count() == 0

    def test_no_count_objects_created_when_no_users_exist(self, db, redis):
        """If no users exist, valid keys produce no Count rows."""
        _set_redis_key(redis, "v:site.com,nobody,loc,2026-05-21", {"/": 5})
        call_command("ingress")
        assert models.Count.objects.count() == 0

    # --- Basic ingestion ---

    def test_simple(self, db, redis):
        """A known user + a valid key creates one Count."""
        User.objects.get_or_create(username="peter")
        _set_redis_key(redis, "v:website.com,peter,loc,2026-05-21", {"/": 1})
        _set_redis_key(redis, "v:example.com,usernotindb,loc,2026-05-21", {"/page": 2})

        call_command("ingress")

        assert models.Count.objects.count() == 1
        count = models.Count.objects.get()
        assert count.host.name == "website.com"
        assert count.host.user.username == "peter"
        assert count.metric == "loc"
        assert count.value == "/"
        assert count.count == 1
        assert str(count.date) == "2026-05-21"

    def test_multiple_values_per_key(self, db, redis):
        """A single Redis hash with several fields yields multiple Count rows."""
        User.objects.get_or_create(username="alice")
        _set_redis_key(
            redis,
            "v:mysite.com,alice,pageview,2026-06-01",
            {"/": 10, "/about": 5, "/contact": 3},
        )
        call_command("ingress")
        assert models.Count.objects.count() == 3
        assert models.Count.objects.get(value="/").count == 10

    def test_incremental_ingress(self, db, redis):
        """Running ingress again with the same key increments the count."""
        User.objects.get_or_create(username="peter")
        _set_redis_key(redis, "v:website.com,peter,loc,2026-05-21", {"/": 1})
        call_command("ingress")
        assert models.Count.objects.get().count == 1

        _set_redis_key(redis, "v:website.com,peter,loc,2026-05-21", {"/": 1})
        call_command("ingress")
        assert models.Count.objects.get().count == 2

    def test_host_auto_created(self, db, redis):
        """A non-existent Host is created on the fly."""
        User.objects.get_or_create(username="charlie")
        assert models.Host.objects.count() == 0

        _set_redis_key(redis, "v:newhost.com,charlie,loc,2026-07-01", {"/": 1})
        call_command("ingress")

        assert models.Host.objects.count() == 1
        host = models.Host.objects.get()
        assert host.name == "newhost.com"
        assert host.user.username == "charlie"

    def test_existing_host_reused(self, db, redis):
        """If the Host already exists it is reused (no duplicates)."""
        user, _ = User.objects.get_or_create(username="dave")
        models.Host.objects.create(name="dave.com", user=user)
        assert models.Host.objects.count() == 1

        _set_redis_key(redis, "v:dave.com,dave,loc,2026-07-01", {"/": 1})
        call_command("ingress")

        assert models.Host.objects.count() == 1
        assert models.Count.objects.get().host.name == "dave.com"

    # --- Post-ingestion cleanup ---

    def test_keys_removed_after_ingress(self, db, user_data, redis_data):
        """Valid Redis keys are deleted after ingestion."""
        call_command("ingress")
        remaining = redis_data.keys("v:*")
        for k in remaining:
            decoded = k.decode()
            assert decoded in (
                "v:learntocook.com,valerie,platform,all",
                "v:learntocook.com,valerie,platform,",
                "v:learntocook.com,,platform,2026-05-22",
                "v:,,,",
            ), f"Unexpected leftover key: {decoded}"

    # --- Bulk / fixture data ---

    def test_all_fixture_data_ingested(self, db, user_data, redis_data):
        """All valid entries from ``redis_data`` are persisted."""
        call_command("ingress")
        assert models.Count.objects.count() == 22

    def test_malformed_keys_skipped(self, db, redis):
        """Keys that don't match the expected schema are silently ignored."""
        _set_redis_key(redis, "v:missingfield,user,loc", {"/": 1})
        _set_redis_key(redis, "v:no_prefix", {"/": 1})
        _set_redis_key(redis, "v:,,,", {"x": 1})

        call_command("ingress")
        assert models.Count.objects.count() == 0

    def test_batch_argument(self, db, user_data, redis_data):
        """The ``--batch-size`` flag doesn't break processing."""
        call_command("ingress", batch_size=5)
        assert models.Count.objects.count() == 22

    def test_idempotent_when_no_new_data(self, db, redis):
        """Running ingress when no new keys exist changes nothing."""
        User.objects.get_or_create(username="alice")
        _set_redis_key(redis, "v:site.com,alice,loc,2026-06-01", {"/": 5})
        call_command("ingress")
        assert models.Count.objects.get().count == 5
        call_command("ingress")
        assert models.Count.objects.get().count == 5
