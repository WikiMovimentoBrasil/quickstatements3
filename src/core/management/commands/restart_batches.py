from datetime import datetime
import logging

from django.core.management.base import BaseCommand
from core.models import Batch

logger = logging.getLogger("qsts3")


class Command(BaseCommand):
    """
    Mitigation fix to re-run batches that are blocked in an eternal
    running state because of a server restart.
    """

    help = "Restart all running batches, after a server restart"

    def handle(self, *args, **options):
        batches = []
        for batch in Batch.objects.filter(status=Batch.STATUS_RUNNING):
            logger.info(f"[{batch}] restarting by server restart...")
            batch.message = f"Restarted after a server restart: {datetime.now()}"
            batch.status = Batch.STATUS_INITIAL
            batches.append(batch)
        Batch.objects.bulk_update(batches, ["message", "status"])
