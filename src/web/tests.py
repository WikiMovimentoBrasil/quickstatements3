from django.test import TestCase as DjangoTestCase
from django.urls import reverse

# Create your tests here.


class TestCase(DjangoTestCase):
    URL_NAME = "/"

    def assert200(self, response):
        self.assertEqual(response.status_code, 200)

    def assertRedirect(self, response):
        self.assertEqual(response.status_code, 302)

    def assertRedirectToPath(self, response, path):
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], path)

    def assertRedirectToUrlName(self, response, url_name):
        self.assertRedirectToPath(response, reverse(url_name))

    def assertUrlInRes(self, url_name, response):
        """Checks if the URL is contained in the response"""
        self.assertInRes(reverse(url_name), response)

    def assertInRes(self, substring, response):
        """Checks if a substring is contained in response content"""
        self.assertIn(substring.lower(), str(response.content).lower().strip())

    def get(self):
        return self.client.get(reverse(self.URL_NAME))

    def save_john_username(self):
        # We need to save it into a variable before saving it
        session = self.client.session
        session["username"] = "John"
        session.save()


class ProfileTests(TestCase):
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

    # TODO: create tests for the POST
    # but for that we need to mock the request


class Logout(TestCase):
    URL_NAME = "logout"

    def test_clears_session(self):
        self.save_john_username()
        self.assertIsNotNone(self.client.session.get("username"))
        self.get()
        self.assertIsNone(self.client.session.get("username"))

    def test_redirects_to_root(self):
        res = self.get()
        self.assertRedirectToPath(res, "/")
