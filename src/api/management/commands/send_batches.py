from django.core.management.base import BaseCommand
from core.models import Batch


class Command(BaseCommand):
    help = "Sends all available batches to the Wikidata API"

    def handle(self, *args, **options):
        while True:
            batch = self._get_first_batch()
            if batch is None:
                self._exit_msg()
                break
            else:
                self._run_batch(batch)
                self._print_result(batch)

    def _get_first_batch(self):
        return (
            Batch.objects.select_for_update()
            .filter(status=Batch.STATUS_INITIAL)
            .order_by("id")
            .first()
        )

    def _exit_msg(self):
        msg = self.style.SUCCESS("==> No more batches to run.")
        self.stdout.write(msg)

    def _run_batch(self, batch):
        self.stdout.write(f"==> Running batch: {batch}")
        batch.run()

    def _print_result(self, batch):
        if batch.status == Batch.STATUS_DONE:
            msg = self.style.SUCCESS(f"====> Batch ran successfully: {batch}")
        elif batch.status == Batch.STATUS_BLOCKED:
            msg = self.style.ERROR(f"====> Batch was blocked: {batch}")
        else:
            msg = self.style.WARNING(f"====> Batch was not finished: {batch}")

        self.stdout.write(msg)
        self.stdout.write("")
