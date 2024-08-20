import os
import requests_mock

from django.test import TestCase as DjangoTestCase
from django.urls import reverse
from django.contrib import auth
from django.contrib.auth.models import User

from ..models import Token


class TestCase(DjangoTestCase):
    """Custom TestCase class with useful methods"""

    URL_NAME = "/"

    # ----------------
    # Assertion methods
    # -----------------

    def assert200(self, response):
        """Asserts the response status code is 200"""
        self.assertStatus(response, 200)

    def assertStatus(self, response, status):
        """Asserts the response status code"""
        self.assertEqual(response.status_code, status)

    def assertRedirect(self, response):
        """Asserts the response is a redirect response"""
        self.assertEqual(response.status_code, 302)

    def assertRedirectToPath(self, response, path):
        """Asserts the response is a redirect to the specificed path"""
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], path)

    def assertRedirectToUrlName(self, response, url_name):
        """Asserts the response is a redirect to the specificed URL"""
        self.assertRedirectToPath(response, reverse(url_name))

    def assertUrlInRes(self, url_name, response):
        """Checks if the URL is contained in the response"""
        self.assertInRes(reverse(url_name), response)

    def assertInRes(self, substring, response):
        """Checks if a substring is contained in response content"""
        self.assertIn(substring.lower(), str(response.content).lower().strip())

    def assertIsAuthenticated(self):
        self.assertTrue(self.get_user().is_authenticated)

    def assertIsNotAuthenticated(self):
        self.assertFalse(self.get_user().is_authenticated)

    # ---------------
    # Utility methods
    # ---------------

    def get(self):
        """Make a test GET request with the test client"""
        return self.client.get(reverse(self.URL_NAME))

    def post(self, data=None):
        """Make a test POST request with the test client"""
        return self.client.post(reverse(self.URL_NAME), data=data)

    def login_john(self):
        """Login with a user with 'john' username"""
        user = User.objects.create_user(username="john")
        client = self.client
        client.force_login(user)

    def get_user(self):
        return auth.get_user(self.client)


class Profile(TestCase):
    URL_NAME = "profile"

    def test_not_logged_in(self):
        res = self.get()
        self.assert200(res)
        self.assertInRes("not logged in", res)
        self.assertUrlInRes("login", res)

    def test_logged_in_when_username_in_session(self):
        self.login_john()
        res = self.get()
        self.assert200(res)
        self.assertInRes("John", res)
        self.assertUrlInRes("logout", res)


class Login(TestCase):
    URL_NAME = "login"

    def test_contains_dev_login_url(self):
        res = self.get()
        self.assert200(res)
        self.assertUrlInRes("login_dev", res)

    def test_redirects_to_profile_if_logged_in(self):
        self.login_john()
        res = self.get()
        self.assertRedirectToUrlName(res, "profile")
        self.assertIsAuthenticated()


class LoginDev(TestCase):
    URL_NAME = "login_dev"

    def test_contains_form(self):
        res = self.get()
        self.assert200(res)
        self.assertInRes("form", res)

    @requests_mock.Mocker()
    def test_login_fail(self, mocker):
        mocker.get(
            "https://www.mediawiki.org/w/rest.php/oauth2/resource/profile",
            json={"error": "access denied"},
            status_code=401,
        )
        res = self.post(data={"access_token": "my_invalid_token"})
        self.assertStatus(res, 400)
        self.assertInRes("Your access token is not valid", res)

    @requests_mock.Mocker()
    def test_login_success(self, mocker):
        mocker.get(
            # TODO: refactor this repeated URL
            "https://www.mediawiki.org/w/rest.php/oauth2/resource/profile",
            json={"username": "Maria"},
            status_code=200,
        )

        res = self.post(data={"access_token": "valid_token"})
        self.assertRedirectToUrlName(res, "profile")

        user = self.get_user()
        token = Token.objects.get(user=user)
        self.assertEqual(user.username, "Maria")
        self.assertEqual(token.value, "valid_token")


class Logout(TestCase):
    URL_NAME = "logout"

    def test_clear_tokens(self):
        self.login_john()
        user_id = self.get_user().id
        self.get()

        tokens = Token.objects.filter(user__id=user_id)
        self.assertFalse(tokens.exists())

    def test_redirects_to_root(self):
        res = self.get()
        self.assertRedirectToPath(res, "/")


class OAuthRedirect(TestCase):
    URL_NAME = "oauth_redirect"

    def test_redirect(self):
        res = self.get()

        self.assertRedirect(res)
        location = res.headers["Location"]
        self.assertIsNotNone(os.getenv("OAUTH_CLIENT_ID"))
        self.assertIn(os.getenv("OAUTH_CLIENT_ID"), location)
        self.assertIn("mediawiki.org/w/rest.php/oauth2/authorize", location)
