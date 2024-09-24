import requests_mock

from django.test import TestCase
from django.contrib.auth.models import User

from core.tests.test_api import ApiMocker
from core.models import Batch
from core.models import BatchCommand
from core.parsers.v1 import V1CommandParser
from web.models import Token


class ProcessingTests(TestCase):
    def parse(self, text):
        user = User.objects.create(username="user")
        Token.objects.create(user=user, value="tokenvalue")
        v1 = V1CommandParser()
        return v1.parse("Test", "user", text)

    def parse_with_block_on_errors(self, text):
        batch = self.parse(text)
        batch.block_on_errors = True
        batch.save()
        return batch

    @requests_mock.Mocker()
    def test_batch_success(self, mocker):
        ApiMocker.property_data_type(mocker, "P65", "quantity")
        ApiMocker.property_data_type(mocker, "P12", "url")
        ApiMocker.add_statement_successful(mocker, "Q1234")

        batch = self.parse('Q1234|P65|32||Q1234|P12|"""https://myurl.com"""')
        batch.run()
        self.assertEqual(batch.status, Batch.STATUS_DONE)

        commands = batch.commands()
        self.assertEqual(commands[0].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[1].status, BatchCommand.STATUS_DONE)

    @requests_mock.Mocker()
    def test_batch_is_blocked_when_data_type_verification_fails(self, mocker):
        ApiMocker.property_data_type(mocker, "P65", "quantity")
        ApiMocker.add_statement_successful(mocker, "Q1234")

        batch = self.parse('Q1234|P65|32||Q1234|P65|"string"')
        batch.block_on_errors = True
        batch.run()
        self.assertEqual(batch.status, Batch.STATUS_BLOCKED)

        commands = batch.commands()
        self.assertEqual(commands[0].status, BatchCommand.STATUS_INITIAL)
        self.assertEqual(commands[1].status, BatchCommand.STATUS_ERROR)

    @requests_mock.Mocker()
    def test_successful_data_type_verification_stays_on_initial(self, mocker):
        ApiMocker.property_data_type(mocker, "P111", "quantity")
        ApiMocker.add_statement_successful(mocker, "Q1234")

        raw = """Q1234|P111|0
        Q1234|P111|1
        Q1234|P111|2
        Q1234|P111|3
        Q1234|P111|4
        Q1234|P111|5
        Q1234|P111|6
        Q1234|P111|"string"
        Q1234|P111|8"""
        batch = self.parse(raw)
        batch.block_on_errors = True
        batch.run()
        self.assertEqual(batch.status, Batch.STATUS_BLOCKED)

        commands = batch.commands()
        self.assertEqual(commands[0].status, BatchCommand.STATUS_INITIAL)
        self.assertEqual(commands[1].status, BatchCommand.STATUS_INITIAL)
        self.assertEqual(commands[2].status, BatchCommand.STATUS_INITIAL)
        self.assertEqual(commands[3].status, BatchCommand.STATUS_INITIAL)
        self.assertEqual(commands[4].status, BatchCommand.STATUS_INITIAL)
        self.assertEqual(commands[5].status, BatchCommand.STATUS_INITIAL)
        self.assertEqual(commands[6].status, BatchCommand.STATUS_INITIAL)
        self.assertEqual(commands[7].status, BatchCommand.STATUS_ERROR)
        self.assertEqual(commands[8].status, BatchCommand.STATUS_INITIAL)
        self.assertEqual(len(commands), 9)

    @requests_mock.Mocker()
    def test_block_on_errors(self, mocker):
        ApiMocker.property_data_type(mocker, "P5", "quantity")
        ApiMocker.add_statement_successful(mocker, "Q1")
        raw = """Q1|P5|33||Q1|P5|"string"||Q1|P5|45"""

        batch = self.parse(raw)
        batch.block_on_errors = False
        batch.save()
        batch.run()
        self.assertEqual(batch.status, Batch.STATUS_DONE)
        commands = batch.commands()
        self.assertEqual(commands[0].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[1].status, BatchCommand.STATUS_ERROR)
        self.assertEqual(commands[2].status, BatchCommand.STATUS_DONE)
        self.assertEqual(len(commands), 3)

        ApiMocker.add_statement_failed_server(mocker, "Q2")
        v1 = V1CommandParser()
        batch = v1.parse("Should block", "user", "Q1|P5|123||Q2|P5|123||Q1|P5|123||Q1|P5|123")
        batch.block_on_errors = True
        batch.save()
        batch.run()
        self.assertEqual(batch.status, Batch.STATUS_BLOCKED)
        commands = batch.commands()
        self.assertEqual(commands[0].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[1].status, BatchCommand.STATUS_ERROR)
        self.assertEqual(commands[2].status, BatchCommand.STATUS_INITIAL)
        self.assertEqual(commands[3].status, BatchCommand.STATUS_INITIAL)
        self.assertEqual(len(commands), 4)

    @requests_mock.Mocker()
    def test_dont_block_on_errors_last_id(self, mocker):
        """
        Checks that when NOT blocking on errors, if a CREATE
        fails, all subsequent LAST commands also fail.
        """
        ApiMocker.property_data_type(mocker, "P1", "quantity")
        ApiMocker.add_statement_successful(mocker, "Q1")
        ApiMocker.create_item_failed_server(mocker)
        batch = self.parse("CREATE||LAST|P1|1||LAST|P1|1||Q1|P1|1")
        batch.run()
        self.assertEqual(batch.status, Batch.STATUS_DONE)
        commands = batch.commands()
        self.assertEqual(commands[0].status, BatchCommand.STATUS_ERROR)
        self.assertTrue("The server failed to process the request" in commands[0].message)
        self.assertEqual(commands[1].status, BatchCommand.STATUS_ERROR)
        self.assertEqual(commands[1].message, "LAST could not be evaluated.")
        self.assertEqual(commands[2].status, BatchCommand.STATUS_ERROR)
        self.assertEqual(commands[2].message, "LAST could not be evaluated.")
        self.assertEqual(commands[3].status, BatchCommand.STATUS_DONE)

    @requests_mock.Mocker()
    def test_block_on_errors_last_id(self, mocker):
        """
        Checks that when we DO block on errors, if a CREATE
        fails, all subsequent LAST commands stay in INITIAL.
        """
        ApiMocker.property_data_type(mocker, "P1", "quantity")
        ApiMocker.add_statement_successful(mocker, "Q1")
        ApiMocker.create_item_failed_server(mocker)
        batch = self.parse_with_block_on_errors("CREATE||LAST|P1|1||LAST|P1|1||Q1|P1|1")
        batch.run()
        self.assertEqual(batch.status, Batch.STATUS_BLOCKED)
        commands = batch.commands()
        self.assertEqual(commands[0].status, BatchCommand.STATUS_ERROR)
        self.assertTrue("The server failed to process the request" in commands[0].message)
        self.assertEqual(commands[1].status, BatchCommand.STATUS_INITIAL)
        self.assertEqual(commands[2].status, BatchCommand.STATUS_INITIAL)
        self.assertEqual(commands[3].status, BatchCommand.STATUS_INITIAL)
