from django.core.cache import cache
from django.core.management import call_command
from django.urls import reverse
import pytest

from accounts.models import User
from .. import models


def _set_redis_key(redis, key, mapping):
    """Helper to set a redis key with a mapping."""
    redis.hset(key, mapping=mapping)


@pytest.fixture
def user_data():
    """Create users that are referenced in ``redis_data``."""
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


@pytest.fixture
def host_data():
    user, _ = User.objects.get_or_create(username="ApplePerson")
    models.Host.objects.create(name="apple.store", user=user)


@pytest.fixture
def redis_data(redis):
    """Load a varied set of Redis keys that should be ingested correctly.

    All dates use the format YYYY-MM-DD (two-digit month/day).
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


class TestIngressCommand:
    """Tests for the ``ingress`` management command."""

    def test_does_not_die_badly(self, db, user_data, host_data, redis_data):
        """All the fixture data is processed without error."""
        call_command("ingress")

    def test_does_not_die_on_empty_redis(self, db):
        """Running ingress when Redis is empty is harmless."""
        call_command("ingress")

    def test_malformed_keys_skipped(self, db, redis):
        """Keys that don't match the expected schema are silently ignored."""
        _set_redis_key(redis, "v:missingfield,user,loc", {"/": 1})
        _set_redis_key(redis, "v:no_prefix", {"/": 1})
        _set_redis_key(redis, "v:,,,", {"x": 1})

        call_command("ingress")
        assert models.Count.objects.count() == 0

    def test_simple(self, db, redis):
        """A known user + a valid key creates one Count.

        Unknown users are silently skipped.
        """
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

    def test_unknown_user_skipped(self, db, redis):
        """Keys whose username doesn't exist in the database are dropped."""
        User.objects.get_or_create(username="existing")
        _set_redis_key(redis, "v:good.com,existing,loc,2026-05-21", {"/": 5})
        _set_redis_key(redis, "v:bad.com,nobody,loc,2026-05-21", {"/": 99})

        call_command("ingress")

        assert models.Count.objects.count() == 1
        c = models.Count.objects.get()
        assert c.host.name == "good.com"

    def test_multiple_values_per_key(self, db, redis):
        """A single Redis hash with several fields yields multiple Count rows."""
        User.objects.get_or_create(username="alice")
        _set_redis_key(
            redis,
            "v:mysite.com,alice,pageview,2026-06-01",
            {
                "/": 10,
                "/about": 5,
                "/contact": 3,
            },
        )

        call_command("ingress")

        assert models.Count.objects.count() == 3
        assert models.Count.objects.get(value="/").count == 10
        assert models.Count.objects.get(value="/about").count == 5
        assert models.Count.objects.get(value="/contact").count == 3

    def test_multiple_metrics_and_dates(self, db, redis):
        """Different metrics / dates produce separate Count records."""
        User.objects.get_or_create(username="bob")
        _set_redis_key(redis, "v:bob.com,bob,loc,2026-06-01", {"/": 3})
        _set_redis_key(redis, "v:bob.com,bob,ref,2026-06-01", {"https://x.com": 1})
        _set_redis_key(redis, "v:bob.com,bob,loc,2026-06-02", {"/": 7})

        call_command("ingress")
        assert models.Count.objects.count() == 3

    def test_incremental_ingress(self, db, redis):
        """Running ingress again with the same key increments the count."""
        User.objects.get_or_create(username="peter")
        _set_redis_key(redis, "v:website.com,peter,loc,2026-05-21", {"/": 1})
        call_command("ingress")
        assert models.Count.objects.get().count == 1

        _set_redis_key(redis, "v:website.com,peter,loc,2026-05-21", {"/": 1})
        call_command("ingress")

        assert models.Count.objects.get().count == 2

    def test_incremental_multiple_values(self, db, redis):
        """Increment works correctly when multiple values exist."""
        User.objects.get_or_create(username="alice")
        _set_redis_key(redis, "v:site.com,alice,loc,2026-06-01", {"/": 2, "/about": 3})
        call_command("ingress")

        _set_redis_key(
            redis,
            "v:site.com,alice,loc,2026-06-01",
            {"/": 1, "/about": 1, "/contact": 5},
        )
        call_command("ingress")

        assert models.Count.objects.get(value="/").count == 3
        assert models.Count.objects.get(value="/about").count == 4
        assert models.Count.objects.get(value="/contact").count == 5

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

    def test_url_encoded_host_and_user(self, db, redis):
        """URL-encoded characters in host/user are decoded."""
        User.objects.get_or_create(username="hello world")
        _set_redis_key(
            redis,
            "v:my%20site.com,hello%20world,loc,2026-08-01",
            {"/": 1},
        )
        call_command("ingress")

        c = models.Count.objects.get()
        assert c.host.name == "my site.com"
        assert c.host.user.username == "hello world"

    def test_uppercase_username(self, db, redis):
        """Usernames with uppercase characters work."""
        User.objects.get_or_create(username="UPPERCASE")
        _set_redis_key(redis, "v:example.com,UPPERCASE,loc,2026-09-01", {"/": 1})
        call_command("ingress")

        assert models.Count.objects.get().host.user.username == "UPPERCASE"

    def test_keys_removed_after_ingress(self, db, user_data, redis_data):
        """Valid Redis keys are deleted after ingestion.

        Malformed keys that don't match the SCAN pattern are left untouched.
        """
        r = cache._cache.get_client()

        valid_before = r.keys("v:*,*,*,*")
        assert len(valid_before) > 0

        call_command("ingress")

        remaining = r.keys("v:*")
        for k in remaining:
            decoded = k.decode()
            assert decoded in (
                "v:learntocook.com,valerie,platform,all",
                "v:learntocook.com,valerie,platform,",
                "v:learntocook.com,,platform,2026-05-22",
                "v:,,,",
            ), f"Unexpected leftover key: {decoded}"

    def test_all_fixture_data_ingested(self, db, user_data, redis_data):
        """All 22 valid entries from ``redis_data`` are persisted."""
        call_command("ingress")
        assert models.Count.objects.count() == 22

    def test_batch_argument(self, db, user_data, redis_data):
        """The ``--batch-size`` flag doesn't break processing."""
        call_command("ingress", batch_size=5)
        assert models.Count.objects.count() == 22

    def test_split_across_multiple_batches(self, db, redis):
        """More keys than the batch size are all processed."""
        User.objects.get_or_create(username="alice")
        for i in range(20):
            _set_redis_key(
                redis,
                f"v:site{i}.com,alice,loc,2026-10-01",
                {f"/page{i}": i},
            )
        call_command("ingress", batch_size=5)
        assert models.Count.objects.count() == 20
