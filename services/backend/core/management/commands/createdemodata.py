"""
Seed the read-only demo account behind dashboard.html?demo=1.

Idempotent: it creates the "demo" user and a "counter.dev" host once and
leaves existing counts untouched, so it is safe to run on every backend
start.
"""

import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import Count, Host

DEMO_USER = "demo"
DEMO_HOST = "counter.dev"
DEMO_PASSWORD = "demo-demo-demo"  # used only by tests; the demo account is public anyway

REFERRERS = {
    "https://google.com/": 40,
    "https://news.ycombinator.com/": 15,
    "https://github.com/": 10,
    "https://bing.com/": 8,
    "": 20,  # direct traffic
}
# The visitor counter sums the "date" category (one bucket per day).
DATE_CATEGORY = "date"
COUNTRIES = {"DE": 30, "US": 25, "FR": 10, "GB": 8, "JP": 5, "IT": 4}
BROWSERS = {"Chrome": 45, "Firefox": 15, "Safari": 10, "Edge": 5}
PLATFORMS = {"Mac OS": 25, "Windows": 25, "Linux": 8, "iOS": 10, "Android": 7}
DEVICES = {"desktop": 60, "mobile": 25}
SCREENS = {"1920x1080": 30, "1440x900": 15, "1366x768": 10, "375x667": 12}
PAGES = {"/": 45, "/pricing": 15, "/docs": 10, "/blog/hello-world": 8}
LANGS = {"en": 40, "de": 20, "fr": 8, "it": 4}
WEEKDAYS = {"Mon": 12, "Tue": 14, "Wed": 15, "Thu": 13, "Fri": 11, "Sat": 6, "Sun": 5}


def _pick_weighted(weights):
    total = sum(weights.values())
    point = random.randint(1, total)
    for item, weight in weights.items():
        point -= weight
        if point <= 0:
            return item
    return item


class Command(BaseCommand):
    help = "Seed the demo account with plausible visit data (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=60)

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.filter(username=DEMO_USER).first()
        if user is None:
            user = User.objects.create_user(username=DEMO_USER, password=DEMO_PASSWORD)
            user.is_active = True
            user.save()
        host = Host.objects.filter(user=user, name=DEMO_HOST).first()
        if host is None:
            host = Host.objects.create(user=user, name=DEMO_HOST)

        # Older seeds may predate a category; start over if "date" (which the
        # visitor counter sums) is missing.
        if Count.objects.filter(host=host).exists():
            if Count.objects.filter(host=host, category=DATE_CATEGORY).exists():
                self.stdout.write("Demo data already present, nothing to do.")
                return
            Count.objects.filter(host=host).delete()

        rng = random.Random(42)  # deterministic demo numbers
        today = date.today()
        records = []
        for day_offset in range(options["days"]):
            day = today - timedelta(days=day_offset)
            visits = rng.randint(60, 140)
            for category, weights in {
                "ref": REFERRERS,
                DATE_CATEGORY: {day.strftime("%Y-%m-%d"): visits},
                "country": COUNTRIES,
                "browser": BROWSERS,
                "platform": PLATFORMS,
                "device": DEVICES,
                "screen": SCREENS,
                "page": PAGES,
                "lang": LANGS,
                "weekday": WEEKDAYS,
            }.items():
                for item, weight in weights.items():
                    total = max(1, round(visits * weight / sum(weights.values()) * rng.uniform(0.7, 1.3)))
                    records.append(Count(host=host, date=day, category=category, item=item, total=total))
            for hour in range(24):
                hour_total = max(0, round(visits / 24 * rng.uniform(0.3, 1.8)))
                if hour_total:
                    records.append(Count(host=host, date=day, category="hour", item=f"{hour:02d}", total=hour_total))
        Count.objects.bulk_create(records, batch_size=5000)
        self.stdout.write(self.style.SUCCESS(f"Seeded demo account with {len(records)} count rows."))