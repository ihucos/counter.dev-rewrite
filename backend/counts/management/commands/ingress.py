from django.core.management.base import BaseCommand, CommandError
from counts.models import Count, Host
from time import sleep
from django.core.cache import cache

# TODO: All keys can be hashes after the big app rewrite
ZET_KEYS = ["lang", "ref", "loc", "page"]


class Command(BaseCommand):
    help = "Ingress data into the Counts app, creating or updating Count records."

    def add_arguments(self, parser):
        parser.add_argument("--forever", action="store_true")

    def handle(self, *args, **options):
        forever = options["forever"]
        assert forever, "only --forever is supported"

        # Get the raw Redis client from Django's cache backend
        # cache._cache is a RedisCacheClient, which has get_client() returning redis.Redis
        redis = cache._cache.get_client()

        while True:
            # SCAN for keys matching the specific pattern
            cursor, keys = redis.scan(
                cursor=cursor, match="v:*,*,*,*-*-*", count=iteration_chunk_size
            )

            # Transaction??
            pipeline = redis_conn.pipeline(transaction=False)

            for key in keys:
                try:
                    _, user, host, metric, date = key.split(":")
                except ValueError:
                    continue  # Skip malformed keys safely

                if metric in ZET_KEYS:
                    pipeline.hgetall(key)
                else:
                    pipeline.zrange(key, 0, -1, withscores=True)

            redis_response = pipeline.execute()
            print(redis_response)
            print(keys)

            # result = redis.echo("hello from redis via django cache")
            # print(f"Redis echo: {result}")
            #
            sleep(3)
