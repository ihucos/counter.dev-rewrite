from time import sleep
from urllib.parse import unquote

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import connection

from accounts.models import User
from counts.models import Count, Host


class BadKeyError(ValueError):
    """Raised when a Redis key does not match the expected ingestion schema."""

    pass


class Command(BaseCommand):
    help = "Ingress data into the Counts app, creating or updating Count records."

    def __init__(self):
        self.redis = cache._cache.get_client()

    def add_arguments(self, parser):
        parser.add_argument("--forever", action="store_true")
        parser.add_argument("--batch-size", type=int, default=1000)
        parser.add_argument(
            "--sleep",
            type=float,
            default=0,
            help="Sleep duration in seconds between iterations when running with --forever (default: 0)",
        )

    def handle(self, *args, **options):
        forever = options["forever"]
        sleep_secs = options["sleep"]
        cursor = 0
        while True:
            cursor, keys = self.redis.scan(
                cursor=cursor, match="v:*,*,*,*-*-*", count=options["batch_size"]
            )
            self._handle_keys_batch(keys)

            if cursor == 0 and not forever:
                break

            if cursor == 0 and forever and sleep_secs > 0:
                sleep(sleep_secs)

    def _parse_key(self, key):
        try:
            key = key.decode()
        except UnicodeDecodeError:
            raise BadKeyError()
        if not key.startswith("v:"):
            raise BadKeyError()
        key = key[len("v:") :]
        try:
            host, user, metric, date = key.split(",")
        except ValueError:
            raise BadKeyError()
        return unquote(host), unquote(user), unquote(metric), unquote(date)

    def _pop_keys(self, keys) -> dict:
        pipeline = self.redis.pipeline(transaction=True)
        for key in keys:
            pipeline.hgetall(key)
        for key in keys:
            pipeline.delete(key)
        return dict(zip(keys, pipeline.execute()))

    def _handle_keys_batch(self, keys):
        # This can fail

        records = []
        for key, hval in self._pop_keys(keys).items():
            try:
                host, user, metric, date = self._parse_key(key)
            except BadKeyError:
                print(f"Bad key: {key}")
                continue
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
        Increment or create the records into postgres
        """
        records = list(records)

        # Map users specified in redis to database users
        user_identifiers = {r["user"] for r in records}
        user_map = {
            **User.objects.in_bulk(user_identifiers, field_name="id"),
            **User.objects.in_bulk(user_identifiers, field_name="username"),
        }

        valid_records = []
        for r in records:
            user_obj = user_map.get(r["user"])
            if user_obj:
                r["user_id"] = user_obj.id
                valid_records.append(r)
        del records

        if not valid_records:
            return

        hosts = Host.objects.bulk_create(
            self._get_unique_hosts(valid_records),
            update_conflicts=True,
            unique_fields=["user_id", "name"],
            update_fields=["name"],
        )

        host_map = {(h.user_id, h.name): h.id for h in hosts}
        for r in valid_records:
            r["host_id"] = host_map.get((r["user_id"], r["host"]))

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
                        "(%s, %s, %s::date, %s, %s)" for _ in valid_records
                    ),
                ),
                [
                    val
                    for r in valid_records
                    for val in (
                        r["host_id"],
                        r["metric"],
                        r["date"],
                        r["value"],
                        r["count"],
                    )
                ],
            )

    def _get_unique_hosts(self, records: list[dict]) -> list[Host]:
        """Extracts unique host-user combinations from records."""
        seen = set()
        unique = []
        for r in records:
            pair = (r["user_id"], r["host"])
            if pair not in seen:
                seen.add(pair)
                unique.append(Host(user_id=r["user_id"], name=r["host"]))
        return unique
