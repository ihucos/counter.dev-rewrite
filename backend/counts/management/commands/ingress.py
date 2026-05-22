from django.core.management.base import BaseCommand, CommandError
from counts.models import Count, Host
from time import sleep
from django.core.cache import cache


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
        result = redis.echo("hello from redis via django cache")
        print(f"Redis echo: {result}")

        while True:
            sleep(3)
