from enum import Enum

from django.db import models
from django.utils.translation import gettext as _


class Batch(models.Model):
    """
    Represents a BATCH, containing multiple commands
    """
    class STATUS(Enum):
        BLOCKED = (-1, _('Blocked'))
        INITIAL = (0, _('Initial'))
        RUNNING = (1, _('Running'))
        DONE = (2, _('Done'))

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


class BatchCommand(models.Model):
    """
    Individual command from a batch
    """
    class STATUS(Enum):
        BLOCKED = (-1, _('Error'))
        INITIAL = (0, _('Initial'))
        RUNNING = (1, _('Running'))
        DONE = (2, _('Done'))

    batch = models.ForeignKey(Batch, null=False, on_delete=models.CASCADE)
    index = models.IntegerField()
    json = models.JSONField()
    status = models.IntegerField(default=STATUS.INITIAL, choices=[s.value for s in STATUS], null=False, db_index=True)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Batch #{self.batch.pk} Command #{self.pk}"

    class Meta:
        verbose_name = _("Batch Command")
        verbose_name_plural = _("Batch Commands")
