from enum import Enum

from django.db import models
from django.utils.translation import gettext as _

from core.parsers.v1 import V1CommandParser
from core.parsers.base import ParserException


class Batch(models.Model):
    """
    Represents a BATCH, containing multiple commands
    """

    class STATUS(Enum):
        BLOCKED = (-1, _("Blocked"))
        INITIAL = (0, _("Initial"))
        RUNNING = (1, _("Running"))
        DONE = (2, _("Done"))

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
            message = None
        except ParserException as e:
            status = BatchCommand.STATUS_ERROR
            command = {}
            message = e.message

        return self.create(batch=batch, index=index, json=command, raw=raw_command, status=status, message=message)

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

    STATUS_CHOICES = ((-1, _("Error")), (0, _("Initial")), (1, _("Running")), (2, _("Done")))

    objects = BatchCommandManager()

    batch = models.ForeignKey(Batch, null=False, on_delete=models.CASCADE)
    index = models.IntegerField()
    json = models.JSONField()
    status = models.IntegerField(default=STATUS_INITIAL, choices=STATUS_CHOICES, null=False, db_index=True)
    raw = models.TextField()
    message = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Batch #{self.batch.pk} Command #{self.pk}"

    class Meta:
        verbose_name = _("Batch Command")
        verbose_name_plural = _("Batch Commands")
