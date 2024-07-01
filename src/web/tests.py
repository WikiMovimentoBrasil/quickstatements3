import requests_mock

from django.test import TestCase as DjangoTestCase
from django.urls import reverse

# Create your tests here.


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

    def assertSessionEqual(self, key, value):
        """Asserts a given session key has the given value."""
        session = self.client.session
        self.assertEqual(session.get(key), value)

    def assertSessionEmpty(self, key):
        """Asserts a given session key has no value"""
        self.assertIsNone(self.client.session.get(key))

    def assertSessionNotEmpty(self, key):
        """Asserts a given session key has a defined value"""
        self.assertIsNotNone(self.client.session.get(key))

    # ---------------
    # Utility methods
    # ---------------

    def get(self):
        """Make a test GET request with the test client"""
        return self.client.get(reverse(self.URL_NAME))

    def post(self, data=None):
        """Make a test POST request with the test client"""
        return self.client.post(reverse(self.URL_NAME), data=data)

    def save_john_username(self):
        """Save username 'John' in the test client session"""
        # We need to save it into a variable before saving it
        session = self.client.session
        session["username"] = "John"
        session.save()


class Profile(TestCase):
    URL_NAME = "profile"

    def test_not_logged_in(self):
        res = self.get()
        self.assert200(res)
        self.assertInRes("not logged in", res)
        self.assertUrlInRes("login", res)

    def test_logged_in_when_username_in_session(self):
        self.save_john_username()
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

    def test_redirects_to_profile_if_username_in_session(self):
        self.save_john_username()
        res = self.get()
        self.assertRedirectToUrlName(res, "profile")


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

        self.assertSessionEqual("access_token", "valid_token")
        self.assertSessionEqual("username", "Maria")


class Logout(TestCase):
    URL_NAME = "logout"

    def test_clears_session(self):
        self.save_john_username()
        self.assertSessionNotEmpty("username")
        self.get()
        self.assertSessionEmpty("username")

    def test_redirects_to_root(self):
        res = self.get()
        self.assertRedirectToPath(res, "/")
