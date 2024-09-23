from django.test import TestCase

from core.models import Batch
from core.models import BatchCommand
from core.parsers.v1 import V1CommandParser
from core.parsers.csv import CSVCommandParser


class TestBatch(TestCase):
    def test_batch_is_running(self):
        batch = Batch.objects.create(name="teste")
        self.assertFalse(batch.is_running)
        batch.status = Batch.STATUS_BLOCKED
        batch.save()
        self.assertFalse(batch.is_running)
        batch.status = Batch.STATUS_STOPPED
        batch.save()
        self.assertFalse(batch.is_running)
        batch.status = Batch.STATUS_DONE
        batch.save()
        self.assertFalse(batch.is_running)
        batch.status = Batch.STATUS_RUNNING
        batch.save()
        self.assertTrue(batch.is_running)

    def test_batch_is_stopped(self):
        batch = Batch.objects.create(name="teste")
        self.assertFalse(batch.is_running)
        batch.status = Batch.STATUS_BLOCKED
        batch.save()
        self.assertFalse(batch.is_stopped)
        batch.status = Batch.STATUS_STOPPED
        batch.save()
        self.assertTrue(batch.is_stopped)
        batch.status = Batch.STATUS_DONE
        batch.save()
        self.assertFalse(batch.is_stopped)
        batch.status = Batch.STATUS_RUNNING
        batch.save()
        self.assertFalse(batch.is_stopped)

    def test_batch_is_initial(self):
        batch = Batch.objects.create(name="teste")
        self.assertTrue(batch.is_initial)
        batch.status = Batch.STATUS_BLOCKED
        batch.save()
        self.assertFalse(batch.is_initial)
        batch.status = Batch.STATUS_STOPPED
        batch.save()
        self.assertFalse(batch.is_initial)
        batch.status = Batch.STATUS_DONE
        batch.save()
        self.assertFalse(batch.is_initial)
        batch.status = Batch.STATUS_RUNNING
        batch.save()
        self.assertFalse(batch.is_stopped)

    def test_batch_stop(self):
        batch = Batch.objects.create(name="teste")
        self.assertFalse(batch.is_stopped)
        batch.stop()
        self.assertTrue(batch.is_stopped)
        self.assertTrue(batch.message.startswith("Batch stopped processing by owner at"))

    def test_batch_restart(self):
        batch = Batch.objects.create(name="teste", status=Batch.STATUS_BLOCKED)
        batch.restart()
        self.assertFalse(batch.is_initial)
        batch.status = Batch.STATUS_RUNNING
        batch.save()
        batch.restart()
        self.assertFalse(batch.is_initial)
        batch.status = Batch.STATUS_DONE
        batch.save()
        batch.restart()
        self.assertFalse(batch.is_initial)
        batch.status = Batch.STATUS_STOPPED
        batch.save()
        batch.restart()
        self.assertTrue(batch.is_initial)      
        self.assertTrue(batch.message.startswith("Batch restarted by owner"))  


class TestV1Batch(TestCase):
    def test_v1_correct_create_command(self):
        v1 = V1CommandParser()
        self.assertFalse(Batch.objects.count())
        self.assertFalse(BatchCommand.objects.count())
        batch = v1.parse("My batch", "myuser", "CREATE||-Q1234|P1|12||Q222|P4|9~0.1")
        self.assertEqual(batch.user, "myuser")
        self.assertEqual(batch.name, "My batch")
        self.assertEqual(BatchCommand.objects.count(), 3)
        self.assertEqual(BatchCommand.objects.filter(batch=batch).count(), 3)
        bc1 = BatchCommand.objects.get(batch=batch, index=0)
        self.assertEqual(bc1.raw, "CREATE")
        bc2 = BatchCommand.objects.get(batch=batch, index=1)
        self.assertEqual(bc2.raw, "-Q1234\tP1\t12")
        bc3 = BatchCommand.objects.get(batch=batch, index=2)
        self.assertEqual(bc3.raw, "Q222\tP4\t9~0.1")


class TestCSVBatch(TestCase):
    def test_create_property(self):
        COMMAND = """qid,Len,Den,P31
,Regina Phalange,fictional character,Q95074"""

        self.assertFalse(Batch.objects.count())
        self.assertFalse(BatchCommand.objects.count())

        v1 = CSVCommandParser()
        batch = v1.parse("My batch CREATE", "myuser", COMMAND)
        self.assertEqual(batch.user, "myuser")
        self.assertEqual(batch.name, "My batch CREATE")
        self.assertEqual(BatchCommand.objects.count(), 4)
        self.assertEqual(BatchCommand.objects.filter(batch=batch).count(), 4)
        bc1 = BatchCommand.objects.get(batch=batch, index=0)
        self.assertEqual(bc1.json, {"action": "create", "type": "item"})
        bc2 = BatchCommand.objects.get(batch=batch, index=1)
        self.assertEqual(
            bc2.json,
            {
                "action": "add",
                "what": "label",
                "item": "LAST",
                "language": "en",
                "value": {"type": "string", "value": "Regina Phalange"},
            },
        )
        bc3 = BatchCommand.objects.get(batch=batch, index=2)
        self.assertEqual(
            bc3.json,
            {
                "action": "add",
                "what": "description",
                "item": "LAST",
                "language": "en",
                "value": {"type": "string", "value": "fictional character"},
            },
        )
        bc4 = BatchCommand.objects.get(batch=batch, index=3)
        self.assertEqual(
            bc4.json,
            {
                "action": "add",
                "what": "statement",
                "entity": {"type": "item", "id": "LAST"},
                "property": "P31",
                "value": {"type": "wikibase-item", "value": "Q95074"},
            },
        )

    def test_add_and_remove_property(self):
        COMMAND = """qid,P31,-P31
Q4115189,Q5,Q5"""

        self.assertFalse(Batch.objects.count())
        self.assertFalse(BatchCommand.objects.count())

        v1 = CSVCommandParser()
        batch = v1.parse("My batch CREATE REMOVE", "myuser", COMMAND)
        self.assertEqual(batch.user, "myuser")
        self.assertEqual(batch.name, "My batch CREATE REMOVE")
        self.assertEqual(BatchCommand.objects.count(), 2)
        self.assertEqual(BatchCommand.objects.filter(batch=batch).count(), 2)
        bc1 = BatchCommand.objects.get(batch=batch, index=0)
        self.assertEqual(
            bc1.json,
            {
                "action": "add",
                "entity": {"id": "Q4115189", "type": "item"},
                "property": "P31",
                "value": {"type": "wikibase-item", "value": "Q5"},
                "what": "statement",
            },
        )
        bc2 = BatchCommand.objects.get(batch=batch, index=1)
        self.assertEqual(
            bc2.json,
            {
                "action": "remove",
                "entity": {"id": "Q4115189", "type": "item"},
                "property": "P31",
                "value": {"type": "wikibase-item", "value": "Q5"},
                "what": "statement",
            },
        )

    def test_add_property(self):
        COMMAND = """qid,P369
Q4115189,Q5
Q4115189,somevalue
Q4115189,novalue
L123,Q5
L123-S1,Q5
L123-F1,Q5"""

        self.assertFalse(Batch.objects.count())
        self.assertFalse(BatchCommand.objects.count())

        v1 = CSVCommandParser()
        batch = v1.parse("My batch 1", "myuser", COMMAND)
        self.assertEqual(batch.user, "myuser")
        self.assertEqual(batch.name, "My batch 1")
        self.assertEqual(BatchCommand.objects.count(), 6)
        self.assertEqual(BatchCommand.objects.filter(batch=batch).count(), 6)
        bc1 = BatchCommand.objects.get(batch=batch, index=0)
        self.assertEqual(
            bc1.json,
            {
                "action": "add",
                "entity": {"id": "Q4115189", "type": "item"},
                "property": "P369",
                "value": {"type": "wikibase-item", "value": "Q5"},
                "what": "statement",
            },
        )
        bc2 = BatchCommand.objects.get(batch=batch, index=1)
        self.assertEqual(
            bc2.json,
            {
                "action": "add",
                "entity": {"id": "Q4115189", "type": "item"},
                "property": "P369",
                "value": {"type": "somevalue", "value": "somevalue"},
                "what": "statement",
            },
        )
        bc3 = BatchCommand.objects.get(batch=batch, index=2)
        self.assertEqual(
            bc3.json,
            {
                "action": "add",
                "entity": {"id": "Q4115189", "type": "item"},
                "property": "P369",
                "value": {"type": "novalue", "value": "novalue"},
                "what": "statement",
            },
        )
        bc4 = BatchCommand.objects.get(batch=batch, index=3)
        self.assertEqual(
            bc4.json,
            {
                "action": "add",
                "entity": {"id": "L123", "type": "lexeme"},
                "property": "P369",
                "value": {"type": "wikibase-item", "value": "Q5"},
                "what": "statement",
            },
        )
        bc5 = BatchCommand.objects.get(batch=batch, index=4)
        self.assertEqual(
            bc5.json,
            {
                "action": "add",
                "entity": {"id": "L123-S1", "type": "sense"},
                "property": "P369",
                "value": {"type": "wikibase-item", "value": "Q5"},
                "what": "statement",
            },
        )
        bc6 = BatchCommand.objects.get(batch=batch, index=5)
        self.assertEqual(
            bc6.json,
            {
                "action": "add",
                "entity": {"id": "L123-F1", "type": "form"},
                "property": "P369",
                "value": {"type": "wikibase-item", "value": "Q5"},
                "what": "statement",
            },
        )

    def test_add_label(self):
        COMMAND = """qid,Len
Q4115189,Sandbox
Q4115189,"Patterns, Predictors, and Outcome"
"""

        self.assertFalse(Batch.objects.count())
        self.assertFalse(BatchCommand.objects.count())

        v1 = CSVCommandParser()
        batch = v1.parse("My batch LABEL", "myuser", COMMAND)
        self.assertEqual(batch.user, "myuser")
        self.assertEqual(batch.name, "My batch LABEL")
        self.assertEqual(BatchCommand.objects.count(), 2)
        self.assertEqual(BatchCommand.objects.filter(batch=batch).count(), 2)
        bc1 = BatchCommand.objects.get(batch=batch, index=0)
        self.assertEqual(
            bc1.json,
            {
                "action": "add",
                "item": "Q4115189",
                "value": {"type": "string", "value": "Sandbox"},
                "what": "label",
                "language": "en",
            },
        )
        bc2 = BatchCommand.objects.get(batch=batch, index=1)
        self.assertEqual(
            bc2.json,
            {
                "action": "add",
                "item": "Q4115189",
                "value": {"type": "string", "value": "Patterns, Predictors, and Outcome"},
                "what": "label",
                "language": "en",
            },
        )

    def test_add_alias(self):
        COMMAND = """qid,Apt
Q411518,Sandbox 3
Q411518,"Patterns, Predictors, and Outcome and Questions"
"""

        self.assertFalse(Batch.objects.count())
        self.assertFalse(BatchCommand.objects.count())

        v1 = CSVCommandParser()
        batch = v1.parse("My batch ALIAS", "myuser", COMMAND)
        self.assertEqual(batch.user, "myuser")
        self.assertEqual(batch.name, "My batch ALIAS")
        self.assertEqual(BatchCommand.objects.count(), 2)
        self.assertEqual(BatchCommand.objects.filter(batch=batch).count(), 2)
        bc1 = BatchCommand.objects.get(batch=batch, index=0)
        self.assertEqual(
            bc1.json,
            {
                "action": "add",
                "item": "Q411518",
                "value": {"type": "string", "value": "Sandbox 3"},
                "what": "alias",
                "language": "pt",
            },
        )
        bc2 = BatchCommand.objects.get(batch=batch, index=1)
        self.assertEqual(
            bc2.json,
            {
                "action": "add",
                "item": "Q411518",
                "value": {"type": "string", "value": "Patterns, Predictors, and Outcome and Questions"},
                "what": "alias",
                "language": "pt",
            },
        )

    def test_add_description(self):
        COMMAND = """qid,Dpt
Q411518,Sandbox Description
Q411518,"Patterns, Predictors, and Outcome and Descriptions"
"""

        self.assertFalse(Batch.objects.count())
        self.assertFalse(BatchCommand.objects.count())

        v1 = CSVCommandParser()
        batch = v1.parse("My batch DESCRIPTION", "myuser", COMMAND)
        self.assertEqual(batch.user, "myuser")
        self.assertEqual(batch.name, "My batch DESCRIPTION")
        self.assertEqual(BatchCommand.objects.count(), 2)
        self.assertEqual(BatchCommand.objects.filter(batch=batch).count(), 2)
        bc1 = BatchCommand.objects.get(batch=batch, index=0)
        self.assertEqual(
            bc1.json,
            {
                "action": "add",
                "item": "Q411518",
                "value": {"type": "string", "value": "Sandbox Description"},
                "what": "description",
                "language": "pt",
            },
        )
        bc2 = BatchCommand.objects.get(batch=batch, index=1)
        self.assertEqual(
            bc2.json,
            {
                "action": "add",
                "item": "Q411518",
                "value": {"type": "string", "value": "Patterns, Predictors, and Outcome and Descriptions"},
                "what": "description",
                "language": "pt",
            },
        )

    def test_full_command(self):
        COMMAND = """qid,Len,Den,Aen,P31,-P31,P21,P735,qal1545,S248,s214,S143,Senwiki
Q4115189,Douglas Adams,author,Douglas Noël Adams,Q5,Q36180,Q6581097,Q463035,\"\"\"1\"\"\",Q54919,\"\"\"113230702\"\"\",Q328,Douglas Adams
"""
        self.maxDiff = None

        self.assertFalse(Batch.objects.count())
        self.assertFalse(BatchCommand.objects.count())

        v1 = CSVCommandParser()
        batch = v1.parse("My batch DESCRIPTION", "myuser", COMMAND)
        self.assertEqual(batch.user, "myuser")
        self.assertEqual(batch.name, "My batch DESCRIPTION")
        self.assertEqual(BatchCommand.objects.count(), 8)
        self.assertEqual(BatchCommand.objects.filter(batch=batch).count(), 8)
        
        bc0 = BatchCommand.objects.get(batch=batch, index=0)
        self.assertEqual(bc0.json,
            {
                "action": "add",
                "item": "Q4115189",
                "value": {"type": "string", "value": "Douglas Adams"},
                "what": "label",
                "language": "en",
            }
        )

        bc1 = BatchCommand.objects.get(batch=batch, index=1)
        self.assertEqual(bc1.json,
            {
                "action": "add",
                "item": "Q4115189",
                "value": {"type": "string", "value": "author"},
                "what": "description",
                "language": "en",
            }
        )

        bc2 = BatchCommand.objects.get(batch=batch, index=2)
        self.assertEqual(bc2.json,
            {
                "action": "add",
                "item": "Q4115189",
                "value": {"type": "string", "value": "Douglas Noël Adams"},
                "what": "alias",
                "language": "en",
            }
        )

        bc3 = BatchCommand.objects.get(batch=batch, index=3)
        self.assertEqual(bc3.json,
            {
                "action": "add",
                "entity": {"id": "Q4115189", "type": "item"},
                "property": "P31",
                "value": {"type": "wikibase-item", "value": "Q5"},
                "what": "statement",
            }
        )

        bc4 = BatchCommand.objects.get(batch=batch, index=4)
        self.assertEqual(bc4.json,
            {
                "action": "remove",
                "entity": {"id": "Q4115189", "type": "item"},
                "property": "P31",
                "value": {"type": "wikibase-item", "value": "Q36180"},
                "what": "statement",
            }
        )

        bc5 = BatchCommand.objects.get(batch=batch, index=5)
        self.assertEqual(bc5.json,
            {
                "action": "add",
                "entity": {"id": "Q4115189", "type": "item"},
                "property": "P21",
                "value": {"type": "wikibase-item", "value": "Q6581097"},
                "what": "statement",
            }
        )

        bc6 = BatchCommand.objects.get(batch=batch, index=6)
        self.assertEqual(bc6.json,
            {
                "action": "add",
                "entity": {"id": "Q4115189", "type": "item"},
                "property": "P735",
                "value": {"type": "wikibase-item", "value": "Q463035"},
                "what": "statement",
                "qualifiers": [
                    {
                        "property": "P1545", 
                        "value": {'type': 'string','value': '1'}
                    }
                ],
                "references": [
                    [
                        {
                            "property": "P248", 
                            "value": {"type": "wikibase-item", "value": "Q54919"}
                        },
                        {
                            "property": "P214",
                            "value": {"type": "string", "value": "113230702"}
                        },
                    ],
                    [
                        {
                            "property": "P143", 
                            "value": {"type": "wikibase-item", "value": "Q328"}
                        }
                    ]
                ]
            }
        )

        bc7 = BatchCommand.objects.get(batch=batch, index=7)
        self.assertEqual(bc7.json,
            {
                "action": "add",
                "item": "Q4115189",
                "value": {"type": "string", "value": "Douglas Adams"},
                "what": "sitelink",
                "site": "enwiki"
            }
        )


