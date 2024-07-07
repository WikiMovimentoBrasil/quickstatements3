from django.test import TestCase

from core.models import Batch
from core.models import BatchCommand


class TestBatchCommand(TestCase):
    
    def setUp(self):
        self.batch = Batch.objects.create(name="Batch", user="wikiuser")

    def test_v1_correct_create_command(self):
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "CREATE")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {'action': 'create' , 'type': 'item'})
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "CREATE ")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {'action': 'create' , 'type': 'item'})
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, " CREATE ")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {'action': 'create' , 'type': 'item'})
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
        self.assertEqual(command.json, {'action': 'merge' , 'type': 'item', 'item1': 'Q1', 'item2': 'Q2'})
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "MERGE\tQ2\tQ1")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {'action': 'merge' , 'type': 'item', 'item1': 'Q1', 'item2': 'Q2'})
        self.assertEqual(command.status, BatchCommand.STATUS_INITIAL)
        command = BatchCommand.objects.create_command_from_v1(self.batch, 0, "MERGE \tQ1 \tQ2 ")
        self.assertEqual(command.batch, self.batch)
        self.assertEqual(command.index, 0)
        self.assertEqual(command.json, {'action': 'merge' , 'type': 'item', 'item1': 'Q1', 'item2': 'Q2'})
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


    