import logging
import time

from core.models import Batch
from django.core.management.base import BaseCommand
from django.db import transaction

logger = logging.getLogger("qsts3")


class Command(BaseCommand):
    TIMEOUT_SEC = 10
    help = "Sends all available batches to the Wikidata API"

    def handle(self, *args, **options):
        logger.info("[command] send_batches management command started!")
        pending_batches = Batch.objects.filter(status=Batch.STATUS_INITIAL)

        while True:
            batches = pending_batches.select_for_update(skip_locked=True)
            for batch in batches.order_by("?").iterator():
                with transaction.atomic():
                    try:
                        batch.run()
                    except Exception as exc:
                        logger.exception(f"Failed to process {batch}: {exc}")
            else:
                logger.info(f"No batches to process. Sleeping {self.TIMEOUT_SEC}s...")
                time.sleep(self.TIMEOUT_SEC)
