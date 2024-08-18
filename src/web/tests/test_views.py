
from django.contrib.auth.models import User
from django.test import TestCase
from django.test import Client
from django.urls import reverse

from core.models import Batch


class ViewsTest(TestCase):
    URL_NAME = "profile"

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
        self.assertEqual(batch.batchcommand_set.count(), 3)

        # Listing again. Now we have something
        response = c.get("/batches/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("batches.html")
        self.assertEqual(list(response.context["page"].object_list), [batch])

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


