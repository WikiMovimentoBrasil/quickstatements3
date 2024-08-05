from django.test import TestCase

from core.models import Batch
from core.models import BatchCommand
from core.parsers.v1 import V1CommandParser


class TestV1Parser(TestCase):
    def test_item_valid_id_parser(self):
        parser = V1CommandParser()
        self.assertTrue(parser.is_valid_item_id("Q1"))
        self.assertTrue(parser.is_valid_item_id("Q1234"))
        self.assertTrue(parser.is_valid_item_id("Q1234345523535534545455342545"))
        self.assertTrue(parser.is_valid_item_id("M1"))
        self.assertTrue(parser.is_valid_item_id("M1234"))
        self.assertTrue(parser.is_valid_item_id("M1234345523535534545455342545"))
        self.assertFalse(parser.is_valid_item_id("1"))
        self.assertFalse(parser.is_valid_item_id("12Q1234"))
        self.assertFalse(parser.is_valid_item_id("Q1234m"))
        self.assertFalse(parser.is_valid_item_id("M1A"))
        self.assertFalse(parser.is_valid_item_id("M12A34"))
        self.assertFalse(parser.is_valid_item_id(None))

    def test_property_valid_id_parser(self):
        parser = V1CommandParser()
        self.assertTrue(parser.is_valid_property_id("P1"))
        self.assertTrue(parser.is_valid_property_id("P1234"))
        self.assertTrue(parser.is_valid_property_id("P1234345523535534545455342545"))
        self.assertFalse(parser.is_valid_property_id("1"))
        self.assertFalse(parser.is_valid_property_id("12P1234"))
        self.assertFalse(parser.is_valid_property_id("P1234m"))
        self.assertFalse(parser.is_valid_property_id("M1A"))
        self.assertFalse(parser.is_valid_property_id("M12A34"))
        self.assertFalse(parser.is_valid_property_id(None))

    def test_source_valid_id_parser(self):
        parser = V1CommandParser()
        self.assertTrue(parser.is_valid_source_id("S1"))
        self.assertTrue(parser.is_valid_source_id("S1234"))
        self.assertTrue(parser.is_valid_source_id("S1234345523535534545455342545"))
        self.assertFalse(parser.is_valid_source_id("1"))
        self.assertFalse(parser.is_valid_source_id("12S1234"))
        self.assertFalse(parser.is_valid_source_id("S1234m"))
        self.assertFalse(parser.is_valid_source_id(None))

    def test_lexeme_valid_id_parser(self):
        parser = V1CommandParser()
        self.assertTrue(parser.is_valid_lexeme_id("L1"))
        self.assertTrue(parser.is_valid_lexeme_id("L1234"))
        self.assertTrue(parser.is_valid_lexeme_id("L1234345523535534545455342545"))
        self.assertFalse(parser.is_valid_lexeme_id("1"))
        self.assertFalse(parser.is_valid_lexeme_id("12P1234"))
        self.assertFalse(parser.is_valid_lexeme_id("L1234m"))
        self.assertFalse(parser.is_valid_lexeme_id("L1da123121212"))
        self.assertFalse(parser.is_valid_lexeme_id("M12A34"))
        self.assertFalse(parser.is_valid_lexeme_id(None))

    def test_form_valid_id_parser(self):
        parser = V1CommandParser()
        self.assertTrue(parser.is_valid_form_id("L1-F1"))
        self.assertTrue(parser.is_valid_form_id("L1234-F1234"))
        self.assertFalse(parser.is_valid_form_id("L1234"))
        self.assertFalse(parser.is_valid_form_id("F1234"))
        self.assertFalse(parser.is_valid_form_id(None))

    def test_sense_valid_id_parser(self):
        parser = V1CommandParser()
        self.assertTrue(parser.is_valid_sense_id("L1-S1"))
        self.assertTrue(parser.is_valid_sense_id("L1234-S1234"))
        self.assertFalse(parser.is_valid_sense_id("L1234"))
        self.assertFalse(parser.is_valid_sense_id("S1234"))
        self.assertFalse(parser.is_valid_sense_id(None))

    def test_get_entity_type(self):
        parser = V1CommandParser()
        self.assertEqual(parser.get_entity_type("Q1222132"), "item")
        self.assertEqual(parser.get_entity_type("M1222132"), "item")
        self.assertEqual(parser.get_entity_type("LAST"), "item")
        self.assertEqual(parser.get_entity_type("P1222132"), "property")
        self.assertEqual(parser.get_entity_type("L13131"), "lexeme")
        self.assertEqual(parser.get_entity_type("L1123-F1312313"), "form")
        self.assertEqual(parser.get_entity_type("L1234-S1234"), "sense")
        self.assertIsNone(parser.get_entity_type("adasdsd"))
        self.assertIsNone(parser.get_entity_type(None))
        self.assertIsNone(parser.get_entity_type(""))

    def test_parse_value_somevalue_novalue(self):
        parser = V1CommandParser()
        self.assertEqual(parser.parse_value("somevalue"), {"value": "somevalue", "type": "somevalue"})
        self.assertEqual(parser.parse_value("novalue"), {"value": "novalue", "type": "novalue"})

    def test_parse_value_item(self):
        parser = V1CommandParser()
        self.assertEqual(
            parser.parse_value("LAST"), {"type": "wikibase-entityid", "value": {"entity-type": "item", "id": "LAST"}}
        )
        self.assertEqual(
            parser.parse_value("Q1233"), {"type": "wikibase-entityid", "value": {"entity-type": "item", "id": "Q1233"}}
        )
        self.assertEqual(
            parser.parse_value("M1233"), {"type": "wikibase-entityid", "value": {"entity-type": "item", "id": "M1233"}}
        )

    def test_parse_value_string(self):
        parser = V1CommandParser()
        self.assertEqual(parser.parse_value('"this is a string"'), {"type": "string", "value": "this is a string"})
        self.assertIsNone(parser.parse_value("not a string"))
        self.assertIsNone(parser.parse_value("'this is a string'"))

    def test_parse_value_monolingual_string(self):
        parser = V1CommandParser()
        self.assertEqual(
            parser.parse_value('en:"this is string in english"'),
            {
                "type": "monolingualtext",
                "value": {
                    "language": "en",
                    "text": "this is string in english",
                },
            },
        )
        self.assertEqual(
            parser.parse_value('pt:"este é um texto em português"'),
            {
                "type": "monolingualtext",
                "value": {
                    "language": "pt",
                    "text": "este é um texto em português",
                },
            },
        )
        self.assertIsNone(parser.parse_value("en:'this is not a monolingualtext'"))

    def test_parse_value_time(self):
        parser = V1CommandParser()
        ret = {
            "type": "time",
            "value": {
                "time": "+1967-01-17T00:00:00Z",
                "timezone": 0,
                "before": 0,
                "after": 0,
                "precision": 11,
                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
            },
        }
        self.assertEqual(parser.parse_value("+1967-01-17T00:00:00Z/11"), ret)
        ret = {
            "type": "time",
            "value": {
                "time": "+1967-01-00T00:00:00Z",
                "timezone": 0,
                "before": 0,
                "after": 0,
                "precision": 10,
                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
            },
        }
        self.assertEqual(parser.parse_value("+1967-01-00T00:00:00Z/10"), ret)
        ret = {
            "type": "time",
            "value": {
                "time": "+1967-00-00T00:00:00Z",
                "timezone": 0,
                "before": 0,
                "after": 0,
                "precision": 9,
                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
            },
        }
        self.assertEqual(parser.parse_value("+1967-00-00T00:00:00Z/9"), ret)

    def test_parse_value_location(self):
        parser = V1CommandParser()
        ret = {
            "type": "globecoordinate",
            "value": {
                "latitude": 43.26193,
                "longitude": 10.92708,
                "precision": 0.000001,
                "globe": "http://www.wikidata.org/entity/Q2",
            },
        }
        self.assertEqual(parser.parse_value("@43.26193/10.92708"), ret)
        self.assertIsNone(parser.parse_value("@43.26193"))

    def test_parse_value_quantity(self):
        parser = V1CommandParser()
        ret = {"type": "quantity", "value": {"amount": "10"}}
        self.assertEqual(parser.parse_value("10"), ret)
        ret = {"type": "quantity", "value": {"amount": "12"}}
        self.assertEqual(parser.parse_value("12U11573"), ret)
        ret = {
            "type": "quantity",
            "value": {
                "amount": "9",
                "upperBound": 9.1,
                "lowerBound": 8.9,
            },
        }
        self.assertEqual(parser.parse_value("9~0.1"), ret)
        ret = {"type": "quantity", "value": {"amount": "10.3"}}
        self.assertEqual(parser.parse_value("10.3"), ret)
        ret = {"type": "quantity", "value": {"amount": "12.8"}}
        self.assertEqual(parser.parse_value("12.8U11573"), ret)
        ret = {
            "type": "quantity",
            "value": {
                "amount": "9.6",
                "upperBound": 9.7,
                "lowerBound": 9.5,
            },
        }
        self.assertEqual(parser.parse_value("9.6~0.1"), ret)


class TestBatchCommand(TestCase):
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

