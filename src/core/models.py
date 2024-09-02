import logging

from django.db import models
from django.utils.translation import gettext as _

logger = logging.getLogger("qsts3")
   

class Batch(models.Model):
    """
    Represents a BATCH, containing multiple commands
    """

    STATUS_BLOCKED = -1
    STATUS_INITIAL = 0
    STATUS_RUNNING = 1
    STATUS_DONE = 2

    STATUS_CHOICES = (
        (STATUS_BLOCKED, _("Blocked")),
        (STATUS_INITIAL, _("Initial")),
        (STATUS_RUNNING, _("Running")),
        (STATUS_DONE, _("Done"))
    )

    name = models.CharField(max_length=255, blank=False, null=False)
    user = models.CharField(max_length=128, blank=False, null=False, db_index=True)
    status = models.IntegerField(default=STATUS_INITIAL, choices=STATUS_CHOICES, null=False, db_index=True)
    message = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        return f"Batch #{self.pk}"

    class Meta:
        verbose_name = _("Batch")
        verbose_name_plural = _("Batches")

    def commands(self):
        return BatchCommand.objects.filter(batch=self).all().order_by("index")

    def run(self):
        """
        Sends all the batch commands to the Wikidata API. This method should not fail.
        Sets the batch status to BLOCKED when a command fails.
        """
        # Ignore when not INITIAL
        if self.status != Batch.STATUS_INITIAL:
            return

        self._update_status_to_running()
        logger.debug(f"[{self}] running...")

        for command in self.commands():
            command.run()
            if command.is_error_status():
                self._update_status_to_blocked()
                logger.warn(f"[{self}] blocked by {command}")
                return

        self._update_status_to_done()
        logger.info(f"[{self}] finished")

    def _send_to_api(self):
        from api.commands import ApiCommandBuilder
        ApiCommandBuilder(self).build_and_send()

    def _update_status_to_running(self):
        self.status = self.STATUS_RUNNING
        self.save()

    def _update_status_to_done(self):
        self.status = self.STATUS_DONE
        self.save()

    def _update_status_to_blocked(self):
        self.status = self.STATUS_BLOCKED
        self.save()


class BatchCommand(models.Model):
    """
    Individual command from a batch
    """

    STATUS_ERROR = -1
    STATUS_INITIAL = 0
    STATUS_RUNNING = 1
    STATUS_DONE = 2

    STATUS_CHOICES = (
        (STATUS_ERROR, _("Error")), 
        (STATUS_INITIAL, _("Initial")), 
        (STATUS_RUNNING, _("Running")), 
        (STATUS_DONE, _("Done"))
    )

    ACTION_CREATE = 0
    ACTION_ADD = 1
    ACTION_REMOVE = 2
    ACTION_MERGE = 3

    ACTION_CHOICES = (
        (ACTION_CREATE, "CREATE"),
        (ACTION_ADD, "ADD"),
        (ACTION_REMOVE, "REMOVE"),
        (ACTION_MERGE, "MERGE")
    )

    batch = models.ForeignKey(Batch, null=False, on_delete=models.CASCADE)
    action = models.IntegerField(default=ACTION_CREATE, choices=ACTION_CHOICES, null=False, blank=False)
    index = models.IntegerField()
    json = models.JSONField()
    status = models.IntegerField(default=STATUS_INITIAL, choices=STATUS_CHOICES, null=False, db_index=True)
    raw = models.TextField()
    message = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Batch #{self.batch.pk} Command #{self.pk}"

    @property
    def entity_info(self):
        item = self.json.get("item", None)
        if item:
            return f"[{item}]"
        else:
            eid = self.json.get('entity', {}).get('id', None)
            return f"[{eid}]" if eid else ""

    @property
    def status_info(self):
        return self.get_status_display().upper()

    @property
    def language(self):
        return self.json.get("language", "")

    @property
    def sitelink(self):
        return self.json.get("site", "")

    @property
    def what(self):
        if not hasattr(self, "_what"):
            self._what = self.json.get("what", "").upper()
        return self._what

    @property
    def prop(self):
        return self.json.get("property", "") 

    @property
    def value(self):
        return self.json.get("value", {}).get("value", "")

    def is_add_or_remove_command(self):
        return self.action in [BatchCommand.ACTION_ADD, BatchCommand.ACTION_REMOVE]

    def is_merge_command(self):
        return self.action == BatchCommand.ACTION_MERGE

    def is_label_alias_description_command(self):
        return self.what in ["DESCRIPTION", "LABEL", "ALIAS"]

    def is_sitelink_command(self):
        return self.what == "SITELINK"

    def is_error_status(self):
        return self.status == BatchCommand.STATUS_ERROR

    def run(self):
        """
        Sends the command to the Wikidata API. This method should not fail.
        """
        # Ignore when not INITIAL
        if self.status != BatchCommand.STATUS_INITIAL:
            return

        self._update_status_to_running()
        logger.debug(f"[{self}] running...")

        try:
            self._send_to_api()
            self._update_status_to_done()
            logger.info(f"[{self}] finished")
        except Exception as e:
            logger.error(f"[{self}] error: {e}")
            self._update_status_to_error()

    def _send_to_api(self):
        from api.commands import ApiCommandBuilder
        ApiCommandBuilder(self).build_and_send()

    def _update_status_to_running(self):
        self.status = BatchCommand.STATUS_RUNNING
        self.save()

    def _update_status_to_done(self):
        self.status = BatchCommand.STATUS_DONE
        self.save()

    def _update_status_to_error(self):
        self.status = BatchCommand.STATUS_ERROR
        self.save()


    class Meta:
        verbose_name = _("Batch Command")
        verbose_name_plural = _("Batch Commands")
        index_together = (
            ('batch', 'index')
        )
