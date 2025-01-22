import copy
from django.test import TestCase
from django.contrib.auth.models import User

from core.parsers.v1 import V1CommandParser
from web.models import Token


class RemoveQualRefTests(TestCase):
    INITIAL: dict = {
        "type": "item",
        "id": "Q12345678",
        "labels": {},
        "descriptions": {},
        "aliases": {},
        "statements": {
            "P65": [
                {
                    "id": "Q12345678$FD9DA04C-1967-4949-92FF-BD8405BCE4D9",
                    "rank": "preferred",
                    "qualifiers": [
                        {
                            "property": {"id": "P65", "data_type": "quantity"},
                            "value": {
                                "type": "value",
                                "content": {"amount": "+84", "unit": "1"},
                            },
                        },
                        {
                            "property": {"id": "P84267", "data_type": "quantity"},
                            "value": {
                                "type": "value",
                                "content": {"amount": "-5", "unit": "1"},
                            },
                        },
                    ],
                    "references": [],
                    "property": {"id": "P65", "data_type": "quantity"},
                    "value": {
                        "type": "value",
                        "content": {"amount": "+42", "unit": "1"},
                    },
                }
            ],
            "P31": [
                {
                    "id": "Q238107$96026FB3-7D84-48E3-8C64-6D2E2D033B7E",
                    "rank": "normal",
                    "qualifiers": [
                        {
                            "property": {"id": "P18", "data_type": "time"},
                            "value": {
                                "type": "value",
                                "content": {
                                    "time": "+2025-01-15T00:00:00Z",
                                    "precision": 11,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                },
                            },
                        }
                    ],
                    "references": [
                        {
                            "hash": "95cc6e523b528da734a9cfdcb25c79f5a423cefe",
                            "parts": [
                                {
                                    "property": {"id": "P93", "data_type": "url"},
                                    "value": {
                                        "type": "value",
                                        "content": "https://kernel.org/",
                                    },
                                },
                                {
                                    "property": {
                                        "id": "P84267",
                                        "data_type": "quantity",
                                    },
                                    "value": {
                                        "type": "value",
                                        "content": {"amount": "+42", "unit": "1"},
                                    },
                                },
                            ],
                        },
                        {
                            "hash": "71a764a610caa3ea6161dfee9115a682945223c7",
                            "parts": [
                                {
                                    "property": {"id": "P93", "data_type": "url"},
                                    "value": {
                                        "type": "value",
                                        "content": "https://www.mediawiki.org/",
                                    },
                                },
                                {
                                    "property": {"id": "P74", "data_type": "time"},
                                    "value": {
                                        "type": "value",
                                        "content": {
                                            "time": "+1980-10-21T00:00:00Z",
                                            "precision": 11,
                                            "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                        },
                                    },
                                },
                            ],
                        },
                    ],
                    "property": {"id": "P31", "data_type": "url"},
                    "value": {"type": "somevalue"},
                }
            ],
        },
        "sitelinks": {},
    }

    def parse(self, text):
        v1 = V1CommandParser()
        batch = v1.parse("Test", "user", text)
        batch.save_batch_and_preview_commands()
        return batch

    def assertQualCount(self, entity: dict, property_id: str, length: int, i: int = 0):
        quals = entity["statements"][property_id][i]["qualifiers"]
        self.assertEqual(len(quals), length)

    def assertRefCount(self, entity: dict, property_id: str, length: int, i: int = 0):
        refs = entity["statements"][property_id][i]["references"]
        self.assertEqual(len(refs), length)

    def assertRefPartsCount(
        self, entity: dict, pid: str, length: int, i: int = 0, ipart: int = 0
    ):
        parts = entity["statements"][pid][i]["references"][ipart]["parts"]
        self.assertEqual(len(parts), length)

    # -----
    # TESTS
    # -----

    def test_remove_qualifier(self):
        text = """REMOVE_QUAL|Q12345678|P65|42|P84267|-5
        REMOVE_QUAL|Q12345678|P31|somevalue|P18|+2025-01-15T00:00:00Z/11"""
        batch = self.parse(text)
        entity = copy.deepcopy(self.INITIAL)
        # -----
        remove_p65_qual = batch.commands()[0]
        self.assertQualCount(entity, "P65", 2)
        remove_p65_qual.update_entity_json(entity)
        self.assertQualCount(entity, "P65", 1)
        self.assertEqual(
            entity["statements"]["P65"][0]["qualifiers"][0]["property"]["id"], "P65"
        )
        # -----
        remove_p31_qual = batch.commands()[1]
        self.assertQualCount(entity, "P31", 1)
        remove_p31_qual.update_entity_json(entity)
        self.assertQualCount(entity, "P31", 0)

    def test_remove_reference(self):
        text = """REMOVE_REF|Q12345678|P65|42|S31|somevalue
        REMOVE_REF|Q12345678|P31|somevalue|S93|"https://www.mediawiki.org/" """
        batch = self.parse(text)
        entity = copy.deepcopy(self.INITIAL)
        # -----
        remove_nothing = batch.commands()[0]
        self.assertRefCount(entity, "P65", 0)
        remove_nothing.update_entity_json(entity)
        self.assertRefCount(entity, "P65", 0)
        # -----
        remove_part_mediawiki = batch.commands()[1]
        self.assertRefCount(entity, "P31", 2)
        self.assertRefPartsCount(entity, "P31", 2, ipart=0)
        self.assertRefPartsCount(entity, "P31", 2, ipart=1)
        remove_part_mediawiki.update_entity_json(entity)
        self.assertRefCount(entity, "P31", 2)
        self.assertRefPartsCount(entity, "P31", 2, ipart=0)
        self.assertRefPartsCount(entity, "P31", 1, ipart=1)
        prop = entity["statements"]["P31"][0]["references"][1]["parts"][0]["property"]
        self.assertEqual(prop["id"], "P74")
