from django.test import TestCase

from core.models import Batch
from core.models import BatchCommand
from core.parsers.v1 import V1CommandParser


class TestV1BatchCommand(TestCase):
    def setUp(self):
        self.batch = Batch.objects.create(name="Batch", user="wikiuser")

    def test_v1_correct_create_command(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "CREATE")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {"action": "create", "type": "item"})
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "CREATE ")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {"action": "create", "type": "item"})
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, " CREATE ")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {"action": "create", "type": "item"})
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_bad_create_command(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "CREATE\tQ123\t")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {})
        self.assertEqual(command.message, "CREATE command can have only 1 column")
        self.assertEqual(command.status, BatchCommand.STATUS_ERROR)

    def test_v1_correct_merge_command(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "MERGE\tQ1\tQ2")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {"action": "merge", "type": "item", "item1": "Q1", "item2": "Q2"})
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "MERGE\tQ2\tQ1")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {"action": "merge", "type": "item", "item1": "Q1", "item2": "Q2"})
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "MERGE \tQ1 \tQ2 ")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {"action": "merge", "type": "item", "item1": "Q1", "item2": "Q2"})
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_bad_merge_command(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "MERGE")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {})
        self.assertEqual(command.status, BatchCommand.STATUS_ERROR)
        self.assertEqual(command.message, "MERGE command must have 3 columns")
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "MERGE\tQ1")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {})
        self.assertEqual(command.status, BatchCommand.STATUS_ERROR)
        self.assertEqual(command.message, "MERGE command must have 3 columns")
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "MERGE\tQ1\t")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {})
        self.assertEqual(command.status, BatchCommand.STATUS_ERROR)
        self.assertEqual(command.message, "MERGE items wrong format item1=[Q1] item2=[]")
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "MERGE\tQ1\tQ2\tQ3")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {})
        self.assertEqual(command.status, BatchCommand.STATUS_ERROR)
        self.assertEqual(command.message, "MERGE command must have 3 columns")

    def test_v1_remove_item(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "-Q1234\tP2\tQ1")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "remove",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P2",
                "value": {"type": "wikibase-entityid", "value": {"entity-type": "item", "id": "Q1"}},
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_remove_time(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "-Q1234\tP1\t12")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "remove",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P1",
                "value": {"type": "quantity", "value": {"amount": "12"}},
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "-Q1234\tP3\t12U11573")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "remove",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P3",
                "value": {"type": "quantity", "value": {"amount": "12"}},
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "-Q1234\tP4\t9~0.1")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "remove",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P4",
                "value": {
                    "type": "quantity",
                    "value": {
                        "amount": "9",
                        "upperBound": 9.1,
                        "lowerBound": 8.9,
                    },
                },
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_create_item(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tP2\tQ1")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "create",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P2",
                "value": {"type": "wikibase-entityid", "value": {"entity-type": "item", "id": "Q1"}},
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_create_quantity(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tP1\t12")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "create",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P1",
                "value": {"type": "quantity", "value": {"amount": "12"}},
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tP3\t12U11573")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "create",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P3",
                "value": {"type": "quantity", "value": {"amount": "12"}},
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tP4\t9~0.1")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "create",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P4",
                "value": {
                    "type": "quantity",
                    "value": {
                        "amount": "9",
                        "upperBound": 9.1,
                        "lowerBound": 8.9,
                    },
                },
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_create_alias(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tApt\t\"Texto brasileiro\"")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {'action': "create" , 'what': "alias" , 'item': 'Q1234', 'language': 'pt', 'value': 'Texto brasileiro'}
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_create_wrong_alias(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tApt\tsomevalue")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {})
        self.assertEqual(command.message, "alias must be a string instance")
        self.assertEqual(command.status, BatchCommand.STATUS_ERROR)

    def test_v1_create_description(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tDen\t\"Item description\"")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {'action': "create" , 'what': "description" , 'item': 'Q1234', 'language': 'en', 'value': 'Item description'}
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_create_wrong_description(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tDpt\tsomevalue")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {})
        self.assertEqual(command.message, "description must be a string instance")
        self.assertEqual(command.status, BatchCommand.STATUS_ERROR)

    def test_v1_create_label(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tLfr\t\"Note en français\"")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {'action': "create" , 'what': "label" , 'item': 'Q1234', 'language': 'fr', 'value': 'Note en français'}
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_create_wrong_label(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tLpt\tbla")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {})
        self.assertEqual(command.message, "label must be a string instance")
        self.assertEqual(command.status, BatchCommand.STATUS_ERROR)

    def test_v1_create_site(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tSmysite\t\"Site mysite\"")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {'action': "create" , 'what': "sitelink" , 'item': 'Q1234', 'site': 'mysite', 'value': 'Site mysite'}
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_create_wrong_site(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tSpt\tsomevalue")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {})
        self.assertEqual(command.message, "sitelink must be a string instance")
        self.assertEqual(command.status, BatchCommand.STATUS_ERROR)

    def test_v1_create_somevalue_novalue(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tP1\tsomevalue")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "create",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P1",
                "value": {"value": "somevalue", "type": "somevalue"},
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tP1\tnovalue")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "create",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P1",
                "value": {"value": "novalue", "type": "novalue"},
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_create_string(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, 'Q1234\tP1\t"this is a string"')
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "create",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P1",
                "value": {"type": "string", "value": "this is a string"},
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_create_monolingualstring(self):
        command = BatchCommand.objects.create_command_from_v1(
            self.batch, 0, 'Q1234\tP10\ten:"this is a string in english"'
        )
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "create",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P10",
                "value": {
                    "type": "monolingualtext",
                    "value": {
                        "language": "en",
                        "text": "this is a string in english",
                    },
                },
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_create_location(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tP10\t@43.26193/10.92708")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "create",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P10",
                "value": {
                    "type": "globecoordinate",
                    "value": {
                        "latitude": 43.26193,
                        "longitude": 10.92708,
                        "precision": 0.000001,
                        "globe": "http://www.wikidata.org/entity/Q2",
                    },
                },
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_create_time(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "Q1234\tP10\t+1967-01-17T00:00:00Z/11")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "create",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P10",
                "value": {
                    "type": "time",
                    "value": {
                        "time": "+1967-01-17T00:00:00Z",
                        "timezone": 0,
                        "before": 0,
                        "after": 0,
                        "precision": 11,
                        "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                    },
                },
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_create_item_with_sources(self):
        command = BatchCommand.objects.create_command_from_v1(
            self.batch, 0, 'Q1234\tP2\tQ1\tS1\t"source text"\tS2\t+1967-01-17T00:00:00Z/11'
        )
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "create",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P2",
                "value": {"type": "wikibase-entityid", "value": {"entity-type": "item", "id": "Q1"}},
                "sources": [
                    {"source": "S1", "value": {"type": "string", "value": "source text"}},
                    {
                        "source": "S2",
                        "value": {
                            "type": "time",
                            "value": {
                                "time": "+1967-01-17T00:00:00Z",
                                "timezone": 0,
                                "before": 0,
                                "after": 0,
                                "precision": 11,
                                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                            },
                        },
                    },
                ],
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_create_item_with_qualifiers(self):
        command = BatchCommand.objects.create_command_from_v1(
            self.batch, 0, 'Q1234\tP2\tQ1\tP1\t"qualifier text"\tP2\t+1970-01-17T00:00:00Z/11'
        )
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "create",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P2",
                "value": {"type": "wikibase-entityid", "value": {"entity-type": "item", "id": "Q1"}},
                "qualifiers": [
                    {"property": "P1", "value": {"type": "string", "value": "qualifier text"}},
                    {
                        "property": "P2",
                        "value": {
                            "type": "time",
                            "value": {
                                "time": "+1970-01-17T00:00:00Z",
                                "timezone": 0,
                                "before": 0,
                                "after": 0,
                                "precision": 11,
                                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                            },
                        },
                    },
                ],
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_create_item_with_qualifiers_and_sources(self):
        command = BatchCommand.objects.create_command_from_v1(
            self.batch, 0, 'Q1234\tP2\tQ1\tS1\t"source text"\tP1\t"qualifier text"\tP2\t+1970-01-17T00:00:00Z/11\tS2\t+1967-01-17T00:00:00Z/11'
        )
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(
            command.json,
            {
                "action": "create",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P2",
                "value": {"type": "wikibase-entityid", "value": {"entity-type": "item", "id": "Q1"}},
                "qualifiers": [
                    {"property": "P1", "value": {"type": "string", "value": "qualifier text"}},
                    {
                        "property": "P2",
                        "value": {
                            "type": "time",
                            "value": {
                                "time": "+1970-01-17T00:00:00Z",
                                "timezone": 0,
                                "before": 0,
                                "after": 0,
                                "precision": 11,
                                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                            },
                        },
                    },
                ],
                "sources": [
                    {"source": "S1", "value": {"type": "string", "value": "source text"}},
                    {
                        "source": "S2",
                        "value": {
                            "type": "time",
                            "value": {
                                "time": "+1967-01-17T00:00:00Z",
                                "timezone": 0,
                                "before": 0,
                                "after": 0,
                                "precision": 11,
                                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                            },
                        },
                    },
                ],
            },
        )
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

    def test_v1_command_with_comment(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "CREATE /* This is a comment. */")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {"action": "create", "type": "item"})
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)

        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "MERGE\tQ1\tQ2 /* This is a comment. */")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {"action": "merge", "type": "item", "item1": "Q1", "item2": "Q2"})
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)
