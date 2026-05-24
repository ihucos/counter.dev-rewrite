from django.core.management.base import BaseCommand, CommandError
from counts.models import Count, Host
from time import sleep
from django.core.cache import cache
from django.db.models.query_utils import Q

# TODO: All keys can be hashes after the big app rewrite
ZET_KEYS = ["lang", "ref", "loc", "page"]
# from .... import models
from accounts.models import User


class Command(BaseCommand):
    help = "Ingress data into the Counts app, creating or updating Count records."

    def add_arguments(self, parser):
        parser.add_argument("--forever", action="store_true")

    def parse_key(self, key):
        if not key.startswith(b"v:"):
            raise ValueError("bad key")
        key = key[len(b"v:") :]
        try:
            host, user, metric, date = key.split(b",")
        except ValueError:
            raise ValueError("bad key")
        # urldecode!!
        return host, user, metric, date

    def handle(self, *args, **options):
        forever = options["forever"]
        assert forever, "only --forever is supported"

        # Get the raw Redis client from Django's cache backend
        # cache._cache is a RedisCacheClient, which has get_client() returning redis.Redis
        redis = cache._cache.get_client()

        cursor = 0
        while True:
            cursor, keys = redis.scan(cursor=cursor, match="v:*,*,*,*-*-*", count=10)
            pipeline = redis.pipeline()
            keys_parts = []
            for key in keys:
                try:
                    key_parts = self.parse_key(key)
                except ValueError:
                    continue
                keys_parts.append(key_parts)
                pipeline.hgetall(key)

            redis_response = pipeline.execute()

            self._ingress_batch(
                [
                    list(  # use * at python 3.15
                        {
                            "user": user,
                            "host": host,
                            "metric": metric,
                            "date": date,
                            "value": value,
                            "count": count,
                        }
                        for (value, count) in vals.items()
                    )
                    for ((host, user, metric, date), vals) in zip(
                        keys_parts, redis_response
                    )
                ]
            )

    def _ingress_batch(self, vals):
        # Hack
        vals_new = []
        for i in vals:
            vals_new.extend(i)
        vals = vals_new

        user_identifiables = [i["user"] for i in vals]
        # use get_user_model

        # matched_users = User.objects.filter(Q(username__in=user) | Q(id__in=[]))
        user_map = User.objects.in_bulk(user_identifiables, field_name="username")

        print(user_identifiables)
        print(user_map)

        assert 0
