from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from quickstatements.apps.core.models import Batch, BatchCommand


class BatchDetailViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="myuser")
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()

    def test_non_auth_request(self):
        response = self.client.get(reverse("batch-detail", kwargs={"pk": 1}))
        self.assertEqual(response.status_code, 401)

    def test_bad_auth_request(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token fdsfsdfsfsdafsdfsdfsfsdfsad")
        response = self.client.get(reverse("batch-detail", kwargs={"pk": 1}))
        self.assertEqual(response.status_code, 401)

    def test_non_existing_authenticated_request(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.get(reverse("batch-detail", kwargs={"pk": 1}))
        self.assertEqual(response.status_code, 404)

    def test_initial_empty_batch_authenticated_request(self):
        original = Batch.objects.create(name="Batch 0", user="testuser")
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.get(reverse("batch-detail", kwargs={"pk": original.pk}))
        self.assertEqual(response.status_code, 200)
        batch = response.data
        self.assertEqual(batch["pk"], original.pk)
        self.assertEqual(batch["user"], "testuser")
        self.assertEqual(batch["name"], "Batch 0")
        self.assertEqual(batch["status"], {"code": 1, "display": "Initial"})
        self.assertEqual(
            batch["summary"],
            {
                "initial_commands": 0,
                "error_commands": 0,
                "running_commands": 0,
                "done_commands": 0,
                "total_commands": 0,
            },
        )
        self.assertEqual(batch["message"], None)
        self.assertTrue("created" in batch)
        self.assertTrue("modified" in batch)
        self.assertEqual(
            batch["commands_url"], f"http://testserver/api/v1/batches/{original.pk}/commands/"
        )

    def test_batch_authenticated_request(self):
        original = Batch.objects.create(
            name="Batch 1", user="testuser", status=Batch.STATUS_RUNNING
        )
        command = BatchCommand.objects.create(
            batch=original,
            index=1,
            action=BatchCommand.ACTION_ADD,
            json={},
            status=BatchCommand.STATUS_INITIAL,
        )

        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

        response = self.client.get(reverse("batch-detail", kwargs={"pk": original.pk}))
        self.assertEqual(response.status_code, 200)
        batch = response.data
        self.assertEqual(batch["pk"], original.pk)
        self.assertEqual(batch["user"], "testuser")
        self.assertEqual(batch["name"], "Batch 1")
        self.assertEqual(batch["status"], {"code": 2, "display": "Running"})
        self.assertEqual(
            batch["summary"],
            {
                "initial_commands": 1,
                "error_commands": 0,
                "running_commands": 0,
                "done_commands": 0,
                "total_commands": 1,
            },
        )
        self.assertEqual(batch["message"], None)
        self.assertTrue("created" in batch)
        self.assertTrue("modified" in batch)
        self.assertEqual(
            batch["commands_url"], f"http://testserver/api/v1/batches/{original.pk}/commands/"
        )

        command.status = BatchCommand.STATUS_RUNNING
        command.save()

        response = self.client.get(reverse("batch-detail", kwargs={"pk": original.pk}))
        self.assertEqual(response.status_code, 200)
        batch = response.data
        self.assertEqual(batch["pk"], original.pk)
        self.assertEqual(batch["user"], "testuser")
        self.assertEqual(batch["name"], "Batch 1")
        self.assertEqual(batch["status"], {"code": 2, "display": "Running"})
        self.assertEqual(
            batch["summary"],
            {
                "initial_commands": 0,
                "error_commands": 0,
                "running_commands": 1,
                "done_commands": 0,
                "total_commands": 1,
            },
        )
        self.assertEqual(batch["message"], None)
        self.assertTrue("created" in batch)
        self.assertTrue("modified" in batch)
        self.assertEqual(
            batch["commands_url"], f"http://testserver/api/v1/batches/{original.pk}/commands/"
        )

        command.status = BatchCommand.STATUS_DONE
        command.save()

        response = self.client.get(reverse("batch-detail", kwargs={"pk": original.pk}))
        self.assertEqual(response.status_code, 200)
        batch = response.data
        self.assertEqual(batch["pk"], original.pk)
        self.assertEqual(batch["user"], "testuser")
        self.assertEqual(batch["name"], "Batch 1")
        self.assertEqual(batch["status"], {"code": 2, "display": "Running"})
        self.assertEqual(
            batch["summary"],
            {
                "initial_commands": 0,
                "error_commands": 0,
                "running_commands": 0,
                "done_commands": 1,
                "total_commands": 1,
            },
        )
        self.assertEqual(batch["message"], None)
        self.assertTrue("created" in batch)
        self.assertTrue("modified" in batch)
        self.assertEqual(
            batch["commands_url"], f"http://testserver/api/v1/batches/{original.pk}/commands/"
        )

        _command2 = BatchCommand.objects.create(
            batch=original,
            index=1,
            action=BatchCommand.ACTION_ADD,
            json={},
            status=BatchCommand.STATUS_INITIAL,
        )

        response = self.client.get(reverse("batch-detail", kwargs={"pk": original.pk}))
        self.assertEqual(response.status_code, 200)
        batch = response.data
        self.assertEqual(batch["pk"], original.pk)
        self.assertEqual(batch["user"], "testuser")
        self.assertEqual(batch["name"], "Batch 1")
        self.assertEqual(batch["status"], {"code": 2, "display": "Running"})
        self.assertEqual(
            batch["summary"],
            {
                "initial_commands": 1,
                "error_commands": 0,
                "running_commands": 0,
                "done_commands": 1,
                "total_commands": 2,
            },
        )
        self.assertEqual(batch["message"], None)
        self.assertTrue("created" in batch)
        self.assertTrue("modified" in batch)
        self.assertEqual(
            batch["commands_url"], f"http://testserver/api/v1/batches/{original.pk}/commands/"
        )

        _command3 = BatchCommand.objects.create(
            batch=original,
            index=1,
            action=BatchCommand.ACTION_ADD,
            json={},
            status=BatchCommand.STATUS_RUNNING,
        )

        response = self.client.get(reverse("batch-detail", kwargs={"pk": original.pk}))
        self.assertEqual(response.status_code, 200)
        batch = response.data
        self.assertEqual(batch["pk"], original.pk)
        self.assertEqual(batch["user"], "testuser")
        self.assertEqual(batch["name"], "Batch 1")
        self.assertEqual(batch["status"], {"code": 2, "display": "Running"})
        self.assertEqual(
            batch["summary"],
            {
                "initial_commands": 1,
                "error_commands": 0,
                "running_commands": 1,
                "done_commands": 1,
                "total_commands": 3,
            },
        )
        self.assertEqual(batch["message"], None)
        self.assertTrue("created" in batch)
        self.assertTrue("modified" in batch)
        self.assertEqual(
            batch["commands_url"], f"http://testserver/api/v1/batches/{original.pk}/commands/"
        )

        _command4 = BatchCommand.objects.create(
            batch=original,
            index=1,
            action=BatchCommand.ACTION_CREATE,
            json={},
            status=BatchCommand.STATUS_ERROR,
        )

        response = self.client.get(reverse("batch-detail", kwargs={"pk": original.pk}))
        self.assertEqual(response.status_code, 200)
        batch = response.data
        self.assertEqual(batch["pk"], original.pk)
        self.assertEqual(batch["user"], "testuser")
        self.assertEqual(batch["name"], "Batch 1")
        self.assertEqual(batch["status"], {"code": 2, "display": "Running"})
        self.assertEqual(
            batch["summary"],
            {
                "initial_commands": 1,
                "error_commands": 1,
                "running_commands": 1,
                "done_commands": 1,
                "total_commands": 4,
            },
        )
        self.assertEqual(batch["message"], None)
        self.assertTrue("created" in batch)
        self.assertTrue("modified" in batch)
        self.assertEqual(
            batch["commands_url"], f"http://testserver/api/v1/batches/{original.pk}/commands/"
        )

    def test_non_allowed_methods_request(self):
        original = Batch.objects.create(
            name="Batch 1", user="testuser", status=Batch.STATUS_RUNNING
        )
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.post(reverse("batch-detail", kwargs={"pk": original.pk}))
        self.assertEqual(response.status_code, 405)
        response = self.client.put(reverse("batch-detail", kwargs={"pk": original.pk}))
        self.assertEqual(response.status_code, 405)
        response = self.client.delete(reverse("batch-detail", kwargs={"pk": original.pk}))
        self.assertEqual(response.status_code, 405)
