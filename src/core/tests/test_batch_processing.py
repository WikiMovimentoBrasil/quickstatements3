import requests_mock

from django.test import TestCase
from django.contrib.auth.models import User

from api.utils import ApiMocker
from core.models import Batch
from core.models import BatchCommand
from core.parsers.v1 import V1CommandParser
from web.models import Token


class ProcessingTests(TestCase):
    def parse_and_run(self, text):
        user = User.objects.create(username="user")
        Token.objects.create(user=user, value="tokenvalue")
        v1 = V1CommandParser()
        batch = v1.parse("Test", "user", text)
        batch.run()
        return batch

    @requests_mock.Mocker()
    def test_batch_success(self, mocker):
        ApiMocker.property_data_type(mocker, "P65", "quantity")
        ApiMocker.property_data_type(mocker, "P12", "url")
        ApiMocker.add_statement_successful(mocker, "Q1234")

        batch = self.parse_and_run('Q1234|P65|32||Q1234|P12|"""https://myurl.com"""')
        self.assertEqual(batch.status, Batch.STATUS_DONE)

        commands = batch.commands()
        self.assertEqual(commands[0].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[1].status, BatchCommand.STATUS_DONE)

    @requests_mock.Mocker()
    def test_batch_is_blocked_when_a_command_fails(self, mocker):
        ApiMocker.property_data_type(mocker, "P65", "quantity")
        ApiMocker.add_statement_successful(mocker, "Q1234")

        batch = self.parse_and_run("Q1234|P65|32||Q1234|P65|'string'")
        self.assertEqual(batch.status, Batch.STATUS_BLOCKED)

        commands = batch.commands()
        self.assertEqual(commands[0].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[1].status, BatchCommand.STATUS_ERROR)
