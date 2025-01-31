import time
import logging

from django.core.management.base import BaseCommand
from core.models import Batch
from django.db import transaction
from django.db.utils import OperationalError

logger = logging.getLogger("qsts3")


class Command(BaseCommand):
    TIMEOUT_SEC = 10

    help = "Sends all available batches to the Wikidata API"

    def handle(self, *args, **options):
        self.send_start_message()

        while True:
            batch = self.get_first_batch_and_lock()
            if batch:
                batch.run()
            else:
                time.sleep(self.TIMEOUT_SEC)

    def send_start_message(self):
        logger.info("[command] send_batches management command started!")

    def get_first_batch_and_lock(self):
        with transaction.atomic():
            try:
                batch = self.get_first_batch()
                self.lock_batch(batch)
            except OperationalError:
                logger.debug("[command] race condition mitigated")
                return None
        return batch

    def get_first_batch(self):
        return (
            Batch.objects.select_for_update(skip_locked=True)
            .filter(status=Batch.STATUS_INITIAL)
            .order_by("id")
            .first()
        )

    def lock_batch(self, batch):
        if batch:
            batch.status = batch.STATUS_RUNNING
            batch.save()
