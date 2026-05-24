from django.core.cache import cache
from django.core.management import call_command
import pytest

# User get_user_model
from accounts.models import User


@pytest.fixture
def user_data():
    User.objects.create(username="ApplePerson")


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
        "v:bud.org,miakatojamazi,lang,2026-05-23",
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
        "v:dash-3.reef.pl,supar,platform,2026-05-22",
        mapping={"Android": 1},  # wrong key
    )
    redis.hset(
        "v:chloe-miju.vercel.app,Supb,ref,2026-05-21",
        mapping={"https://ab.co.uk": 4},
    )
    redis.hset(
        "v:dacomic.co.ke,UPERCASE,browser,2026-05-23",
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
    def test_does_not_die_badly(self, db, user_data, redis_data):
        call_command("ingress", forever=True)
