import time

from django.core.management.base import BaseCommand
from core.models import Batch


class Command(BaseCommand):
    TIMEOUT_SEC = 10

    help = "Sends all available batches to the Wikidata API"

    def handle(self, *args, **options):
        self.send_start_message()

        while True:
            batch = self.get_first_batch()
            if batch:
                batch.run()
            else:
                time.sleep(self.TIMEOUT_SEC)

    def send_start_message(self):
        msg = self.style.SUCCESS("==> send_batches management command started!")
        self.stdout.write(msg)

    def get_first_batch(self):
        return (
            Batch.objects.select_for_update()
            .filter(status=Batch.STATUS_INITIAL)
            .order_by("id")
            .first()
        )
