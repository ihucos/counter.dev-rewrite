from django.core.management import call_command
import pytest

from core import models
from core.management.commands.sync import BadKeyError, Command
from django.contrib.auth import get_user_model


User = get_user_model()


@pytest.fixture
def user_data():
    """Create users referenced in the redis_data fixture."""
    for u in ["alice", "bob", "charlie"]:
        User.objects.get_or_create(username=u)
    return User.objects.filter(username__in=["alice", "bob", "charlie"])


@pytest.fixture
def host_data():
    """Create a pre-existing Host record for alice."""
    user, _ = User.objects.get_or_create(username="alice")
    return models.Host.objects.create(name="alicesite.com", user=user)


@pytest.fixture
def redis_data(redis):
    """Load minimal Redis keys for ingestion tests.

    - 4 valid keys (testing single value, multiple values, various components)
    - 2 deliberately malformed keys that must be skipped
    """
    entries = {
        # Valid
        "v:alicesite.com,alice,pageview,2026-05-21": {"/": 5},
        "v:bobsite.com,bob,click,2026-05-22": {"button1": 3, "button2": 7},
        "v:charliesite.com,charlie,screen,2026-05-23": {"1024x768": 2},
        # Multiple values per key
        "v:alicesite.com,alice,pageview,2026-05-22": {"/home": 10, "/about": 4},
        # Malformed – these should be skipped
        "v:bobsite.com,bob,click,all": {"x": 1},
        "v:,,,": {"x": 1},
    }
    for key, mapping in entries.items():
        redis.hset(key, mapping=mapping)
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


class TestSyncCommand:
    """Integration tests for the ``sync`` management command."""

    # --- Resilience ---

    def test_does_not_die_badly(self, db, user_data, host_data, redis_data):
        """All the fixture data is processed without raising an exception."""
        call_command("sync")

    def test_does_not_die_on_empty_redis(self, db):
        """Running sync when Redis is empty is harmless (no-op)."""
        call_command("sync")
        assert models.Count.objects.count() == 0

    def test_no_count_objects_created_when_no_users_exist(self, db, redis):
        """If no users exist, valid keys produce no Count rows."""
        redis.hset("v:site.com,nobody,loc,2026-05-21", mapping={"/": 5})
        call_command("sync")
        assert models.Count.objects.count() == 0

    # --- Basic ingestion ---

    def test_simple(self, db, redis):
        """A known user + a valid key creates one Count."""
        User.objects.get_or_create(username="peter")
        redis.hset("v:website.com,peter,loc,2026-05-21", mapping={"/": 1})
        redis.hset("v:example.com,usernotindb,loc,2026-05-21", mapping={"/page": 2})

        call_command("sync")

        assert models.Count.objects.count() == 1
        count = models.Count.objects.get()
        assert count.host.name == "website.com"
        assert count.host.user.username == "peter"
        assert count.category == "loc"
        assert count.item == "/"
        assert count.total == 1
        assert str(count.date) == "2026-05-21"

    def test_multiple_values_per_key(self, db, redis):
        """A single Redis hash with several fields yields multiple Count rows."""
        User.objects.get_or_create(username="alice")
        redis.hset(
            "v:mysite.com,alice,pageview,2026-06-01",
            mapping={"/": 10, "/about": 5, "/contact": 3},
        )
        call_command("sync")
        assert models.Count.objects.count() == 3
        assert models.Count.objects.get(item="/").total == 10

    def test_incremental_sync(self, db, redis):
        """Running sync again with the same key increments the count."""
        User.objects.get_or_create(username="peter")
        redis.hset("v:website.com,peter,loc,2026-05-21", mapping={"/": 1})
        call_command("sync")
        assert models.Count.objects.get().total == 1

        redis.hset("v:website.com,peter,loc,2026-05-21", mapping={"/": 1})
        call_command("sync")
        assert models.Count.objects.get().total == 2

    def test_host_auto_created(self, db, redis):
        """A non-existent Host is created on the fly."""
        User.objects.get_or_create(username="charlie")
        assert models.Host.objects.count() == 0

        redis.hset("v:newhost.com,charlie,loc,2026-07-01", mapping={"/": 1})
        call_command("sync")

        assert models.Host.objects.count() == 1
        host = models.Host.objects.get()
        assert host.name == "newhost.com"
        assert host.user.username == "charlie"

    def test_existing_host_reused(self, db, redis):
        """If the Host already exists it is reused (no duplicates)."""
        user, _ = User.objects.get_or_create(username="dave")
        models.Host.objects.create(name="dave.com", user=user)
        assert models.Host.objects.count() == 1

        redis.hset("v:dave.com,dave,loc,2026-07-01", mapping={"/": 1})
        call_command("sync")

        assert models.Host.objects.count() == 1
        assert models.Count.objects.get().host.name == "dave.com"

    # --- Post-ingestion cleanup ---

    def test_keys_removed_after_sync(self, db, user_data, redis_data):
        """Valid Redis keys are deleted after ingestion."""
        call_command("sync")
        remaining = redis_data.keys("v:*")
        for k in remaining:
            decoded = k.decode()
            assert decoded in (
                "v:bobsite.com,bob,click,all",
                "v:,,,",
            ), f"Unexpected leftover key: {decoded}"

    # --- Bulk / fixture data ---

    def test_all_fixture_data_ingested(self, db, user_data, redis_data):
        """All valid entries from ``redis_data`` are persisted."""
        call_command("sync")
        # 4 valid keys produce 6 Count rows:
        #   alicesite.com,alice,pageview,2026-05-21  -> 1 value
        #   bobsite.com,bob,click,2026-05-22         -> 2 values
        #   charliesite.com,charlie,screen,2026-05-23 -> 1 value
        #   alicesite.com,alice,pageview,2026-05-22  -> 2 values
        assert models.Count.objects.count() == 6

    def test_malformed_keys_skipped(self, db, redis):
        """Keys that don't match the expected schema are silently ignored."""
        redis.hset("v:missingfield,user,loc", mapping={"/": 1})
        redis.hset("v:no_prefix", mapping={"/": 1})
        redis.hset("v:,,,", mapping={"x": 1})

        call_command("sync")
        assert models.Count.objects.count() == 0

    def test_batch_argument(self, db, user_data, redis_data):
        """The ``--batch-size`` flag doesn't break processing."""
        call_command("sync", batch_size=5)
        assert models.Count.objects.count() == 6

    def test_idempotent_when_no_new_data(self, db, redis):
        """Running sync when no new keys exist changes nothing."""
        User.objects.get_or_create(username="alice")
        redis.hset("v:site.com,alice,loc,2026-06-01", mapping={"/": 5})
        call_command("sync")
        assert models.Count.objects.get().total == 5
        call_command("sync")
        assert models.Count.objects.get().total == 5
