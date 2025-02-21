import logging

from core.models import Batch
from django.core.management.base import BaseCommand
from django.db import transaction

logger = logging.getLogger("qsts3")


class Command(BaseCommand):
    help = "Sends all available batches to the Wikidata API"

    def handle(self, *args, **options):
        logger.info("[command] send_batches management command started!")
        batches = Batch.objects.filter(status=Batch.STATUS_INITIAL)

        for batch in (
            batches.select_for_update(skip_locked=True).order_by("?").iterator()
        ):
            with transaction.atomic():
                try:
                    batch.run()
                except Exception as exc:
                    logger.exception(f"Failed to process {batch}: {exc}")
