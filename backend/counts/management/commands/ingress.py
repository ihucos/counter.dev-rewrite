from django.core.management.base import BaseCommand, CommandError
from counts.models import Count, Host
from time import sleep
from django.core.cache import cache
from django.db.models.query_utils import Q

# TODO: All keys can be hashes after the big app rewrite
ZET_KEYS = ["lang", "ref", "loc", "page"]
from ... import models
from accounts.models import User


class Command(BaseCommand):
    help = "Ingress data into the Counts app, creating or updating Count records."

    def add_arguments(self, parser):
        parser.add_argument("--forever", action="store_true")

    def parse_key(self, key):
        if not key.startswith("v:"):
            raise ValueError("bad key")
        key = key[len(b"v:") :]
        try:
            host, user, metric, date = key.split(",")
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

            # This can fail
            keys = [i.decode() for i in keys]

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
        vals = list(vals)

        # Hack
        vals_new = []
        for i in vals:
            vals_new.extend(i)
        vals = vals_new

        # Map users specified in redis to database users
        user_identifiables = [i["user"] for i in vals]  # use get_user_model
        user_map = {}
        user_map.update(User.objects.in_bulk(user_identifiables, field_name="id"))
        user_map.update(User.objects.in_bulk(user_identifiables, field_name="username"))

        # Drop users not in database
        for v in list(vals):
            if v["user"] not in user_map:
                vals.remove(v)

        # # Create missing hosts
        # models.Host.objects.bulk_create(
        #     [models.Host(user=user_map[v["user"]], name=v["host"]) for v in vals],
        #     ignore_conflicts=True,
        # )
        #
        # # Fetch hosts
        # q = Q()
        # for v in vals:
        #     q = q | (Q(user=user_map[v["user"]]) & Q(name=v["host"]))
        # hosts = models.Host.objects.filter(q)

        # bulk create with update_conflcits
        hosts = Host.objects.bulk_create(
            [Host(user=user_map[v["user"]], name=v["host"]) for v in vals],
            update_conflicts=True,
            unique_fields=["user", "name"],
            update_fields=["user", "name"],
        )
        hosts_map = {(i.user_id, i.name): i for i in hosts}

        # Create or "get" (via update_conclits" hack) counts
        counts = models.Count.objects.bulk_create(
            [
                models.Count(
                    host=hosts_map[(user_map[v["user"]].id, v["host"])],
                    metric=v["metric"],
                    date=v["date"],
                    value=v["value"],
                    count=v["count"],
                )
                for v in vals
            ],
            update_conflicts=True,
            unique_fields=["host", "date", "metric", "value"],
            update_fields=["host", "date", "metric", "value"],
        )
