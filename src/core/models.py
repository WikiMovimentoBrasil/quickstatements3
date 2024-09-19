import logging

from django.db import models
from django.utils.translation import gettext as _

from .client import Client
from .exceptions import ApiException
from .exceptions import InvalidPropertyDataType

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

        client = Client.from_username(self.user)

        last_id = None

        for command in self.commands():
            command.update_last_id(last_id)
            command.run(client)
            if command.is_error_status():
                self._update_status_to_blocked()
                logger.warn(f"[{self}] blocked by {command}")
                return

            if command.action == BatchCommand.ACTION_CREATE:
                last_id = command.response_id()

        self._update_status_to_done()
        logger.info(f"[{self}] finished")

    def _send_to_api(self):
        from .commands import ApiCommandBuilder
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
    data_type_verified = models.BooleanField(default=False)
    response_json = models.JSONField(default=dict)

    def __str__(self):
        return f"Batch #{self.batch.pk} Command #{self.pk}"

    @property
    def entity_info(self):
        entity_id = self.entity_id()
        return f"[{entity_id}]" if entity_id else ""

    def entity_id(self):
        item = self.json.get("item", None)
        if item:
            return item
        return self.json.get("entity", {}).get("id", None)

    def set_entity_id(self, value):
        if self.json.get("item", None):
            self.json["item"] = value
        elif self.json.get("entity", {}).get("id", None):
            self.json["entity"]["id"] = value
        else:
            raise ValueError("This command has no entity to update its id.")

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

    @property
    def data_type(self):
        return self.json.get("value", {}).get("type", "")

    def is_add_statement(self):
        return self.action == BatchCommand.ACTION_ADD and self.what == "STATEMENT"

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

    def response_id(self):
        """
        Returns the response's id.            

        It is the created entity id when in a CREATE action.
        """
        return self.response_json.get("id")

    def update_last_id(self, last_id=None):
        """
        Updates this command's entity id, if it's LAST, to the argument.
        """
        if self.entity_id() == "LAST" and last_id is not None:
            self.set_entity_id(last_id)
            self.save()

    def run(self, client: Client):
        """
        Sends the command to the Wikidata API. This method should not fail.
        """
        # Ignore when not INITIAL
        if self.status != BatchCommand.STATUS_INITIAL:
            return

        self._update_status_to_running()
        logger.debug(f"[{self}] running...")

        try:
            self.verify_data_type(client)
            self.response_json = self._send_to_api()
            self._update_status_to_done()
            logger.info(f"[{self}] finished")
        except (ApiException, Exception) as e:
            message = getattr(e, "message", str(e))
            logger.error(f"[{self}] error: {message}")
            self.message = message
            self._update_status_to_error()

    def _send_to_api(self):
        from .commands import ApiCommandBuilder
        return ApiCommandBuilder(self).build_and_send()

    def _update_status_to_running(self):
        self.status = BatchCommand.STATUS_RUNNING
        self.save()

    def _update_status_to_done(self):
        self.status = BatchCommand.STATUS_DONE
        self.save()

    def _update_status_to_error(self):
        self.status = BatchCommand.STATUS_ERROR
        self.save()

    def get_label(self, api_client, preferred_language="en", cache_dictionary={}):
        """
        Obtains the label for the entity of this command.

        If there is no initial entity, like in a CREATE command, it will return None.

        Using the entity's entity id, will obtain the labels from the API.

        The prefered language will be used at first. If there is no label for the
        preferred language, it will use the english label.

        The cache_dictionary argument can be used when running this in a for loop
        with multiple commands that have the same entity id, to reduce API calls.
        """
        id = self.entity_id()

        if id is None or id == "LAST":
            return id

        if cache_dictionary.get(id) is None:
            labels = api_client.get_labels(id)

            preferred = labels.get(preferred_language)

            if not preferred and preferred_language != "en":
                cache_dictionary[id] = labels.get("en")
            else:
                cache_dictionary[id] = preferred

        return cache_dictionary[id]

    def verify_data_type(self, client: Client):
        """
        Checks if the supplied data type is allowed by the property's required data type.

        It sets the status to ERROR if the data type is invalid, updates the message,
        and raises InvalidPropertyDataType.

        Only makes sense in commands that require data type verification
        (see self._should_verify_data_type)
        """
        if self.should_verify_data_type():
            needed_data_type = client.get_property_data_type(self.prop)
            if self.data_type != needed_data_type:
                exception = InvalidPropertyDataType(
                    self.prop,
                    self.data_type,
                    needed_data_type
                )
                self.message = exception.message
                self._update_status_to_error()
                raise exception

        self.data_type_verified = True
        self.save()

    def should_verify_data_type(self):
        """
        Checks if this command needs data type verification.

        1) It needs to be not verified yet, of course.

        2) It needs if it is of the following types/actions:

        - Statement addition

        3) And the data type is not somevalue or novalue, since those
        can be used in any property.
        """
        is_not_verified_yet = not self.data_type_verified
        needed_actions = self.is_add_statement()
        data_type_is_not_somevalue_or_novalue = self.data_type not in ["somevalue", "novalue"]
        return (
            is_not_verified_yet
            and needed_actions
            and data_type_is_not_somevalue_or_novalue
        )



    class Meta:
        verbose_name = _("Batch Command")
        verbose_name_plural = _("Batch Commands")
        index_together = (
            ('batch', 'index')
        )
