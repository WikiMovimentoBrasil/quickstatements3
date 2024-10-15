import requests_mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.test import Client

from core.tests.test_api import ApiMocker
from core.client import Client as ApiClient
from web.models import Token
from web.models import Preferences

from core.models import Batch
from core.models import BatchCommand
from core.parsers.v1 import V1CommandParser


class ViewsTest(TestCase):
    URL_NAME = "profile"

    def assertInRes(self, substring, response):
        """Checks if a substring is contained in response content"""
        self.assertIn(substring.lower(), str(response.content).lower().strip())

    def assertNotInRes(self, substring, response):
        """Checks if a substring is not contained in response content"""
        self.assertNotIn(substring.lower(), str(response.content).lower().strip())

    def login_user_and_get_token(self, username):
        """
        Creates an user and a test token.

        Returns a tuple with the user object and their API client.
        """
        user = User.objects.create_user(username=username)
        self.client.force_login(user)

        Token.objects.create(user=user, value="TEST_TOKEN")
        api_client = ApiClient.from_user(user)

        return (user, api_client)

    def test_home(self):
        c = Client()
        response = c.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("index.html")

    def test_batches(self):
        c = Client()
        response = c.get("/batches")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["location"], "/batches/")

        response = c.get("/batches/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batches.html")
        self.assertEqual(list(response.context["page"].object_list), [])

    def test_batches_by_user(self):
        c = Client()
        response = c.get("/batches/mgalves80")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["location"], "/batches/mgalves80/")

        response = c.get("/batches/mgalves80/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batches.html")
        self.assertEqual(list(response.context["page"].object_list), [])
        self.assertEqual(response.context["username"], "mgalves80")

    def test_non_existing_batch(self):
        c = Client()
        response = c.get("/batch/123456789")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["location"], "/batch/123456789/")

        response = c.get("/batch/123456789/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed("batch_not_found.html")

    def test_existing_batch(self):
        batch = Batch.objects.create(name="My new batch", user="mgalves80")

        c = Client()
        response = c.get(f"/batch/{batch.pk}")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["location"], f"/batch/{batch.pk}/")

        response = c.get(f"/batch/{batch.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batch.html")
        self.assertEqual(response.context["batch"], batch)

        response = c.get(f"/batch/{batch.pk}/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batch_summary.html")
        self.assertEqual(response.context["pk"], batch.pk)
        self.assertEqual(response.context["status"], "Initial")
        self.assertEqual(response.context["error_count"], 0)
        self.assertEqual(response.context["initial_count"], 0)
        self.assertEqual(response.context["running_count"], 0)
        self.assertEqual(response.context["done_count"], 0)
        self.assertEqual(response.context["total_count"], 0)
        self.assertEqual(response.context["done_percentage"], 0)

        response = c.get(f"/batch/{batch.pk}/commands/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batch_commands.html")
        self.assertEqual(response.context["batch_pk"], batch.pk)
        self.assertEqual(response.context["only_errors"], False)

    def test_batch_command_filters(self):
        batch = Batch.objects.create(name="My new batch", user="mgalves80")
        b1 = BatchCommand.objects.create(
            batch=batch, index=0, action=BatchCommand.ACTION_ADD, json={}, raw="{}", status=BatchCommand.STATUS_INITIAL
        )
        b2 = BatchCommand.objects.create(
            batch=batch, index=1, action=BatchCommand.ACTION_ADD, json={}, raw="{}", status=BatchCommand.STATUS_ERROR
        )
        b3 = BatchCommand.objects.create(
            batch=batch, index=2, action=BatchCommand.ACTION_ADD, json={}, raw="{}", status=BatchCommand.STATUS_INITIAL
        )
        b4 = BatchCommand.objects.create(
            batch=batch, index=4, action=BatchCommand.ACTION_ADD, json={}, raw="{}", status=BatchCommand.STATUS_ERROR
        )

        c = Client()
        response = c.get(f"/batch/{batch.pk}/commands/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batch_commands.html")
        self.assertEqual(response.context["batch_pk"], batch.pk)
        self.assertEqual(response.context["only_errors"], False)
        self.assertEqual(list(response.context["page"].object_list), [b1, b2, b3, b4])
        response = c.get(f"/batch/{batch.pk}/commands/?show_errors=1")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batch_commands.html")
        self.assertEqual(response.context["batch_pk"], batch.pk)
        self.assertEqual(response.context["only_errors"], True)
        self.assertEqual(list(response.context["page"].object_list), [b2, b4])

    def test_existing_batches(self):
        b1 = Batch.objects.create(name="My new batch", user="mgalves80")
        b2 = Batch.objects.create(name="My new batch", user="mgalves80")
        b3 = Batch.objects.create(name="My new batch", user="wikilover")

        c = Client()

        response = c.get("/batches/mgalves80/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batches.html")
        self.assertEqual(list(response.context["page"].object_list), [b2, b1])
        self.assertEqual(response.context["username"], "mgalves80")

        response = c.get("/batches/wikilover/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batches.html")
        self.assertEqual(list(response.context["page"].object_list), [b3])
        self.assertEqual(response.context["username"], "wikilover")

        response = c.get("/batches/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batches.html")
        self.assertEqual(list(response.context["page"].object_list), [b3, b2, b1])

    def test_create_v1_batch_logged_user(self):
        c = Client()
        user = User.objects.create_user(username="john")
        c.force_login(user)

        # Black box testing. We dont have any batch listed
        response = c.get("/batches/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batches.html")
        self.assertEqual(list(response.context["page"].object_list), [])

        # Creating our new batch
        response = c.get("/batch/new/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("new_batch.html")

        response = c.post("/batch/new/", data={"name": "My v1 batch", "type": "v1", "commands": "CREATE||-Q1234|P1|12||Q222|P4|9~0.1"})
        self.assertEqual(response.status_code, 302)

        # Lets view the new batch
        response = c.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batch.html")
        batch = response.context["batch"]
        self.assertEqual(batch.name, "My v1 batch")
        self.assertTrue(batch.is_preview)
        self.assertEqual(batch.batchcommand_set.count(), 3)

        # Listing again. Now we have something
        response = c.get("/batches/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batches.html")
        self.assertEqual(list(response.context["page"].object_list), [batch])
        self.assertTrue(batch.is_preview)

    def test_create_csv_batch_logged_user(self):
        c = Client()
        user = User.objects.create_user(username="john")
        c.force_login(user)

        # Black box testing. We dont have any batch listed
        response = c.get("/batches/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batches.html")
        self.assertEqual(list(response.context["page"].object_list), [])

        # Creating our new batch
        response = c.get("/batch/new/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("new_batch.html")

        response = c.post("/batch/new/", data={"name": "My CSV batch", "type": "csv", "commands": "qid,P31,-P31"})
        self.assertEqual(response.status_code, 302)

        # Lets view the new batch
        response = c.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batch.html")
        batch = response.context["batch"]
        self.assertEqual(batch.name, "My CSV batch")
        self.assertEqual(batch.batchcommand_set.count(), 0)

        # Listing again. Now we have something
        response = c.get("/batches/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batches.html")
        self.assertEqual(list(response.context["page"].object_list), [batch])

    def test_create_batch_anonymous_user(self):
        c = Client()
       
        response = c.get("/batch/new/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/auth/login/?next=/batch/new/")

        response = c.post("/batch/new/", data={"name": "My v1 batch", "type": "v1", "commands": "CREATE||-Q1234|P1|12||Q222|P4|9~0.1"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/auth/login/?next=/batch/new/")

    @requests_mock.Mocker()
    def test_command_labels(self, mocker):
        user, api_client = self.login_user_and_get_token("wikiuser")

        parser = V1CommandParser()
        batch = parser.parse("Batch", "wikiuser", "Q1234\tP2\tQ1")

        labels = {
            "en": "English label",
            "pt": "Portuguese label",
        }
        ApiMocker.labels(mocker, api_client, "Q1234", labels)

        response = self.client.get(f"/batch/{batch.pk}/commands/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batch_commands.html")
        self.assertInRes("English label", response)

        # Portuguse uses its label
        prefs = Preferences.objects.create(
            user=user,
            language="pt",
        )
        response = self.client.get(f"/batch/{batch.pk}/commands/")
        self.assertEqual(response.status_code, 200)
        self.assertInRes("Portuguese label", response)

        # Spanish will use the english label
        prefs.language = "es"
        prefs.save()
        response = self.client.get(f"/batch/{batch.pk}/commands/")
        self.assertEqual(response.status_code, 200)
        self.assertInRes("English label", response)

    @requests_mock.Mocker()
    def test_profile_is_autoconfirmed(self, mocker):
        ApiMocker.is_autoconfirmed(mocker)
        user, api_client = self.login_user_and_get_token("user")
        res = self.client.get("/auth/profile/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed("profile.html")
        self.assertEqual(res.context["is_autoconfirmed"], True)
        self.assertEqual(res.context["token_failed"], False)
        self.assertInRes("We have successfully verified that you are an autoconfirmed user.", res)

    @requests_mock.Mocker()
    def test_profile_is_not_autoconfirmed(self, mocker):
        ApiMocker.is_not_autoconfirmed(mocker)
        user, api_client = self.login_user_and_get_token("user")
        res = self.client.get("/auth/profile/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed("profile.html")
        self.assertEqual(res.context["is_autoconfirmed"], False)
        self.assertEqual(res.context["token_failed"], False)
        self.assertInRes("You are not an autoconfirmed user.", res)

    @requests_mock.Mocker()
    def test_profile_autoconfirmed_failed(self, mocker):
        ApiMocker.autoconfirmed_failed(mocker)
        user, api_client = self.login_user_and_get_token("user")
        res = self.client.get("/auth/profile/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed("profile.html")
        self.assertEqual(res.context["is_autoconfirmed"], False)
        self.assertEqual(res.context["token_failed"], True)
        self.assertInRes("We could not verify you are an autoconfirmed user.", res)

    @requests_mock.Mocker()
    def test_new_batch_is_not_autoconfirmed(self, mocker):
        ApiMocker.is_not_autoconfirmed(mocker)
        user, api_client = self.login_user_and_get_token("user")
        res = self.client.get("/batch/new/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["is_autoconfirmed"], False)
        self.assertInRes("Preview", res)
        self.assertInRes("Note: only", res)
        self.assertInRes("autoconfirmed users", res)
        self.assertInRes("can have their batches run.", res)

    @requests_mock.Mocker()
    def test_new_batch_is_autoconfirmed(self, mocker):
        ApiMocker.is_autoconfirmed(mocker)
        user, api_client = self.login_user_and_get_token("user")
        res = self.client.get("/batch/new/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["is_autoconfirmed"], True)
        self.assertInRes("Create", res)
        self.assertNotInRes("Note: only", res)
        self.assertNotInRes("autoconfirmed users", res)
        self.assertNotInRes("can have their batches run.", res)

    def test_allow_start_after_create(self):
        c = Client()
        user = User.objects.create_user(username="john")
        c.force_login(user)

        response = c.post("/batch/new/", data={"name": "My v1 batch", "type": "v1", "commands": "CREATE||-Q1234|P1|12||Q222|P4|9~0.1"})
        self.assertEqual(response.status_code, 302)

        response = c.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batch.html")
        batch = response.context["batch"]
        self.assertEqual(batch.name, "My v1 batch")
        self.assertEqual(batch.batchcommand_set.count(), 3)
        self.assertTrue(batch.is_preview)

        pk = batch.pk

        response = c.get(f"/batch/{pk}/allow_start/")
        self.assertEqual(response.status_code, 405)

        response = c.post(f"/batch/{pk}/allow_start/")
        self.assertEqual(response.status_code, 302)

        response = c.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["batch"].is_preview)
        self.assertTrue(response.context["batch"].is_initial)

    @requests_mock.Mocker()
    def test_allow_start_after_create_is_not_autoconfirmed(self, mocker):
        ApiMocker.is_not_autoconfirmed(mocker)
        user, api_client = self.login_user_and_get_token("user")

        res = self.client.post("/batch/new/", data={"name": "name", "type": "v1", "commands": "CREATE||LAST|P1|Q1"})
        self.assertEqual(res.status_code, 302)
        res = self.client.get(res.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["is_autoconfirmed"], False)
        self.assertInRes("Note: only", res)
        self.assertInRes("autoconfirmed users", res)
        self.assertInRes("can have their batches run.", res)
        self.assertInRes("""<input type="submit" value="Allow batch to run" disabled>""", res)

    @requests_mock.Mocker()
    def test_allow_start_after_create_is_autoconfirmed(self, mocker):
        ApiMocker.is_autoconfirmed(mocker)
        user, api_client = self.login_user_and_get_token("user")

        res = self.client.post("/batch/new/", data={"name": "name", "type": "v1", "commands": "CREATE||LAST|P1|Q1"})
        self.assertEqual(res.status_code, 302)
        res = self.client.get(res.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["is_autoconfirmed"], True)
        self.assertInRes("""<input type="submit" value="Allow batch to run">""", res)
        self.assertNotInRes("Note: only", res)
        self.assertNotInRes("autoconfirmed users", res)
        self.assertNotInRes("can have their batches run.", res)
        self.assertNotInRes("""<input type="submit" value="Allow batch to run" disabled>""", res)

    @requests_mock.Mocker()
    def test_batch_does_not_call_autoconfirmed_if_not_in_preview(self, mocker):
        ApiMocker.is_autoconfirmed(mocker)
        user, api_client = self.login_user_and_get_token("user")

        res = self.client.post("/batch/new/", data={"name": "name", "type": "v1", "commands": "CREATE||LAST|P1|Q1"})
        self.assertEqual(res.status_code, 302)
        url = res.url
        res = self.client.get(url)
        self.assertEqual(res.context["is_autoconfirmed"], True)
        batch = res.context["batch"]
        batch.allow_start()
        res = self.client.get(url)
        self.assertEqual(res.context["is_autoconfirmed"], None)
        batch.stop()
        res = self.client.get(url)
        self.assertEqual(res.context["is_autoconfirmed"], None)

    def test_create_block_on_errors(self):
        c = Client()
        user = User.objects.create_user(username="john")
        c.force_login(user)

        response = c.post(
            "/batch/new/",
            data={
                "name": "should block",
                "type": "v1",
                "commands": "CREATE||-Q1234|P1|12||Q222|P4|9~0.1",
            },
        )
        response = c.get(response.url)
        self.assertFalse(response.context["batch"].block_on_errors)

        response = c.post(
            "/batch/new/",
            data={
                "name": "should block",
                "type": "v1",
                "commands": "CREATE||-Q1234|P1|12||Q222|P4|9~0.1",
                "block_on_errors": "block_on_errors",
            },
        )
        response = c.get(response.url)
        self.assertTrue(response.context["batch"].block_on_errors)

    def test_restart_after_stopped_buttons(self):
        c = Client()
        user = User.objects.create_user(username="john")
        c.force_login(user)

        response = c.post("/batch/new/", data={"name": "My v1 batch", "type": "v1", "commands": "CREATE||-Q1234|P1|12||Q222|P4|9~0.1"})
        self.assertEqual(response.status_code, 302)

        response = c.get(response.url)
        self.assertInRes("Allow batch to run", response)

        batch = response.context["batch"]
        pk = batch.pk

        response = c.post(f"/batch/{pk}/allow_start/")
        response = c.get(response.url)
        self.assertInRes("Stop execution", response)

        response = c.post(f"/batch/{pk}/stop/")
        response = c.get(response.url)
        self.assertInRes("Restart", response)

        response = c.post(f"/batch/{pk}/restart/")
        response = c.get(response.url)
        self.assertInRes("Stop execution", response)

