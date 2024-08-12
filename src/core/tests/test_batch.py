from django.test import TestCase

from core.models import Batch
from core.models import BatchCommand


class TestBatch(TestCase):
    def test_v1_correct_create_command(self):
        self.assertFalse(Batch.objects.count())
        self.assertFalse(BatchCommand.objects.count())
        batch = Batch.objects.create_batch("My batch", "CREATE||-Q1234|P1|12||Q222|P4|9~0.1", "v1", "myuser")
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
        


