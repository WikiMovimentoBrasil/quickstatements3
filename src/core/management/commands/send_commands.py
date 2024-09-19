from django.core.management.base import BaseCommand
from core.models import BatchCommand


class Command(BaseCommand):
    help = "Sends all available commands to the Wikidata API"

    def handle(self, *args, **options):
        while True:
            command = self._get_first_command()
            if command is None:
                self._exit_msg()
                break
            else:
                self._run(command)
                self._print_result(command)

    def _get_first_command(self):
        return (
            BatchCommand.objects.select_for_update()
            .filter(status=BatchCommand.STATUS_INITIAL)
            .order_by("id")
            .first()
        )

    def _exit_msg(self):
        msg = self.style.SUCCESS("==> No more comands to run.")
        self.stdout.write(msg)

    def _run(self, command):
        self.stdout.write(f"==> Running command: {command}")
        command.run()

    def _print_result(self, command):
        if command.status == BatchCommand.STATUS_DONE:
            msg = self.style.SUCCESS(f"====> Command ran successfully: {command}")
        elif command.status == BatchCommand.STATUS_ERROR:
            msg = self.style.ERROR(f"====> Command failed: {command}")
        else:
            msg = self.style.WARNING(f"====> Command was not finished: {command}")

        self.stdout.write(msg)
        self.stdout.write("")
