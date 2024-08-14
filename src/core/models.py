from enum import Enum

from django.db import models
from django.utils.translation import gettext as _

from core.parsers.v1 import V1CommandParser
from core.parsers.base import ParserException


class BatchManager(models.Manager):

    def create_batch(self, batch_name: str, batch_commands: str, batch_type: str, batch_owner: str):
        BATCH_COMMAND_CREATOR = {
            "v1": BatchCommand.objects.create_command_from_v1,
            "csv": BatchCommand.objects.create_command_from_csv
        }

        fn = BATCH_COMMAND_CREATOR.get(batch_type)
        if not fn:
            raise ParserException("Commands format must be v1 or csv")

        batch = self.create(name=batch_name, user=batch_owner)
        batch_commands = batch_commands.replace("||", "\n").replace("|", "\t")
        for index, command in enumerate(batch_commands.split("\n")):
            fn(batch, index, command)
        return batch
        

class Batch(models.Model):
    """
    Represents a BATCH, containing multiple commands
    """
    class STATUS(Enum):
        BLOCKED = (-1, _("Blocked"))
        INITIAL = (0, _("Initial"))
        RUNNING = (1, _("Running"))
        DONE = (2, _("Done"))

    objects = BatchManager()

    name = models.CharField(max_length=255, blank=False, null=False)
    user = models.CharField(max_length=128, blank=False, null=False, db_index=True)
    status = models.IntegerField(default=STATUS.INITIAL.value[0], choices=[s.value for s in STATUS], null=False)
    message = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Batch #{self.pk}"

    class Meta:
        verbose_name = _("Batch")
        verbose_name_plural = _("Batches")

    def commands(self):
        return BatchCommand.objects.filter(batch=self).all().order_by("index")


class BatchCommandManager(models.Manager):
    def create_command_from_v1(self, batch, index, raw_command):
        parser = V1CommandParser()
        try:
            status = BatchCommand.STATUS_INITIAL
            command = parser.parse(raw_command)
            if command["action"] == "add":
                action = BatchCommand.ACTION_ADD
            elif command["action"] == "remove":
                action = BatchCommand.ACTION_REMOVE 
            elif command["action"] == "create":
                action = BatchCommand.ACTION_CREATE
            else:
                action = BatchCommand.ACTION_MERGE
            message = None
        except ParserException as e:
            status = BatchCommand.STATUS_ERROR
            command = {}
            message = e.message
            action = BatchCommand.ACTION_CREATE

        return self.create(batch=batch, index=index, action=action, json=command, raw=raw_command, status=status, message=message)

    def create_command_from_csv(self, batch, index, raw_command):
        return self.create(batch=batch, index=index, json=command, raw=raw_command)


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

    objects = BatchCommandManager()

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
        

    class Meta:
        verbose_name = _("Batch Command")
        verbose_name_plural = _("Batch Commands")
