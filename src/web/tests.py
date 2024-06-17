from django.test import TestCase
from django.urls import reverse

# Create your tests here.


def is_in_res(substring, response):
    """Checks if a substring is contained in response content"""
    return substring.lower() in str(response.content).lower().strip()


def url_in_res(url_name, response):
    """Checks if the URL with the given name is contained in the response"""
    return is_in_res(reverse(url_name), response)


def save_john_username_in_session(client):
    # We need to save it into a variable before modifying it
    session = client.session
    session["username"] = "John"
    session.save()


class ProfileTests(TestCase):
    def get(self):
        return self.client.get(reverse("profile"))

    def test_not_logged_in(self):
        res = self.get()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(is_in_res("not logged in", res))
        self.assertTrue(url_in_res("login", res))

    def test_logged_in_when_username_in_session(self):
        save_john_username_in_session(self.client)
        res = self.get()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(is_in_res("John", res))
        self.assertTrue(url_in_res("logout", res))


class Login(TestCase):
    def get(self):
        return self.client.get(reverse("login"))

    def test_contains_dev_login_url(self):
        res = self.get()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(url_in_res("login_dev", res))

    def test_redirects_to_profile_if_username_in_session(self):
        save_john_username_in_session(self.client)
        res = self.get()
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers["Location"], reverse("profile"))


class LoginDev(TestCase):
    def get(self):
        return self.client.get(reverse("login_dev"))

    def test_contains_form(self):
        res = self.get()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(is_in_res("form", res))

    # TODO: create tests for the POST
    # but for that we need to mock the request


class Logout(TestCase):
    def get(self):
        return self.client.get(reverse("logout"))

    def test_clears_session(self):
        save_john_username_in_session(self.client)
        self.assertIsNotNone(self.client.session.get("username"))
        self.get()
        self.assertIsNone(self.client.session.get("username"))

    def test_redirects_to_root(self):
        res = self.get()
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers["Location"], "/")
