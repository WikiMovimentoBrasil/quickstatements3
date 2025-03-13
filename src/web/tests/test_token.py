from datetime import datetime
from datetime import timedelta
from datetime import UTC

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.timezone import now

from web.models import Token


class TokenTests(TestCase):
    def test_creation_from_full_token(self):
        full_token = {
            "access_token": "access_token",
            "refresh_token": "refresh_token",
            "expires_at": 1729809078,
        }
        user = User.objects.create(username="u")
        t = Token.objects.create_from_full_token(user, full_token)
        self.assertEqual(t.user.id, user.id)
        self.assertEqual(t.value, "access_token")
        self.assertEqual(t.refresh_token, "refresh_token")
        self.assertEqual(t.expires_at.year, 2024)
        self.assertEqual(t.expires_at.month, 10)
        self.assertEqual(t.expires_at.day, 24)
        self.assertEqual(t.expires_at.hour, 22)
        self.assertEqual(t.expires_at.minute, 31)
        self.assertEqual(t.expires_at.second, 18)
        self.assertEqual(t.expires_at, datetime(2024, 10, 24, 22, 31, 18, tzinfo=UTC))

    def test_creation_from_full_token_key_error(self):
        user = User.objects.create(username="u")
        with self.assertRaises(KeyError):
            full_token = {
                "access_token": "access_token",
                "expires_at": 1729809078,
            }
            Token.objects.create_from_full_token(user, full_token)
        with self.assertRaises(KeyError):
            full_token = {
                "refresh_token": "refresh_token",
                "expires_at": 1729809078,
            }
            Token.objects.create_from_full_token(user, full_token)
        with self.assertRaises(KeyError):
            full_token = {
                "access_token": "access_token",
                "refresh_token": "refresh_token",
            }
            Token.objects.create_from_full_token(user, full_token)

    def test_is_expired(self):
        user = User.objects.create(username="u1")
        token = Token.objects.create(user=user)
        self.assertFalse(token.is_expired())

        for value in (
            now() - timedelta(minutes=4),
            now(),
            now() + timedelta(minutes=2),
            now() + timedelta(minutes=4),
            now() + timedelta(minutes=4, seconds=59),
        ):
            token.expires_at = value
            token.save()
            self.assertTrue(token.is_expired())

        for value in (
            now() + timedelta(minutes=5, seconds=10),
            now() + timedelta(minutes=6),
            now() + timedelta(hours=3),
            None,
        ):
            token.expires_at = value
            token.save()
            self.assertFalse(token.is_expired())

    def test_str(self):
        user = User.objects.create(username="u1")
        token = Token.objects.create(user=user)
        self.assertEqual(str(token), f"Token for {user}: [redacted]")
        token = Token(value="x")
        self.assertEqual(str(token), "Anonymous token: [redacted]")
