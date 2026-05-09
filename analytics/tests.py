from datetime import date, datetime, timezone, timedelta
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from .models import Site, Count
from .permissions import IngressClient

User = get_user_model()


class SiteModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_create_site(self):
        site = Site.objects.create(user=self.user, domain="example.com")
        self.assertEqual(site.domain, "example.com")
        self.assertEqual(site.user, self.user)
        self.assertEqual(site.allowed_domains, [])
        self.assertFalse(site.filter_allowed_domains)

    def test_site_str(self):
        site = Site.objects.create(user=self.user, domain="example.com")
        self.assertEqual(str(site), f"example.com ({self.user.id})")

    def test_unique_together_user_domain(self):
        Site.objects.create(user=self.user, domain="example.com")
        with self.assertRaises(Exception):  # IntegrityError
            Site.objects.create(user=self.user, domain="example.com")

    def test_site_with_allowed_domains(self):
        site = Site.objects.create(
            user=self.user,
            domain="example.com",
            allowed_domains=["*.example.com", "www.example.com"],
            filter_allowed_domains=True
        )
        self.assertEqual(len(site.allowed_domains), 2)
        self.assertTrue(site.filter_allowed_domains)

    def test_different_users_can_have_same_domain(self):
        other_user = User.objects.create_user(username="otheruser", password="testpass123")
        site1 = Site.objects.create(user=self.user, domain="example.com")
        site2 = Site.objects.create(user=other_user, domain="example.com")
        
        self.assertNotEqual(site1.user_id, site2.user_id)
        self.assertEqual(site1.domain, site2.domain)


class CountModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.site = Site.objects.create(user=self.user, domain="example.com")

    def test_create_count(self):
        count = Count.objects.create(
            site=self.site,
            date=date(2024, 1, 1),
            metric="pageviews",
            value="/home",
            count=100
        )
        self.assertEqual(count.site, self.site)
        self.assertEqual(count.metric, "pageviews")
        self.assertEqual(count.value, "/home")
        self.assertEqual(count.count, 100)

    def test_count_str(self):
        count = Count.objects.create(
            site=self.site,
            date=date(2024, 1, 1),
            metric="pageviews",
            value="/home",
            count=100
        )
        self.assertIn("pageviews=/home", str(count))
        self.assertIn("100", str(count))

    def test_unique_together_constraint(self):
        Count.objects.create(
            site=self.site,
            date=date(2024, 1, 1),
            metric="pageviews",
            value="/home",
            count=100
        )
        with self.assertRaises(Exception):  # IntegrityError
            Count.objects.create(
                site=self.site,
                date=date(2024, 1, 1),
                metric="pageviews",
                value="/home",
                count=50
            )

    def test_different_values_same_metric(self):
        count1 = Count.objects.create(
            site=self.site,
            date=date(2024, 1, 1),
            metric="pageviews",
            value="/home",
            count=100
        )
        count2 = Count.objects.create(
            site=self.site,
            date=date(2024, 1, 1),
            metric="pageviews",
            value="/about",
            count=50
        )
        self.assertEqual(count1.metric, count2.metric)
        self.assertNotEqual(count1.value, count2.value)


class SiteViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.other_user = User.objects.create_user(username="otheruser", password="testpass123")

    def test_list_sites(self):
        Site.objects.create(user=self.user, domain="example.com")
        Site.objects.create(user=self.user, domain="test.com")
        Site.objects.create(user=self.other_user, domain="other.com")
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/analytics/sites/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        domains = [s["domain"] for s in response.data]
        self.assertIn("example.com", domains)
        self.assertIn("test.com", domains)
        self.assertNotIn("other.com", domains)

    def test_list_sites_ordered_by_domain(self):
        Site.objects.create(user=self.user, domain="zebra.com")
        Site.objects.create(user=self.user, domain="apple.com")
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/analytics/sites/")
        self.assertEqual(response.status_code, 200)
        domains = [s["domain"] for s in response.data]
        self.assertEqual(domains, ["apple.com", "zebra.com"])

    def test_create_site(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "domain": "newsite.com",
            "allowed_domains": ["*.newsite.com"],
            "filter_allowed_domains": True
        }
        response = self.client.post("/api/analytics/sites/", data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["domain"], "newsite.com")
        self.assertEqual(response.data["allowed_domains"], ["*.newsite.com"])
        
        site = Site.objects.get(domain="newsite.com")
        self.assertEqual(site.user, self.user)

    def test_retrieve_site(self):
        site = Site.objects.create(user=self.user, domain="example.com")
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/analytics/sites/{site.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["domain"], "example.com")

    def test_retrieve_other_user_site_forbidden(self):
        site = Site.objects.create(user=self.other_user, domain="other.com")
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/analytics/sites/{site.id}/")
        self.assertEqual(response.status_code, 404)

    def test_update_site(self):
        site = Site.objects.create(user=self.user, domain="example.com")
        
        self.client.force_authenticate(user=self.user)
        data = {"domain": "updated.com"}
        response = self.client.patch(f"/api/analytics/sites/{site.id}/", data)
        self.assertEqual(response.status_code, 200)
        
        site.refresh_from_db()
        self.assertEqual(site.domain, "updated.com")

    def test_delete_site(self):
        site = Site.objects.create(user=self.user, domain="example.com")
        
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/analytics/sites/{site.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Site.objects.filter(id=site.id).exists())

    def test_delete_other_user_site_forbidden(self):
        site = Site.objects.create(user=self.other_user, domain="other.com")
        
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/analytics/sites/{site.id}/")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Site.objects.filter(id=site.id).exists())

    def test_unauthenticated_access(self):
        response = self.client.get("/api/analytics/sites/")
        self.assertEqual(response.status_code, 401)


@override_settings(INGRESS_SECRET_KEY="test-secret-key")
class IngressViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.user.timezone = 0
        self.user.save()

    def test_ingress_authentication_with_header(self):
        data = []
        response = self.client.post(
            "/api/analytics/ingress/",
            data,
            format="json",
            HTTP_X_INGRESS_SECRET="test-secret-key"
        )
        self.assertEqual(response.status_code, 202)

    def test_ingress_authentication_with_bearer(self):
        data = []
        response = self.client.post(
            "/api/analytics/ingress/",
            data,
            format="json",
            HTTP_AUTHORIZATION="Bearer test-secret-key"
        )
        self.assertEqual(response.status_code, 202)

    def test_ingress_authentication_invalid_secret(self):
        data = []
        response = self.client.post(
            "/api/analytics/ingress/",
            data,
            format="json",
            HTTP_X_INGRESS_SECRET="wrong-secret"
        )
        self.assertEqual(response.status_code, 403)

    def test_ingress_authentication_missing_secret(self):
        data = []
        response = self.client.post(
            "/api/analytics/ingress/",
            data,
            format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_ingress_creates_site_and_count(self):
        data = [
            {
                "user": self.user.id,
                "site": "example.com",
                "metric": "pageviews",
                "value": "/home",
                "incr": "1"
            }
        ]
        response = self.client.post(
            "/api/analytics/ingress/",
            data,
            format="json",
            HTTP_X_INGRESS_SECRET="test-secret-key"
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["accepted"], 1)
        
        # Verify site created
        site = Site.objects.get(user=self.user, domain="example.com")
        self.assertIsNotNone(site)
        
        # Verify count created
        count = Count.objects.get(site=site, metric="pageviews", value="/home")
        self.assertEqual(count.count, 1)

    def test_ingress_aggregates_multiple_entries(self):
        data = [
            {
                "user": self.user.id,
                "site": "example.com",
                "metric": "pageviews",
                "value": "/home",
                "incr": "5"
            },
            {
                "user": self.user.id,
                "site": "example.com",
                "metric": "pageviews",
                "value": "/home",
                "incr": "3"
            }
        ]
        response = self.client.post(
            "/api/analytics/ingress/",
            data,
            format="json",
            HTTP_X_INGRESS_SECRET="test-secret-key"
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["accepted"], 1)
        
        site = Site.objects.get(user=self.user, domain="example.com")
        count = Count.objects.get(site=site, metric="pageviews", value="/home")
        self.assertEqual(count.count, 8)

    def test_ingress_updates_existing_count(self):
        site = Site.objects.create(user=self.user, domain="example.com")
        Count.objects.create(
            site=site,
            date=date.today(),
            metric="pageviews",
            value="/home",
            count=10
        )
        
        data = [
            {
                "user": self.user.id,
                "site": "example.com",
                "metric": "pageviews",
                "value": "/home",
                "incr": "5"
            }
        ]
        response = self.client.post(
            "/api/analytics/ingress/",
            data,
            format="json",
            HTTP_X_INGRESS_SECRET="test-secret-key"
        )
        self.assertEqual(response.status_code, 202)
        
        count = Count.objects.get(site=site, metric="pageviews", value="/home")
        self.assertEqual(count.count, 15)

    def test_ingress_skips_unknown_user(self):
        data = [
            {
                "user": "unknown-user-id",
                "site": "example.com",
                "metric": "pageviews",
                "value": "/home",
                "incr": "1"
            }
        ]
        response = self.client.post(
            "/api/analytics/ingress/",
            data,
            format="json",
            HTTP_X_INGRESS_SECRET="test-secret-key"
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["accepted"], 0)

    def test_ingress_multiple_metrics(self):
        data = [
            {
                "user": self.user.id,
                "site": "example.com",
                "metric": "pageviews",
                "value": "/home",
                "incr": "1"
            },
            {
                "user": self.user.id,
                "site": "example.com",
                "metric": "referrer",
                "value": "google.com",
                "incr": "1"
            }
        ]
        response = self.client.post(
            "/api/analytics/ingress/",
            data,
            format="json",
            HTTP_X_INGRESS_SECRET="test-secret-key"
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["accepted"], 2)
        
        site = Site.objects.get(user=self.user, domain="example.com")
        self.assertEqual(Count.objects.filter(site=site).count(), 2)

    def test_ingress_with_timezone_offset(self):
        # User in UTC-5
        self.user.timezone = -5
        self.user.save()
        
        data = [
            {
                "user": self.user.id,
                "site": "example.com",
                "metric": "pageviews",
                "value": "/home",
                "incr": "1"
            }
        ]
        response = self.client.post(
            "/api/analytics/ingress/",
            data,
            format="json",
            HTTP_X_INGRESS_SECRET="test-secret-key"
        )
        self.assertEqual(response.status_code, 202)
        
        site = Site.objects.get(user=self.user, domain="example.com")
        count = Count.objects.get(site=site)
        
        # Verify date is in user's timezone
        tz = timezone(timedelta(hours=-5))
        expected_date = datetime.now(tz).date()
        self.assertEqual(count.date, expected_date)

    def test_ingress_empty_batch(self):
        data = []
        response = self.client.post(
            "/api/analytics/ingress/",
            data,
            format="json",
            HTTP_X_INGRESS_SECRET="test-secret-key"
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["accepted"], 0)

    def test_ingress_multiple_users(self):
        other_user = User.objects.create_user(username="otheruser", password="testpass123")
        other_user.timezone = 0
        other_user.save()
        
        data = [
            {
                "user": self.user.id,
                "site": "example.com",
                "metric": "pageviews",
                "value": "/home",
                "incr": "1"
            },
            {
                "user": other_user.id,
                "site": "example.com",
                "metric": "pageviews",
                "value": "/home",
                "incr": "1"
            }
        ]
        response = self.client.post(
            "/api/analytics/ingress/",
            data,
            format="json",
            HTTP_X_INGRESS_SECRET="test-secret-key"
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["accepted"], 2)
        
        # Verify separate sites created
        self.assertEqual(Site.objects.filter(domain="example.com").count(), 2)

    def test_ingress_client_properties(self):
        client = IngressClient()
        self.assertTrue(client.is_authenticated)
        self.assertTrue(client.is_active)
        self.assertFalse(client.is_anonymous)
        self.assertEqual(str(client), "ingress")


class QueryViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.other_user = User.objects.create_user(username="otheruser", password="testpass123")
        self.site = Site.objects.create(user=self.user, domain="example.com")

    def test_query_basic(self):
        Count.objects.create(
            site=self.site,
            date=date(2024, 1, 1),
            metric="pageviews",
            value="/home",
            count=100
        )
        Count.objects.create(
            site=self.site,
            date=date(2024, 1, 2),
            metric="pageviews",
            value="/home",
            count=50
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/analytics/query/?site={self.site.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pageviews"]["/home"], 150)

    def test_query_with_start_date(self):
        Count.objects.create(
            site=self.site,
            date=date(2024, 1, 1),
            metric="pageviews",
            value="/home",
            count=100
        )
        Count.objects.create(
            site=self.site,
            date=date(2024, 1, 5),
            metric="pageviews",
            value="/home",
            count=50
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/analytics/query/?site={self.site.id}&start_date=2024-01-05"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pageviews"]["/home"], 50)

    def test_query_with_end_date(self):
        Count.objects.create(
            site=self.site,
            date=date(2024, 1, 1),
            metric="pageviews",
            value="/home",
            count=100
        )
        Count.objects.create(
            site=self.site,
            date=date(2024, 1, 5),
            metric="pageviews",
            value="/home",
            count=50
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/analytics/query/?site={self.site.id}&end_date=2024-01-01"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pageviews"]["/home"], 100)

    def test_query_with_date_range(self):
        Count.objects.create(
            site=self.site,
            date=date(2024, 1, 1),
            metric="pageviews",
            value="/home",
            count=100
        )
        Count.objects.create(
            site=self.site,
            date=date(2024, 1, 5),
            metric="pageviews",
            value="/home",
            count=50
        )
        Count.objects.create(
            site=self.site,
            date=date(2024, 1, 10),
            metric="pageviews",
            value="/home",
            count=25
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/analytics/query/?site={self.site.id}&start_date=2024-01-01&end_date=2024-01-05"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pageviews"]["/home"], 150)

    def test_query_multiple_metrics(self):
        Count.objects.create(
            site=self.site,
            date=date(2024, 1, 1),
            metric="pageviews",
            value="/home",
            count=100
        )
        Count.objects.create(
            site=self.site,
            date=date(2024, 1, 1),
            metric="referrer",
            value="google.com",
            count=50
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/analytics/query/?site={self.site.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pageviews"]["/home"], 100)
        self.assertEqual(response.data["referrer"]["google.com"], 50)

    def test_query_multiple_values_per_metric(self):
        Count.objects.create(
            site=self.site,
            date=date(2024, 1, 1),
            metric="pageviews",
            value="/home",
            count=100
        )
        Count.objects.create(
            site=self.site,
            date=date(2024, 1, 1),
            metric="pageviews",
            value="/about",
            count=50
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/analytics/query/?site={self.site.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pageviews"]["/home"], 100)
        self.assertEqual(response.data["pageviews"]["/about"], 50)

    def test_query_missing_site_parameter(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/analytics/query/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("site", response.data["detail"])

    def test_query_nonexistent_site(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/analytics/query/?site=99999")
        self.assertEqual(response.status_code, 404)

    def test_query_other_user_site_forbidden(self):
        other_site = Site.objects.create(user=self.other_user, domain="other.com")
        Count.objects.create(
            site=other_site,
            date=date(2024, 1, 1),
            metric="pageviews",
            value="/home",
            count=100
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/analytics/query/?site={other_site.id}")
        self.assertEqual(response.status_code, 404)

    def test_query_unauthenticated(self):
        response = self.client.get(f"/api/analytics/query/?site={self.site.id}")
        self.assertEqual(response.status_code, 401)

    def test_query_empty_result(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/analytics/query/?site={self.site.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {})
