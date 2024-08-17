from django.test import TestCase

from core.models import Batch
from core.models import BatchCommand
from core.parsers.v1 import V1CommandParser


class TestV1Parser(TestCase):
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

 


