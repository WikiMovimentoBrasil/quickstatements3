from django.test import TestCase

from core.models import Batch
from core.models import BatchCommand
from core.parsers.v1 import V1CommandParser


class TestV1ParserCommand(TestCase):
    def test_v1_correct_create_command(self):
        parser = V1CommandParser()
        data = parser.parse_command("CREATE")
        self.assertEqual(data, {"action": "create", "type": "item"})
        data = parser.parse_command("CREATE ")
        self.assertEqual(data, {"action": "create", "type": "item"})
        data = parser.parse_command(" CREATE ")
        self.assertEqual(data, {"action": "create", "type": "item"})

    def test_v1_bad_create_command(self):
        parser = V1CommandParser()
        with self.assertRaises(Exception) as context:
            data = parser.parse_command("CREATE\tQ123\t")
        self.assertEqual(context.exception.message, "CREATE command can have only 1 column")

    def test_v1_correct_merge_command(self):
        parser = V1CommandParser()
        data = parser.parse_command("MERGE\tQ2\tQ1")
        self.assertEqual(data, {"action": "merge", "type": "item", "item1": "Q1", "item2": "Q2"})
        data = parser.parse_command("MERGE \tQ1 \tQ2 ")
        self.assertEqual(data, {"action": "merge", "type": "item", "item1": "Q1", "item2": "Q2"})

    def test_v1_bad_merge_command(self):
        parser = V1CommandParser()
        with self.assertRaises(Exception) as context:
            data = parser.parse_command("MERGE")
        self.assertEqual(context.exception.message, "MERGE command must have 3 columns")
        with self.assertRaises(Exception) as context:
            data = parser.parse_command("MERGE\tQ1")
        self.assertEqual(context.exception.message, "MERGE command must have 3 columns")
        with self.assertRaises(Exception) as context:
            data = parser.parse_command("MERGE\tQ1\t")
        self.assertEqual(context.exception.message, "MERGE items wrong format item1=[Q1] item2=[]")
        with self.assertRaises(Exception) as context:
            data = parser.parse_command("MERGE\tQ1\tQ2\tQ3")
        self.assertEqual(context.exception.message, "MERGE command must have 3 columns")

    def test_v1_remove_item(self):
        parser = V1CommandParser()
        data = parser.parse_command("-Q1234\tP2\tQ1")
        self.assertEqual(
            data,
            {
                "action": "remove",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P2",
                "value": {"type": "wikibase-item", "value": "Q1"},
                "what": "statement",
            },
        )

    def test_v1_remove_quantity(self):
        parser = V1CommandParser()
        data = parser.parse_command("-Q1234\tP1\t12")
        self.assertEqual(
            data,
            {
                "action": "remove",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P1",
                "value": {"type": "quantity", "value": {"amount": "12", "unit": "1"}},
                "what": "statement",
            },
        )

        data = parser.parse_command("-Q1234\tP3\t12U11573")
        self.assertEqual(
            data,
            {
                "action": "remove",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P3",
                "value": {"type": "quantity", "value": {"amount": "12", "unit": "11573"}},
                "what": "statement",
            },
        )

        data = parser.parse_command("-Q1234\tP4\t9~0.1")
        self.assertEqual(
            data,
            {
                "action": "remove",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P4",
                "value": {
                    "type": "quantity",
                    "value": {"amount": "9", "upperBound": "9.1", "lowerBound": "8.9", "unit": "1"},
                },
                "what": "statement",
            },
        )

    def test_v1_add_item(self):
        parser = V1CommandParser()
        data = parser.parse_command("Q1234\tP2\tQ1")
        self.assertEqual(
            data,
            {
                "action": "add",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P2",
                "value": {"type": "wikibase-item", "value": "Q1"},
                "what": "statement",
            },
        )

    def test_v1_add_quantity(self):
        parser = V1CommandParser()
        data = parser.parse_command("Q1234\tP1\t12")
        self.assertEqual(
            data,
            {
                "action": "add",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P1",
                "value": {"type": "quantity", "value": {"amount": "12", "unit": "1"}},
                "what": "statement",
            },
        )

        data = parser.parse_command("Q1234\tP3\t12U11573")
        self.assertEqual(
            data,
            {
                "action": "add",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P3",
                "value": {"type": "quantity", "value": {"amount": "12", "unit": "11573"}},
                "what": "statement",
            },
        )

        data = parser.parse_command("Q1234\tP4\t9~0.1")
        self.assertEqual(
            data,
            {
                "action": "add",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P4",
                "value": {
                    "type": "quantity",
                    "value": {"amount": "9", "upperBound": "9.1", "lowerBound": "8.9", "unit": "1"},
                },
                "what": "statement",
            },
        )

    def test_v1_add_alias(self):
        parser = V1CommandParser()

        data = parser.parse_command('Q1234\tApt\t"Texto brasileiro"')
        self.assertEqual(
            data,
            {
                "action": "add",
                "what": "alias",
                "item": "Q1234",
                "language": "pt",
                "value": {"type": "string", "value": "Texto brasileiro"},
            },
        )

    def test_v1_add_wrong_alias(self):
        parser = V1CommandParser()
        with self.assertRaises(Exception) as context:
            data = parser.parse_command("Q1234\tApt\tsomevalue")
        self.assertEqual(context.exception.message, "alias must be a string instance")

    def test_v1_add_description(self):
        parser = V1CommandParser()
        data = parser.parse_command('Q1234\tDen\t"Item description"')
        self.assertEqual(
            data,
            {
                "action": "add",
                "what": "description",
                "item": "Q1234",
                "language": "en",
                "value": {"type": "string", "value": "Item description"},
            },
        )

    def test_v1_add_wrong_description(self):
        parser = V1CommandParser()
        with self.assertRaises(Exception) as context:
            data = parser.parse_command("Q1234\tDpt\tsomevalue")
        self.assertEqual(context.exception.message, "description must be a string instance")

    def test_v1_add_label(self):
        parser = V1CommandParser()
        data = parser.parse_command('Q1234\tLfr\t"Note en français"')
        self.assertEqual(
            data,
            {
                "action": "add",
                "what": "label",
                "item": "Q1234",
                "language": "fr",
                "value": {"type": "string", "value": "Note en français"},
            },
        )

    def test_v1_add_wrong_label(self):
        parser = V1CommandParser()
        with self.assertRaises(Exception) as context:
            data = parser.parse_command("Q1234\tLpt\tbla")
        self.assertEqual(context.exception.message, "label must be a string instance")

    def test_v1_add_site(self):
        parser = V1CommandParser()
        data = parser.parse_command('Q1234\tSmysite\t"Site mysite"')
        self.assertEqual(
            data,
            {
                "action": "add",
                "what": "sitelink",
                "item": "Q1234",
                "site": "mysite",
                "value": {"type": "string", "value": "Site mysite"},
            },
        )

    def test_v1_add_wrong_site(self):
        parser = V1CommandParser()
        with self.assertRaises(Exception) as context:
            data = parser.parse_command("Q1234\tSpt\tsomevalue")
        self.assertEqual(context.exception.message, "sitelink must be a string instance")

    def test_v1_add_somevalue_novalue(self):
        parser = V1CommandParser()
        data = parser.parse_command("Q1234\tP1\tsomevalue")
        self.assertEqual(
            data,
            {
                "action": "add",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P1",
                "value": {"value": "somevalue", "type": "somevalue"},
                "what": "statement",
            },
        )

        data = parser.parse_command("Q1234\tP1\tnovalue")
        self.assertEqual(
            data,
            {
                "action": "add",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P1",
                "value": {"value": "novalue", "type": "novalue"},
                "what": "statement",
            },
        )

    def test_v1_add_string(self):
        parser = V1CommandParser()
        data = parser.parse_command('Q1234\tP1\t"this is a string"')
        self.assertEqual(
            data,
            {
                "action": "add",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P1",
                "value": {"type": "string", "value": "this is a string"},
                "what": "statement",
            },
        )

    def test_v1_add_monolingualstring(self):
        parser = V1CommandParser()
        data = parser.parse_command('Q1234\tP10\ten:"this is a string in english"')
        self.assertEqual(
            data,
            {
                "action": "add",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P10",
                "value": {
                    "type": "monolingualtext",
                    "value": {
                        "language": "en",
                        "text": "this is a string in english",
                    },
                },
                "what": "statement",
            },
        )

    def test_v1_add_location(self):
        parser = V1CommandParser()
        data = parser.parse_command("Q1234\tP10\t@43.26193/10.92708")
        self.assertEqual(
            data,
            {
                "action": "add",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P10",
                "value": {
                    "type": "globecoordinate",
                    "value": {
                        "latitude": "43.26193",
                        "longitude": "10.92708",
                        "precision": "0.000001",
                        "globe": "http://www.wikidata.org/entity/Q2",
                    },
                },
                "what": "statement",
            },
        )

    def test_v1_add_time(self):
        parser = V1CommandParser()
        data = parser.parse_command("Q1234\tP10\t+1967-01-17T00:00:00Z/11")
        self.assertEqual(
            data,
            {
                "action": "add",
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
                "what": "statement",
            },
        )

    def test_v1_add_item_with_references(self):
        parser = V1CommandParser()
        data = parser.parse_command('Q1234\tP2\tQ1\tS1\t"source text"\tS2\t+1967-01-17T00:00:00Z/11')
        self.assertEqual(
            data,
            {
                "action": "add",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P2",
                "value": {"type": "wikibase-item", "value": "Q1"},
                "references": [
                    [
                        {"property": "P1", "value": {"type": "string", "value": "source text"}},
                        {
                            "property": "P2",
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
                        }
                    ]
                ],
                "what": "statement",
            },
        )

    def test_v1_add_item_with_references_multiple_blocks(self):
        parser = V1CommandParser()
        data = parser.parse_command('Q1234\tP2\tQ1\tS1\t"source text"\t!S2\t+1967-01-17T00:00:00Z/11')
        self.assertEqual(
            data,
            {
                "action": "add",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P2",
                "value": {"type": "wikibase-item", "value": "Q1"},
                "references": [
                    [
                        {
                            "property": "P1", 
                            "value": {
                                "type": "string", 
                                "value": "source text"
                            }
                        },
                    ],
                    [
                        {
                            "property": "P2",
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
                        }
                    ]
                ],
                "what": "statement",
            },
        )

    def test_v1_add_item_with_qualifiers(self):
        parser = V1CommandParser()
        data = parser.parse_command('Q1234\tP2\tQ1\tP1\t"qualifier text"\tP2\t+1970-01-17T00:00:00Z/11')
        self.assertEqual(
            data,
            {
                "action": "add",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P2",
                "value": {"type": "wikibase-item", "value": "Q1"},
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
                "what": "statement",
            },
        )

    def test_v1_add_item_with_qualifiers_and_references(self):
        parser = V1CommandParser()
        data = parser.parse_command(
            'Q1234\tP2\tQ1\tS1\t"source text"\tP1\t"qualifier text"\tP2\t+1970-01-17T00:00:00Z/11\tS2\t+1967-01-17T00:00:00Z/11'
        )
        self.assertEqual(
            data,
            {
                "action": "add",
                "entity": {"type": "item", "id": "Q1234"},
                "property": "P2",
                "value": {"type": "wikibase-item", "value": "Q1"},
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
                "references": [
                    [
                        {"property": "P1", "value": {"type": "string", "value": "source text"}},
                        {
                            "property": "P2",
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
                        }
                    ]
                ],
                "what": "statement",
            },
        )

    def test_v1_command_with_comment(self):
        parser = V1CommandParser()
        data = parser.parse_command("CREATE /* This is a comment. */")
        self.assertEqual(
            data,
            {
                "action": "create",
                "type": "item",
                "summary": "This is a comment.",
            },
        )

        data = parser.parse_command("MERGE\tQ1\tQ2 /* This is a comment. */")
        self.assertEqual(
            data, {"action": "merge", "type": "item", "item1": "Q1", "item2": "Q2", "summary": "This is a comment."}
        )
