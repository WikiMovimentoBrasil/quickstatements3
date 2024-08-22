from django.test import TestCase

from core.parsers.v1 import BaseParser


class TestBaseParser(TestCase):
    def test_item_valid_id_parser(self):
        parser = BaseParser()
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
        parser = BaseParser()
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
        parser = BaseParser()
        self.assertTrue(parser.is_valid_source_id("S1"))
        self.assertTrue(parser.is_valid_source_id("S1234"))
        self.assertTrue(parser.is_valid_source_id("S1234345523535534545455342545"))
        self.assertFalse(parser.is_valid_source_id("1"))
        self.assertFalse(parser.is_valid_source_id("12S1234"))
        self.assertFalse(parser.is_valid_source_id("S1234m"))
        self.assertFalse(parser.is_valid_source_id(None))

    def test_lexeme_valid_id_parser(self):
        parser = BaseParser()
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
        parser = BaseParser()
        self.assertTrue(parser.is_valid_form_id("L1-F1"))
        self.assertTrue(parser.is_valid_form_id("L1234-F1234"))
        self.assertFalse(parser.is_valid_form_id("L1234"))
        self.assertFalse(parser.is_valid_form_id("F1234"))
        self.assertFalse(parser.is_valid_form_id(None))

    def test_sense_valid_id_parser(self):
        parser = BaseParser()
        self.assertTrue(parser.is_valid_sense_id("L1-S1"))
        self.assertTrue(parser.is_valid_sense_id("L1234-S1234"))
        self.assertFalse(parser.is_valid_sense_id("L1234"))
        self.assertFalse(parser.is_valid_sense_id("S1234"))
        self.assertFalse(parser.is_valid_sense_id(None))

    def test_sense_valid_alias_parser(self):
        parser = BaseParser()
        self.assertTrue(parser.is_valid_alias("Aen"))
        self.assertFalse(parser.is_valid_alias("Ae"))
        self.assertFalse(parser.is_valid_alias("Aeadsdasdadasd"))
        self.assertFalse(parser.is_valid_alias("A1212"))
        self.assertFalse(parser.is_valid_alias(None))

    def test_sense_valid_description_parser(self):
        parser = BaseParser()
        self.assertTrue(parser.is_valid_description("Den"))
        self.assertFalse(parser.is_valid_description("De"))
        self.assertFalse(parser.is_valid_description("Deeqweqweqwe"))
        self.assertFalse(parser.is_valid_description("D1212"))
        self.assertFalse(parser.is_valid_description(None))

    def test_sense_valid_label_parser(self):
        parser = BaseParser()
        self.assertTrue(parser.is_valid_label("Len"))
        self.assertFalse(parser.is_valid_label("Le"))
        self.assertFalse(parser.is_valid_label("Lefsfdsfdsf"))
        self.assertFalse(parser.is_valid_label("L1212"))
        self.assertFalse(parser.is_valid_label(None))

    def test_sense_valid_sitelink_parser(self):
        parser = BaseParser()
        self.assertTrue(parser.is_valid_sitelink("Swikibr"))
        self.assertFalse(parser.is_valid_sitelink("S2121212"))
        self.assertFalse(parser.is_valid_sitelink(None))

    def test_get_entity_type(self):
        parser = BaseParser()
        self.assertEqual(parser.get_entity_type("Q1222132"), "item")
        self.assertEqual(parser.get_entity_type("M1222132"), "item")
        self.assertEqual(parser.get_entity_type("LAST"), "item")
        self.assertEqual(parser.get_entity_type("P1222132"), "property")
        self.assertEqual(parser.get_entity_type("L13131"), "lexeme")
        self.assertEqual(parser.get_entity_type("L1123-F1312313"), "form")
        self.assertEqual(parser.get_entity_type("L1234-S1234"), "sense")
        self.assertEqual(parser.get_entity_type("Apt"), "alias")
        self.assertEqual(parser.get_entity_type("Dfr"), "description")
        self.assertEqual(parser.get_entity_type("Len"), "label")
        self.assertEqual(parser.get_entity_type("Swiki"), "sitelink")
        self.assertIsNone(parser.get_entity_type("adasdsd"))
        self.assertIsNone(parser.get_entity_type(None))
        self.assertIsNone(parser.get_entity_type(""))

    def test_parse_value_somevalue_novalue(self):
        parser = BaseParser()
        self.assertEqual(parser.parse_value("somevalue"), {"value": "somevalue", "type": "somevalue"})
        self.assertEqual(parser.parse_value("novalue"), {"value": "novalue", "type": "novalue"})

    def test_parse_value_item(self):
        parser = BaseParser()
        self.assertEqual(parser.parse_value("LAST"), {"type": "wikibase-item", "value": "LAST"})
        self.assertEqual(parser.parse_value("Q1233"), {"type": "wikibase-item", "value": "Q1233"})
        self.assertEqual(parser.parse_value("M1233"), {"type": "wikibase-item", "value": "M1233"})

    def test_parse_value_string(self):
        parser = BaseParser()
        self.assertEqual(parser.parse_value('"this is a string"'), {"type": "string", "value": "this is a string"})
        self.assertIsNone(parser.parse_value("not a string"))
        self.assertIsNone(parser.parse_value("'this is a string'"))

    def test_parse_value_monolingual_string(self):
        parser = BaseParser()
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

    def test_parse_url(self):
        parser = BaseParser()
        self.assertEqual(
            parser.parse_value('"""http://google.com"""'),
            {
                "type": "url",
                "value": "http://google.com",
            },
        )
        self.assertEqual(
            parser.parse_value('"""https://wikidata.com"""'),
            {
                "type": "url",
                "value": "https://wikidata.com",
            },
        )

    def test_parse_commons_media(self):
        parser = BaseParser()
        self.assertEqual(
            parser.parse_value('"""Frans Breydel - A merry company.jpg"""'),
            {
                "type": "commonsMedia",
                "value": "Frans Breydel - A merry company.jpg",
            },
        )
        self.assertEqual(
            parser.parse_value('"""\'Girl Reading\' by Mary Colman Wheeler, El Paso Museum of Art.JPG"""'),
            {
                "type": "commonsMedia",
                "value": "'Girl Reading' by Mary Colman Wheeler, El Paso Museum of Art.JPG",
            },
        )

    def test_parse_external_id(self):
        parser = BaseParser()
        self.assertEqual(
            parser.parse_value('"""Sandbox"""'),
            {
                "type": "external-id",
                "value": "Sandbox",
            },
        )
        self.assertEqual(
            parser.parse_value('"""Patterns, Predictors, and Outcome"""'),
            {
                "type": "external-id",
                "value": "Patterns, Predictors, and Outcome",
            },
        )

    def test_parse_value_time(self):
        parser = BaseParser()
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
        parser = BaseParser()
        ret = {
            "type": "globecoordinate",
            "value": {
                "latitude": "43.26193",
                "longitude": "10.92708",
                "precision": "0.000001",
                "globe": "http://www.wikidata.org/entity/Q2",
            },
        }
        self.assertEqual(parser.parse_value("@43.26193/10.92708"), ret)
        self.assertIsNone(parser.parse_value("@43.26193"))

    def test_parse_value_quantity(self):
        parser = BaseParser()
        ret = {"type": "quantity", "value": {"amount": "10", "unit": "1"}}
        self.assertEqual(parser.parse_value("10"), ret)
        
        ret = {"type": "quantity", "value": {"amount": "12", "unit": "11573"}}
        self.assertEqual(parser.parse_value("12U11573"), ret)
        
        ret = {
            "type": "quantity",
            "value": {"amount": "9", "upperBound": "9.1", "lowerBound": "8.9", "unit": "1"},
        }
        self.assertEqual(parser.parse_value("9~0.1"), ret)
        
        ret = {"type": "quantity", "value": {"amount": "10.3", "unit": "1"}}
        self.assertEqual(parser.parse_value("10.3"), ret)

        ret = {"type": "quantity", "value": {"amount": "12.8", "unit": "11573"}}
        self.assertEqual(parser.parse_value("12.8U11573"), ret)
        
        ret = {
            "type": "quantity",
            "value": {"amount": "9.6", "upperBound": "9.7", "lowerBound": "9.5", "unit": "1"},
        }
        self.assertEqual(parser.parse_value("9.6~0.1"), ret)
