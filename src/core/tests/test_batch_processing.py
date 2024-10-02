import requests_mock

from django.test import TestCase
from django.contrib.auth.models import User

from core.tests.test_api import ApiMocker
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
    def test_batch_is_blocked_when_value_type_verification_fails(self, mocker):
        ApiMocker.property_data_type(mocker, "P65", "quantity")
        ApiMocker.add_statement_successful(mocker, "Q1234")

        batch = self.parse_and_run('Q1234|P65|32||Q1234|P65|"string"')
        self.assertEqual(batch.status, Batch.STATUS_BLOCKED)

        commands = batch.commands()
        self.assertEqual(commands[0].status, BatchCommand.STATUS_INITIAL)
        self.assertEqual(commands[1].status, BatchCommand.STATUS_ERROR)

    @requests_mock.Mocker()
    def test_successful_value_type_verification_stays_on_initial(self, mocker):
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
        batch = self.parse_and_run(raw)
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
    def test_all_data_types(self, mocker):
        ApiMocker.create_item(mocker, "Q123")
        ApiMocker.add_statement_successful(mocker, "Q123")
        ApiMocker.property_data_type(mocker, "P1", "commonsMedia")
        ApiMocker.property_data_type(mocker, "P2", "geo-shape")
        ApiMocker.property_data_type(mocker, "P3", "tabular-data")
        ApiMocker.property_data_type(mocker, "P4", "url")
        ApiMocker.property_data_type(mocker, "P5", "external-id")
        ApiMocker.property_data_type(mocker, "P6", "wikibase-item")
        ApiMocker.property_data_type(mocker, "P7", "wikibase-property")
        ApiMocker.property_data_type(mocker, "P8", "globe-coordinate")
        ApiMocker.property_data_type(mocker, "P9", "monolingualtext")
        ApiMocker.property_data_type(mocker, "P10", "quantity")
        ApiMocker.property_data_type(mocker, "P11", "string")
        ApiMocker.property_data_type(mocker, "P12", "time")
        ApiMocker.property_data_type(mocker, "P13", "musical-notation")
        ApiMocker.property_data_type(mocker, "P14", "math")
        ApiMocker.property_data_type(mocker, "P15", "wikibase-lexeme")
        ApiMocker.property_data_type(mocker, "P16", "wikibase-form")
        ApiMocker.property_data_type(mocker, "P17", "wikibase-sense")
        ApiMocker.property_data_type(mocker, "P18", "entity-schema")

        raw = """CREATE
        LAST|P1|"MyCommonsMedia.jpg"
        LAST|P2|"@43.26193/10.92708"
        LAST|P3|"my,tabular,data"
        LAST|P4|"https://www.myurl.com"
        LAST|P5|"123.456.789-00"
        LAST|P6|Q123
        LAST|P7|P123
        LAST|P8|@43.26193/10.92708
        LAST|P9|pt:"monolingualtext"
        LAST|P10|12345678
        LAST|P11|"string"
        LAST|P12|+1967-01-17T00:00:00Z/11
        LAST|P13|"my musical notation"
        LAST|P14|"my mathematical notation"
        LAST|P15|L123
        LAST|P16|L123-F123
        LAST|P17|L123-S123
        LAST|P18|Q123"""
        batch = self.parse_and_run(raw)
        self.assertEqual(batch.status, Batch.STATUS_DONE)

        commands = batch.commands()
        self.assertEqual(commands[0].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[1].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[2].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[3].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[4].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[5].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[6].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[7].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[8].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[9].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[10].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[11].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[12].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[13].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[14].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[15].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[16].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[17].status, BatchCommand.STATUS_DONE)
        self.assertEqual(commands[18].status, BatchCommand.STATUS_DONE)
