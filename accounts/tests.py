import json
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

User = get_user_model()


class LoginViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )

    def test_login_success(self):
        data = {"username": "testuser", "password": "testpass123"}
        response = self.client.post("/api/accounts/login/", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "testuser")
        self.assertEqual(response.data["email"], "test@example.com")

    def test_login_invalid_credentials(self):
        data = {"username": "testuser", "password": "wrongpassword"}
        response = self.client.post("/api/accounts/login/", data)
        self.assertEqual(response.status_code, 400)

    def test_login_nonexistent_user(self):
        data = {"username": "nonexistent", "password": "testpass123"}
        response = self.client.post("/api/accounts/login/", data)
        self.assertEqual(response.status_code, 400)

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        data = {"username": "testuser", "password": "testpass123"}
        response = self.client.post("/api/accounts/login/", data)
        self.assertEqual(response.status_code, 400)


class LogoutViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_logout(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/accounts/logout/")
        self.assertEqual(response.status_code, 204)

    def test_logout_unauthenticated(self):
        response = self.client.post("/api/accounts/logout/")
        self.assertEqual(response.status_code, 401)


class MeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )

    def test_get_me(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/accounts/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "testuser")
        self.assertEqual(response.data["email"], "test@example.com")

    def test_get_me_unauthenticated(self):
        response = self.client.get("/api/accounts/me/")
        self.assertEqual(response.status_code, 401)

    def test_delete_me(self):
        self.client.force_authenticate(user=self.user)
        user_id = self.user.id
        response = self.client.delete("/api/accounts/me/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_delete_me_unauthenticated(self):
        response = self.client.delete("/api/accounts/me/")
        self.assertEqual(response.status_code, 401)


class PasswordChangeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="oldpass123")

    def test_change_password_success(self):
        self.client.force_authenticate(user=self.user)
        data = {"old_password": "oldpass123", "new_password": "NewValidPass123!"}
        response = self.client.post("/api/accounts/password/change/", data)
        self.assertEqual(response.status_code, 204)

        # Verify password changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewValidPass123!"))
        self.assertFalse(self.user.check_password("oldpass123"))

    def test_change_password_wrong_old_password(self):
        self.client.force_authenticate(user=self.user)
        data = {"old_password": "wrongpass", "new_password": "NewValidPass123!"}
        response = self.client.post("/api/accounts/password/change/", data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("old_password", response.data)

    def test_change_password_weak_new_password(self):
        self.client.force_authenticate(user=self.user)
        data = {"old_password": "oldpass123", "new_password": "123"}
        response = self.client.post("/api/accounts/password/change/", data)
        self.assertEqual(response.status_code, 400)

    def test_change_password_unauthenticated(self):
        data = {"old_password": "oldpass123", "new_password": "NewValidPass123!"}
        response = self.client.post("/api/accounts/password/change/", data)
        self.assertEqual(response.status_code, 401)


class EmailChangeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="old@example.com"
        )

    def test_change_email(self):
        self.client.force_authenticate(user=self.user)
        data = {"email": "new@example.com"}
        response = self.client.post("/api/accounts/email/change/", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "new@example.com")

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")

    def test_clear_email(self):
        self.client.force_authenticate(user=self.user)
        data = {"email": ""}
        response = self.client.post("/api/accounts/email/change/", data)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["email"])

    def test_change_email_unauthenticated(self):
        data = {"email": "new@example.com"}
        response = self.client.post("/api/accounts/email/change/", data)
        self.assertEqual(response.status_code, 401)

    def test_change_email_invalid_format(self):
        self.client.force_authenticate(user=self.user)
        data = {"email": "not-an-email"}
        response = self.client.post("/api/accounts/email/change/", data)
        self.assertEqual(response.status_code, 400)


class TimezoneViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_change_timezone(self):
        self.client.force_authenticate(user=self.user)
        data = {"timezone": -5}
        response = self.client.post("/api/accounts/timezone/", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["timezone"], -5)

        self.user.refresh_from_db()
        self.assertEqual(self.user.timezone, -5)

    def test_change_timezone_positive(self):
        self.client.force_authenticate(user=self.user)
        data = {"timezone": 9}
        response = self.client.post("/api/accounts/timezone/", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["timezone"], 9)

    def test_change_timezone_zero(self):
        self.client.force_authenticate(user=self.user)
        data = {"timezone": 0}
        response = self.client.post("/api/accounts/timezone/", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["timezone"], 0)

    def test_change_timezone_unauthenticated(self):
        data = {"timezone": -5}
        response = self.client.post("/api/accounts/timezone/", data)
        self.assertEqual(response.status_code, 401)


class PrefsViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_change_prefs(self):
        self.client.force_authenticate(user=self.user)
        data = {"prefs": {"theme": "dark", "language": "en"}}
        response = self.client.post("/api/accounts/prefs/", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["prefs"], {"theme": "dark", "language": "en"})

        self.user.refresh_from_db()
        self.assertEqual(self.user.prefs, {"theme": "dark", "language": "en"})

    def test_change_prefs_empty(self):
        self.client.force_authenticate(user=self.user)
        data = {"prefs": {}}
        response = self.client.post("/api/accounts/prefs/", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["prefs"], {})

    def test_change_prefs_overwrites(self):
        self.user.prefs = {"theme": "light"}
        self.user.save()

        self.client.force_authenticate(user=self.user)
        data = {"prefs": {"theme": "dark", "language": "fr"}}
        response = self.client.post("/api/accounts/prefs/", data)
        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.assertEqual(self.user.prefs["theme"], "dark")
        self.assertEqual(self.user.prefs["language"], "fr")

    def test_change_prefs_unauthenticated(self):
        data = {"prefs": {"theme": "dark"}}
        response = self.client.post("/api/accounts/prefs/", data)
        self.assertEqual(response.status_code, 401)


@override_settings(
    PASSWORD_RESET_URL_BASE="http://example.com/reset",
    DEFAULT_FROM_EMAIL="noreply@example.com",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class PasswordResetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )

    def test_password_reset_request(self):
        from django.core import mail

        data = {"email": "test@example.com"}
        response = self.client.post("/api/accounts/password/reset/", data)
        self.assertEqual(response.status_code, 204)

        # Verify email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Reset", mail.outbox[0].subject)
        self.assertIn("Reset", mail.outbox[0].body)

    def test_password_reset_request_case_insensitive(self):
        from django.core import mail

        data = {"email": "TEST@EXAMPLE.COM"}
        response = self.client.post("/api/accounts/password/reset/", data)
        self.assertEqual(response.status_code, 204)

        # Email should still be sent (case-insensitive lookup)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_request_unknown_email(self):
        from django.core import mail

        data = {"email": "unknown@example.com"}
        response = self.client.post("/api/accounts/password/reset/", data)
        self.assertEqual(response.status_code, 204)  # Don't leak info

        # No email sent
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_confirm(self):
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        data = {"uid": uid, "token": token, "new_password": "NewValidPass123!"}
        response = self.client.post("/api/accounts/password/reset/confirm/", data)
        self.assertEqual(response.status_code, 204)

        # Verify password changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewValidPass123!"))

    def test_password_reset_confirm_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        data = {
            "uid": uid,
            "token": "invalid-token",
            "new_password": "NewValidPass123!",
        }
        response = self.client.post("/api/accounts/password/reset/confirm/", data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.data)

    def test_password_reset_confirm_invalid_uid(self):
        token = default_token_generator.make_token(self.user)

        data = {
            "uid": "invalid-uid",
            "token": token,
            "new_password": "NewValidPass123!",
        }
        response = self.client.post("/api/accounts/password/reset/confirm/", data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.data)

    def test_password_reset_confirm_nonexistent_user(self):
        token = default_token_generator.make_token(self.user)
        # Use a different user's uid format
        other_user = User.objects.create_user(username="other", password="pass")
        uid = urlsafe_base64_encode(force_bytes("nonexistent-id"))

        data = {"uid": uid, "token": token, "new_password": "NewValidPass123!"}
        response = self.client.post("/api/accounts/password/reset/confirm/", data)
        self.assertEqual(response.status_code, 400)

    def test_password_reset_confirm_weak_password(self):
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        data = {"uid": uid, "token": token, "new_password": "123"}
        response = self.client.post("/api/accounts/password/reset/confirm/", data)
        self.assertEqual(response.status_code, 400)


class UserSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )

    def test_user_serializer_data(self):
        from .serializers import UserSerializer

        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertEqual(data["username"], "testuser")
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["timezone"], 0)
        self.assertEqual(data["prefs"], {})
        self.assertIn("id", data)

    def test_user_serializer_id_readonly(self):
        from .serializers import UserSerializer

        serializer = UserSerializer(
            data={
                "id": "different-id",
                "username": "testuser",
                "email": "test@example.com",
            }
        )
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()
        # ID should not be changed
        self.assertNotEqual(instance.id, "different-id")
