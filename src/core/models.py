import logging
from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _

from .client import Client
from .commands import ApiCommandBuilder
from .exceptions import ApiException
from .exceptions import InvalidPropertyValueType
from .exceptions import NoToken
from .exceptions import UnauthorizedToken
from .exceptions import ServerError
from .exceptions import UserError
from .exceptions import NoStatementsForThatProperty
from .exceptions import NoStatementsWithThatValue

logger = logging.getLogger("qsts3")


class Batch(models.Model):
    """
    Represents a BATCH, containing multiple commands
    """

    STATUS_STOPPED = -2
    STATUS_BLOCKED = -1
    STATUS_PREVIEW = 0
    STATUS_INITIAL = 1
    STATUS_RUNNING = 2
    STATUS_DONE = 3

    STATUS_CHOICES = (
        (STATUS_STOPPED, _("Stopped")),
        (STATUS_BLOCKED, _("Blocked")),
        (STATUS_PREVIEW, _("Preview")),
        (STATUS_INITIAL, _("Initial")),
        (STATUS_RUNNING, _("Running")),
        (STATUS_DONE, _("Done")),
    )

    name = models.CharField(max_length=255, blank=False, null=False)
    user = models.CharField(max_length=128, blank=False, null=False, db_index=True)
    status = models.IntegerField(default=STATUS_INITIAL, choices=STATUS_CHOICES, null=False, db_index=True)
    message = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)
    block_on_errors = models.BooleanField(default=False)

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
        if not self.is_initial:
            return

        self.start()

        try:
            client = Client.from_username(self.user)
            is_autoconfirmed = client.get_is_autoconfirmed()
        except (NoToken, UnauthorizedToken, ServerError):
            return self.block_no_token()
        if not is_autoconfirmed:
            return self.block_is_not_autoconfirmed()

        # TODO: if self.verify_value_types_before_running
        for command in self.commands():
            try:
                command.verify_value_types(client)
            except InvalidPropertyValueType:
                if self.block_on_errors:
                    return self.block_by(command)

        last_id = None

        for command in self.commands():
            self.refresh_from_db()
            if self.is_stopped:
                # The status changed, so we have to stop
                return

            command.update_last_id(last_id)
            command.run(client)
            if command.is_error_status() and self.block_on_errors:
                return self.block_by(command)

            if command.action == BatchCommand.ACTION_CREATE:
                last_id = command.response_id()

        self.finish()

    def start(self):
        logger.debug(f"[{self}] running...")
        self.message = f"Batch started processing at {datetime.now()}"
        self.status = self.STATUS_RUNNING
        self.save()

    def finish(self):
        logger.info(f"[{self}] finished")
        self.message = f"Batch finished processing at {datetime.now()}"
        self.status = self.STATUS_DONE
        self.save()

    def stop(self):
        logger.debug(f"[{self}] stop...")
        self.message = f"Batch stopped processing by owner at {datetime.now()}"
        self.status = self.STATUS_STOPPED
        self.save()

    def restart(self):
        if self.is_stopped:
            logger.debug(f"[{self}] restarting...")
            self.message = f"Batch restarted by owner {datetime.now()}"
            self.status = self.STATUS_INITIAL
            self.save()

    def block_is_not_autoconfirmed(self):
        logger.warn(f"[{self}] blocked, the user {self.user} is not autoconfirmed")
        message = "The user is not an autoconfirmed user."
        self.block_with_message(message)

    def block_no_token(self):
        logger.error(f"[{self}] blocked, we don't have a valid token for the user {self.user}")
        message = "We don't have a valid API token for the user"
        self.block_with_message(message)

    def block_by(self, command):
        logger.warn(f"[{self}] blocked by {command}")
        message = f"blocked by command {command.index}"
        self.block_with_message(message)

    def block_with_message(self, message):
        self.message = message
        self.status = self.STATUS_BLOCKED
        self.save()

    @property
    def is_preview(self):
        return self.status == Batch.STATUS_PREVIEW

    @property
    def is_running(self):
        return self.status == Batch.STATUS_RUNNING

    @property
    def is_stopped(self):
        return self.status == Batch.STATUS_STOPPED

    @property
    def is_initial(self):
        return self.status == Batch.STATUS_INITIAL

    @property
    def is_initial_or_running(self):
        return self.is_initial or self.is_running

    @property
    def is_preview_initial_or_running(self):
        return self.is_preview or self.is_initial or self.is_running

    def add_preview_command(self, preview_command: "BatchCommand") -> bool:
        if not hasattr(self, "_preview_commands"):
            self._preview_commands = []
        if preview_command is not None:
            self._preview_commands.append(preview_command)
            return True
        return False

    def get_preview_commands(self) -> list:
        if hasattr(self, "_preview_commands"):
            return self._preview_commands
        else:
            return []

    def save_batch_and_preview_commands(self):
        self.status = self.STATUS_INITIAL
        if not self.pk:
            super(Batch, self).save()
        if hasattr(self, "_preview_commands"):
            for batch_command in self._preview_commands:
                batch_command.batch = self
                batch_command.save()


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
        (STATUS_DONE, _("Done")),
    )

    ACTION_CREATE = 0
    ACTION_ADD = 1
    ACTION_REMOVE = 2
    ACTION_MERGE = 3

    ACTION_CHOICES = (
        (ACTION_CREATE, "CREATE"),
        (ACTION_ADD, "ADD"),
        (ACTION_REMOVE, "REMOVE"),
        (ACTION_MERGE, "MERGE"),
    )

    # -------
    # Identifier fields
    # -------
    batch = models.ForeignKey(Batch, null=False, on_delete=models.CASCADE)
    index = models.IntegerField()

    # -------
    # Datetime
    # -------
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    # -------
    # Parser fields
    # -------
    raw = models.TextField()
    json = models.JSONField()

    # -------
    # Operation/action fields
    # -------
    action = models.IntegerField(default=ACTION_CREATE, choices=ACTION_CHOICES, null=False, blank=False)
    user_summary = models.TextField(blank=True, null=True)

    class Operation(models.TextChoices):
        CREATE_ITEM = "create_item", _("Create item")
        CREATE_PROPERTY = "create_property", _("Create property")
        REMOVE_STATEMENT_BY_ID = "remove_statement_by_id", _("Remove statement by id")
        REMOVE_STATEMENT_BY_VALUE = "remove_statement_by_value", _("Remove statement by value")
        SET_SITELINK = "set_sitelink", _("Set sitelink")
        REMOVE_SITELINK = "remove_sitelink", _("Remove sitelink")

    operation = models.TextField(
        null=True,
        blank=True,
        choices=Operation,
    )

    # -------
    # Running fields
    # -------
    status = models.IntegerField(default=STATUS_INITIAL, choices=STATUS_CHOICES, null=False, db_index=True)
    value_type_verified = models.BooleanField(default=False)

    # -------
    # Post-running fields
    # -------
    message = models.TextField(blank=True, null=True)
    response_json = models.JSONField(default=dict, blank=True)

    class Error(models.TextChoices):
        OP_NOT_IMPLEMENTED = "op_not_implemented", _("Operation not implemented")
        NO_STATEMENTS_PROPERTY = "no_statements_property", _("No statements for given property")
        NO_STATEMENTS_VALUE = "no_statements_value", _("No statements with given value")
        SITELINK_INVALID = "sitelink_invalid", _("The sitelink id is invalid")

    error = models.TextField(
        null=True,
        blank=True,
        choices=Error,
    )

    def __str__(self):
        return f"Batch #{self.batch.pk} Command #{self.pk}"

    # -----------------
    # Status-changing methods
    # -----------------

    def start(self):
        logger.debug(f"[{self}] running...")
        self.status = BatchCommand.STATUS_RUNNING
        self.save()

    def finish(self):
        logger.info(f"[{self}] finished")
        self.status = BatchCommand.STATUS_DONE
        self.save()

    def error_with_value(self, value: Error):
        self.error = value
        self.error_with_message(value.label)

    def error_with_exception(self, exception: Exception):
        message = getattr(exception, "message", str(exception))
        self.error_with_message(message)

    def error_with_message(self, message):
        logger.error(f"[{self}] error: {message}")
        self.message = message
        self.status = BatchCommand.STATUS_ERROR
        self.save()

    # -----------------
    # Entity id methods
    # -----------------

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

    # -----------------
    # Property methods
    # -----------------

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
    def type(self):
        return self.json.get("type", "").upper()

    @property
    def value(self):
        return self.json.get("value", {}).get("value", "")

    @property
    def value_type(self):
        return self.json.get("value", {}).get("type", "")

    @property
    def value_value(self):
        return self.json.get("value", {}).get("value", "")

    @property
    def statement_api_value(self):
        if self.value_type in ["novalue", "somevalue"]:
            return {
                "type": self.value_type,
            }
        else:
            return {
                "type": "value",
                "content": self.value_value,
            }

    def qualifiers(self):
        return self.json.get("qualifiers", [])

    def references(self):
        return self.json.get("references", [])

    def reference_parts(self):
        parts = []
        for ref in self.references():
            parts.extend(ref)
        return parts

    # -----------------
    # verification methods
    # -----------------

    def is_add(self):
        return self.action == BatchCommand.ACTION_ADD

    def is_add_statement(self):
        return self.is_add() and self.what == "STATEMENT"

    def is_add_label_description_alias(self):
        return self.is_add() and self.what in ["DESCRIPTION", "LABEL", "ALIAS"]

    def is_remove(self):
        return self.action == BatchCommand.ACTION_REMOVE

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

    # -----------------
    # LAST related methods
    # -----------------

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

    # -----------------
    # Wikibase API basic methods
    # -----------------

    def run(self, client: Client):
        """
        Sends the command to the Wikidata API. This method should not raise exceptions.
        """
        # Ignore when not INITIAL
        if self.status != BatchCommand.STATUS_INITIAL:
            return

        self.start()

        if self.entity_id() == "LAST":
            self.error_with_message("LAST could not be evaluated.")
            return

        try:
            self.verify_value_types(client)
            self.response_json = self.send_to_api(client)
            self.finish()
        except NotImplementedError:
            self.error_with_value(self.Error.OP_NOT_IMPLEMENTED)
        except NoStatementsForThatProperty:
            self.error_with_value(self.Error.NO_STATEMENTS_PROPERTY)
        except NoStatementsWithThatValue:
            self.error_with_value(self.Error.NO_STATEMENTS_VALUE)
        except UserError as e:
            if e.response_message == "Invalid path parameter: 'site_id'":
                self.error_with_value(self.Error.SITELINK_INVALID)
            else:
                self.error_with_exception(e)
        except (ApiException, Exception) as e:
            self.error_with_exception(e)

    def edit_summary(self):
        """
        Returns the final edit summary.

        It joins the user supplied summary with
        the identification necessary for EditGroups.
        """
        editgroups = self.editgroups_summary()
        return f"{editgroups}: {self.user_summary}" if self.user_summary else editgroups

    def editgroups_summary(self):
        """
        Returns the EditGroups notice to put into the summary.
        """
        # Our regex for EditGroups:
        # ".*\[\[:toollabs:TOOLFORGE_TOOL_NAME/batch/(\d+)\|.*"
        tool = settings.TOOLFORGE_TOOL_NAME
        batch_id = self.batch.id
        return f"[[:toollabs:{tool}/batch/{batch_id}|batch #{batch_id}]]"

    def api_payload(self):
        """
        Returns the data that is sent to the Wikibase API through the body.
        """
        match self.operation:
            case self.Operation.CREATE_ITEM:
                return {"item": {}}
            case self.Operation.SET_SITELINK:
                return {
                    "sitelink": {
                        "title": self.value_value,
                        "badges": [],
                    },
                }
            case _:
                return {}

    def api_body(self):
        """
        Returns the final Wikibase API body.

        Joins the api payload with bot marking = False and the edit summary.
        """
        body = self.api_payload()
        body["bot"] = False
        body["comment"] = self.edit_summary()
        return body

    def send_to_api(self, client: Client) -> dict:
        match self.operation:
            case self.Operation.CREATE_ITEM:
                return client.create_item(self.api_body())
            case self.Operation.CREATE_PROPERTY:
                raise NotImplementedError()
            case self.Operation.REMOVE_STATEMENT_BY_ID | self.Operation.REMOVE_STATEMENT_BY_VALUE:
                return client.delete_statement(self.statement_id(client), self.api_body())
            case self.Operation.SET_SITELINK:
                return client.add_sitelink(self.entity_id(), self.sitelink, self.api_body())
            case self.Operation.REMOVE_SITELINK:
                sitelinks = client.sitelinks(self.entity_id(), self.api_body())
                # TODO: (improve) workaround to make it idempotent like QSv2
                # I could not make it work using json patches,
                # the API gives an error when trying to remove a non-existant path
                if self.sitelink in sitelinks:
                    return client.remove_sitelink(self.entity_id(), self.sitelink, self.api_body())
                else:
                    return sitelinks
            case _:
                return ApiCommandBuilder(self, client).build_and_send()

    # -----------------
    # Auxiliary methods for Wikibase API interaction
    # -----------------

    def statement_id(self, client: Client) -> str:
        """
        Returns the ID of the statement related to this command.
        """
        if self.operation == self.Operation.REMOVE_STATEMENT_BY_ID:
            return self.json["id"]
        elif self.operation == self.Operation.REMOVE_STATEMENT_BY_VALUE:
            return self.get_statement_id_by_value(client)

    def get_statement_id_by_value(self, client: Client) -> str:
        """
        Gets the first statement from the API that matches
        this commmand's property and value.

        # Raises

        - `NoStatementsForThatProperty`
        - `NoStatementsWithThatValue`
        """
        all = client.get_statements(self.entity_id())
        statements = all.get(self.prop, [])

        if len(statements) == 0:
            raise NoStatementsForThatProperty(self.entity_id(), self.prop)

        for statement in statements:
            if statement["value"] == self.statement_api_value:
                return statement["id"]

        raise NoStatementsWithThatValue(self.entity_id(), self.prop, self.statement_api_value)

    # -----------------
    # Visualization/label methods
    # -----------------

    def get_label(self, client: Client, preferred_language="en"):
        """
        Obtains the label for the entity of this command.

        If there is no initial entity, like in a CREATE command, it will return None.

        Using the entity's entity id, will obtain the labels from the API.

        The prefered language will be used at first. If there is no label for the
        preferred language, it will use the english label.
        """
        id = self.entity_id()

        if id is None or id == "LAST":
            return id

        labels = client.get_labels(id)

        preferred = labels.get(preferred_language)

        if not preferred and preferred_language != "en":
            return labels.get("en")
        else:
            return preferred

    # -----------------
    # Value type verification
    # -----------------

    def verify_value_types(self, client: Client):
        """
        Checks if the supplied value type is allowed by the property's required value type.

        Makes that check for the statement and for qualifiers and references.

        It sets the status to ERROR if the value type is invalid, updates the message,
        and raises InvalidPropertyValueType.

        Only makes sense in commands that require value type verification
        (see self._should_verify_value_types)

        # Raises

        - InvalidPropertyValueType: when the value type is not valid.
        """
        if self.should_verify_value_types():
            try:
                client.verify_value_type(self.prop, self.value_type)
                for q in self.qualifiers():
                    client.verify_value_type(q["property"], q["value"]["type"])
                for p in self.reference_parts():
                    client.verify_value_type(p["property"], p["value"]["type"])
            except InvalidPropertyValueType as e:
                self.error_with_message(e.message)
                raise e

        self.value_type_verified = True
        self.save()

    def should_verify_value_types(self):
        """
        Checks if this command needs value type verification.

        1) It needs to be not verified yet, of course.

        2) It needs if it is of the following types/actions:

        - Statement addition
        """
        is_not_verified_yet = not self.value_type_verified
        is_needed_actions = self.is_add_statement()
        return is_not_verified_yet and is_needed_actions

    # -----------------
    # Meta
    # -----------------

    class Meta:
        verbose_name = _("Batch Command")
        verbose_name_plural = _("Batch Commands")
        index_together = ("batch", "index")
