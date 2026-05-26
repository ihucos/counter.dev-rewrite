from django.core.cache import cache
from django.core.management import call_command
import pytest

# User get_user_model
from accounts.models import User
from .. import models


@pytest.fixture
def user_data():
    User.objects.get_or_create(username="ApplePerson")
    User.objects.get_or_create(username="meisen")
    User.objects.get_or_create(username="eduard")
    User.objects.get_or_create(username="yum")
    User.objects.get_or_create(username="miako")
    User.objects.get_or_create(username="dora")
    User.objects.get_or_create(username="0x93")
    User.objects.get_or_create(username="supar")
    User.objects.get_or_create(username="Supb")
    User.objects.get_or_create(username="UPPERCASE")
    User.objects.get_or_create(username="miguel")
    User.objects.get_or_create(username="DancingRain")
    User.objects.get_or_create(username="valerie")


@pytest.fixture
def host_data():
    models.Host.objects.create(
        name="apple.store", user=User.objects.get_or_create(username="ApplePerson")[0]
    )


@pytest.fixture
def redis_data(redis):
    redis.hset(
        "v:apple.store,ApplePerson,loc,2026-05-21",
        mapping={"/": 2},
    )
    redis.hset(
        "v:meisen.com,meisen,weekday,2026-05-21",
        mapping={"4": 49},
    )
    redis.hset(
        "v:long.sub.domain.ac.id,eduard,ref,2026-05-23",
        mapping={"https://blog.com": 50, "https://b.it": 4},
    )
    redis.hset(
        "v:abcd.thisismemywebsitelong.blog,yum,loc,2026-05-22",
        mapping={"/": 50, "/privacy.html": 20, "/blog": 31},
    )
    redis.hset(
        "v:bud.org,miako,lang,2026-05-23",
        mapping={"de": 4, "en": 30},
    )
    redis.hset(
        "v:blog.fas.pm,dora,ref,2026-05-22",
        mapping={
            "http://example.com/page1.html": 3,
            "https://example.com/page2.html": 7,
        },
    )
    redis.hset(
        "v:dash-dash.org,0x93,date,2026-05-23",
        mapping={"2026-05-23": 50},
    )
    redis.hset(
        "v:dash-3.reef.pl,dora,platform,2026-05-22",
        mapping={"Android": 1},  # wrong key
    )
    redis.hset(
        "v:chloe-miju.vercel.app,Supb,ref,2026-05-21",
        mapping={"https://ab.co.uk": 4},
    )
    redis.hset(
        "v:dacomic.co.ke,UPPERCASE,browser,2026-05-23",
        mapping={"Chrome": 1, "Safari": 3},
    )
    redis.hset(
        "v:sikalig.com.ua,miguel,screen,2026-05-22",
        mapping={"1024x781": 2, "800x600": 5},
    )
    redis.hset(
        "v:pepper-big-73e580.netlify.app,batho,screen,2026-05-21",
        mapping={"1024x781": 2, "800x600": 1},
    )
    redis.hset(
        "v:mygitrep.github.io,DancingRain,browser,2026-05-22",
        mapping={"Firefox": 1},
    )
    redis.hset(
        "v:learntocook.com,valerie,platform,2026-05-22",
        mapping={"Mobile": 5},  # Wrong keys
    )

    # put in some things that should not match / malformed
    redis.hset(
        "v:learntocook.com,valerie,platform,all",
        mapping={"foo": 1},  # Wrong keys
    )
    redis.hset(
        "v:learntocook.com,valerie,platform,",
        mapping={"foo": 1},  # Wrong keys
    )
    redis.hset(
        "v:learntocook.com,,platform,2026-05-22",
        mapping={"foo": 1},  # Wrong keys
    )
    redis.hset(
        "v:,,,",
        mapping={"foo": 1},  # Wrong keys
    )


class TestIngressView:
    def test_does_not_die_badly(self, db, user_data, host_data, redis_data):
        call_command("ingress")
        call_command("ingress")

    def test_simple(self, db, redis):
        User.objects.get_or_create(username="peter")
        redis.hset(
            "v:website.com,peter,loc,2026-05-21",
            mapping={"/": 1},
        )
        redis.hset(
            "v:example.com,usernotindb,loc,2026-05-21",
            mapping={"/page": 2},
        )
        call_command("ingress")
        count = models.Count.objects.get()
        assert count.host.name == "website.com"
        assert count.host.user.username == "peter"
        assert count.metric == "loc"
        assert count.value == "/"
        assert count.count == 1

        redis.hset(
            "v:website.com,peter,loc,2026-05-21",
            mapping={"/": 1},
        )
        call_command("ingress")
        count = models.Count.objects.get()
        assert count.count == 2
        assert User.objects.get().username == "peter", "Only peter user is created"
