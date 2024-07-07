from enum import Enum

from django.db import models
from django.utils.translation import gettext as _


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
        status = BatchCommand.STATUS_INITIAL
        message = None
        command = {}

        # comment = ''
        # if ( re.find ( '/^(.*?) *\/\* *(.*?) *\*\/ *$/' , $row , $m ) ) { // Extract comment as summary
        #     comment = $m[2] ;
        #     raw_command = $m[1] ;
        # }
        elements = raw_command.split("\t")
        if len(elements) == 0:
            return None

        llen = len(elements)
        first_command = elements[0].upper().strip()

        if first_command == "CREATE":
            if llen != 1:
                message = "CREATE command can have only 1 column"
                status = BatchCommand.STATUS_ERROR
            else:
                command.update({"action": "create", "type": "item"})

        elif first_command == "MERGE":
            if llen != 3:
                message = "MERGE command must have 3 columns"
                status = BatchCommand.STATUS_ERROR
            else:
                item1 = elements[1].strip()
                item2 = elements[2].strip()
                try:
                    item1_id = int(item1[1:])
                    item2_id = int(item2[1:])
                    if item1_id > item2_id:
                        # Always merge into older item
                        item1, item2 = item2, item1
                    command.update({"action": "merge", "type": "item", "item1": item1, "item2": item2})
                except ValueError:
                    message = f"MERGE items wrong format item1=[{item1}] item2=[{item2}]"
                    status = BatchCommand.STATUS_ERROR

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
