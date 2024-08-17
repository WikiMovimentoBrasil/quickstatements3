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

