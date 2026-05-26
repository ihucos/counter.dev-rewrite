from django.core.management.base import BaseCommand, CommandError
from counts.models import Count, Host
from time import sleep
from django.core.cache import cache
from django.db.models.query_utils import Q

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

    def add_arguments(self, parser):
        parser.add_argument("--forever", action="store_true")

    def _parse_key(self, key):
        if not key.startswith("v:"):
            raise ValueError("bad key")
        key = key[len(b"v:") :]
        try:
            host, user, metric, date = key.split(",")
        except ValueError:
            raise ValueError("bad key")
        # urldecode!!
        return host, user, metric, date

    def _pop_keys(self, keys) -> dict:
        pipeline = self.redis.pipeline()
        for key in keys:
            pipeline.hgetall(key)
        for key in keys:
            pipeline.delete(key)
        return dict(zip(keys, pipeline.execute()))

    def _handle_keys_batch(self, keys):
        # This can fail
        keys = [i.decode() for i in keys]

        keys_with_vals = self._pop_keys(keys)
        parsed_keys_with_vals = {
            self._parse_key(key): val for (key, val) in keys_with_vals.items()
        }

        vals = []
        for (host, user, metric, date), hvals in parsed_keys_with_vals.items():
            for value, count in hvals.items():
                vals.append(
                    {
                        "host": host.decode() if isinstance(host, bytes) else host,
                        "user": user.decode() if isinstance(user, bytes) else user,
                        "metric": metric.decode()
                        if isinstance(metric, bytes)
                        else metric,
                        "date": date.decode() if isinstance(date, bytes) else date,
                        "value": value.decode() if isinstance(value, bytes) else value,
                        "count": int(count),
                    }
                )

        self._save_values_batch(vals)

    def handle(self, *args, **options):
        forever = options["forever"]
        cursor = 0
        while True:
            cursor, keys = self.redis.scan(
                cursor=cursor, match="v:*,*,*,*-*-*", count=10
            )
            self._handle_keys_batch(keys)

            if not forever:
                break

    def _save_values_batch(self, vals: list[dict]):
        """
        Increment values batch into postgres
        """
        vals = list(vals)

        # Map users specified in redis to database users
        user_map = {
            **User.objects.in_bulk([i["user"] for i in vals], field_name="id"),
            **User.objects.in_bulk([i["user"] for i in vals], field_name="username"),
        }

        # Remove users not in database
        vals = [val for val in vals if val["user"] in user_map]

        if not vals:
            return

        # Create or "get" (via update_conflicts hack) hosts
        hosts = Host.objects.bulk_create(
            [
                models.Host(**i)
                for i in unique_dicts(
                    [
                        {"user_id": user_map[v["user"]].id, "name": v["host"]}
                        for v in vals
                    ]
                )
            ],
            update_conflicts=True,
            unique_fields=["user", "name"],
            update_fields=["user", "name"],
        )
        # Frozendict!
        hosts_map = {(i.user_id, i.name): i for i in hosts}

        # First pass: create any new count records with count=0.
        # Existing records are ignored (ignore_conflicts=True).
        # This ensures every unique (host, date, metric, value) combo exists.
        models.Count.objects.bulk_create(
            [
                models.Count(
                    host=hosts_map[(user_map[v["user"]].id, v["host"])],
                    metric=v["metric"],
                    date=v["date"],
                    value=v["value"],
                    count=0,
                )
                for v in vals
            ],
            ignore_conflicts=True,
        )

        # Second pass: use a single batched UPDATE via raw SQL for efficiency.
        # We build a VALUES table and join to update counts in one query.
        from django.db import connection

        records = []
        for v in vals:
            host = hosts_map[(user_map[v["user"]].id, v["host"])]
            records.extend((host.id, v["metric"], v["date"], v["value"], v["count"]))

        # Use a single UPDATE ... FROM (VALUES ...) query to batch increment all counts

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE {table}
                SET count = count + v.incr
                FROM (VALUES {value_expressions}) AS v(host_id, metric, date, value, incr)
                WHERE {table}.host_id = v.host_id
                  AND {table}.metric = v.metric
                  AND {table}.date = v.date
                  AND {table}.value = v.value
                """.format(
                    table=Count._meta.db_table,
                    value_expressions=", ".join(
                        "(%s, %s, %s::date, %s, %s)" for _ in vals
                    ),
                ),
                records,
            )
