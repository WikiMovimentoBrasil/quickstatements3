import logging
import threading
import time

from core.models import Batch
from django.core.management.base import BaseCommand

logger = logging.getLogger("qsts3")


def process_batches(batches):
    for batch in batches.iterator():
        try:
            batch.run()
        except Exception as exc:
            logger.exception(f"Failed to process {batch}: {exc}")


class Command(BaseCommand):
    TIMEOUT_SEC = 2
    help = "Sends all available batches to the Wikidata API"

    def handle(self, *args, **options):
        logger.info("[command] send_batches management command started!")
        user_threads = {}

        while True:
            batches = Batch.objects.filter(status=Batch.STATUS_INITIAL)
            users = batches.values_list("user", flat=True).distinct()

            completed = [u for u, t in user_threads.items() if not t.is_alive()]
            for user in completed:
                del user_threads[user]

            for user in users:
                thread = user_threads.get(user, None)
                if thread is not None and thread.is_alive():
                    logger.debug(f"Thread for user {user} is running...")
                    continue

                user_batches = batches.filter(user=user)
                thread = threading.Thread(
                    target=process_batches, daemon=True, args=(user_batches,)
                )
                logger.info(f"Starting thread for user {user}...")
                thread.start()
                user_threads[user] = thread

            logger.debug(f"No batches to process. Sleeping {self.TIMEOUT_SEC}s...")
            time.sleep(self.TIMEOUT_SEC)
