from django.core.management.base import BaseCommand, CommandError
from counts.models import Count, Host
from time import sleep
from django.core.cache import cache
from django.db.models.query_utils import Q
from django.db import connection

from ... import models
from accounts.models import User


def unique_dicts(lst: list[dict]) -> list[dict]:
    unique_list = set()
    for dic in lst:
        unique_list.add(tuple(sorted(dic.items())))
    return [dict(i) for i in unique_list]


class Command(BaseCommand):
    help = "Ingress data into the Counts app, creating or updating Count records."

    def __init__(self):
        self.redis = cache._cache.get_client()
        self.redis.connection_pool.connection_kwargs["decode_responses"] = True

    def add_arguments(self, parser):
        parser.add_argument("--forever", action="store_true")
        parser.add_argument("--batch", type=int, default=1000)

    def handle(self, *args, **options):
        forever = options["forever"]
        cursor = 0
        while True:
            cursor, keys = self.redis.scan(
                cursor=cursor, match="v:*,*,*,*-*-*", count=options["batch"]
            )
            self._handle_keys_batch(keys)

            if cursor == 0 and not forever:
                break

    def _parse_key(self, key):
        if not key.startswith("v:"):
            raise ValueError("bad key")
        key = key[len("v:") :]
        try:
            host, user, metric, date = key.split(",")
        except ValueError:
            raise ValueError("bad key")
        # urldecode!!
        return host, user, metric, date

    def _pop_keys(self, keys) -> dict:
        pipeline = self.redis.pipeline(transaction=True)
        for key in keys:
            pipeline.hgetall(key)
        for key in keys:
            pipeline.delete(key)
        return dict(zip(keys, pipeline.execute()))

    def _handle_keys_batch(self, keys):
        # This can fail
        keys = [i.decode() for i in keys]

        records = []
        for key, hval in self._pop_keys(keys).items():
            host, user, metric, date = self._parse_key(key)
            for value, count in hval.items():
                records.append(
                    {
                        "host": host,
                        "user": user,
                        "metric": metric,
                        "date": date,
                        "value": value.decode(),
                        "count": int(count),
                    }
                )
        self._save_values_batch(records)

    def _save_values_batch(self, records: list[dict]):
        """
        Increment values batch into postgres
        """
        records = list(records)

        # Map users specified in redis to database users
        user_map = {
            **User.objects.in_bulk([i["user"] for i in records], field_name="id"),
            **User.objects.in_bulk([i["user"] for i in records], field_name="username"),
        }

        # Remove users not in database
        records = [r for r in records if r["user"] in user_map]

        if not records:
            return

        # Create or "get" (via update_conflicts hack) hosts
        hosts = Host.objects.bulk_create(
            [
                models.Host(**i)
                for i in unique_dicts(
                    [
                        {"user_id": user_map[r["user"]].id, "name": r["host"]}
                        for r in records
                    ]
                )
            ],
            update_conflicts=True,
            unique_fields=["user_id", "name"],
            update_fields=["name"],
        )
        # Frozendict!
        hosts_map = {(i.user_id, i.name): i for i in hosts}
        print(hosts)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO {table} (host_id, metric, date, value, count)
                VALUES {value_expressions}
                ON CONFLICT (host_id, metric, date, value) 
                DO UPDATE SET count = {table}.count + EXCLUDED.count
                """.format(
                    table=Count._meta.db_table,
                    value_expressions=", ".join(
                        "(%s, %s, %s::date, %s, %s)" for _ in records
                    ),
                ),
                [
                    val
                    for r in records
                    for val in (
                        hosts_map[(user_map[r["user"]].id, r["host"])].id,
                        r["metric"],
                        r["date"],
                        r["value"],
                        r["count"],
                    )
                ],
            )
