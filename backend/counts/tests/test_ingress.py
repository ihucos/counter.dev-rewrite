from django.core.cache import cache
from django.core.management import call_command
import pytest


class TestIngressView:
    def test_does_not_die_badly(self):
        call_command("ingress", forever=True)
