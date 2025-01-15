import logging
import jsonpatch
from typing import Optional
from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _

from .client import Client
from .exceptions import ApiException
from .exceptions import InvalidPropertyValueType
from .exceptions import NoToken
from .exceptions import UnauthorizedToken
from .exceptions import ServerError
from .exceptions import UserError
from .exceptions import NoStatementsForThatProperty
from .exceptions import NoStatementsWithThatValue
from .exceptions import NonexistantPropertyOrNoDataType

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
            except (InvalidPropertyValueType, NonexistantPropertyOrNoDataType):
                if self.block_on_errors:
                    return self.block_by(command)

        last_id = None
        previous_entity_json = None
        commands = self.commands()
        count = commands.count()

        for i, command in enumerate(commands):
            self.refresh_from_db()
            if self.is_stopped:
                # The status changed, so we have to stop
                return

            next = commands[i+1] if (i + 1) < count else None

            command.update_last_id(last_id)
            command.check_combination(previous_entity_json, next)
            command.run(client)

            if command.is_error_status() and self.block_on_errors:
                return self.block_by(command)

            previous_entity_json = getattr(command, "final_entity_json", None)
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
        if preview_command is not None and isinstance(preview_command, BatchCommand):
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
        #
        SET_STATEMENT = "set_statement", _("Set statement")
        #
        REMOVE_STATEMENT_BY_ID = "remove_statement_by_id", _("Remove statement by id")
        REMOVE_STATEMENT_BY_VALUE = "remove_statement_by_value", _("Remove statement by value")
        #
        SET_SITELINK = "set_sitelink", _("Set sitelink")
        SET_LABEL = "set_label", _("Set label")
        SET_DESCRIPTION = "set_description", _("Set description")
        #
        REMOVE_SITELINK = "remove_sitelink", _("Remove sitelink")
        REMOVE_LABEL = "remove_label", _("Remove label")
        REMOVE_DESCRIPTION = "remove_description", _("Remove description")
        #
        ADD_ALIAS = "add_alias", _("Add alias")
        REMOVE_ALIAS = "remove_alias", _("Remove alias")

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

    def entity_url(self):
        entity_id = self.entity_id()
        base = Client.BASE_REST_URL.replace("/w/rest.php", "")
        if entity_id and entity_id != "LAST":
            return f"{base}/entity/{entity_id}"
        else:
            return ""

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
        return self.json.get("what", "").upper()

    @property
    def what_plural_lowercase(self):
        what = self.json.get("what")
        if what == "alias":
            return "aliases"
        elif what:
            return f"{what}s"

    @property
    def language_or_sitelink(self):
        return self.language if self.language else self.sitelink

    @property
    def prop(self):
        return self.json.get("property", "")

    @property
    def type(self):
        return self.json.get("type", "").upper()

    @property
    def value_dict(self):
        if not hasattr(self, "_value_dict"):
            self._value_dict = self.json.get("value", {})
        return self._value_dict

    @property
    def value(self):
        return self.value_dict.get("value", "")

    @property
    def value_type(self):
        return self.value_dict.get("type", "")

    @property
    def value_value(self):
        return self.value_dict.get("value", "")

    def parser_value_to_api_value(self, parser_value):
        if parser_value["type"] in ["novalue", "somevalue"]:
            return {
                "type": parser_value["type"],
            }
        else:
            return {
                "type": "value",
                "content": parser_value["value"],
            }

    @property
    def statement_api_value(self):
        value = self.json["value"]
        if value["type"] == "quantity" and value["value"]["unit"] != "1":
            # TODO: the unit is an entity and we need to put the
            # full entity URL... so we need the client
            # to process the URL
            raise NotImplementedError()
        return self.parser_value_to_api_value(value)

    def update_statement(self, st):
        st.setdefault("property", {"id": self.prop})
        st.setdefault("value", self.statement_api_value)
        quals, refs, rank = self.qualifiers_for_api(), self.references_for_api(), self.statement_rank()
        if quals:
            st.setdefault("qualifiers", [])
            st["qualifiers"].extend(quals)
        if refs:
            st.setdefault("references", [])
            st["references"].extend(refs)
        if rank:
            st["rank"] = rank

    def qualifiers_for_api(self):
        return [
            {
                "property": {"id": q["property"]},
                "value": self.parser_value_to_api_value(q["value"]),
            }
            for q in self.qualifiers()
        ]

    def references_for_api(self):
        all_refs = []
        for ref in self.references():
            fixed_parts = []
            for part in ref:
                fixed_parts.append({
                    "property": {"id": part["property"]},
                    "value": self.parser_value_to_api_value(part["value"]),
                })
            all_refs.append({"parts": fixed_parts})
        return all_refs

    def qualifiers(self):
        return self.json.get("qualifiers", [])

    def references(self):
        return self.json.get("references", [])

    def reference_parts(self):
        parts = []
        for ref in self.references():
            parts.extend(ref)
        return parts

    def statement_rank(self):
        return self.json.get("rank")

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
            if self.can_combine_with_next:
                self.final_entity_json = self.get_final_entity_json(client)
            else:
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
        if editgroups:
            return f"{editgroups}: {self.user_summary}" if self.user_summary else editgroups
        else:
            return self.user_summary if self.user_summary else ""

    def editgroups_summary(self):
        """
        Returns the EditGroups notice to put into the summary.
        """
        # Our regex for EditGroups:
        # ".*\[\[:toollabs:TOOLFORGE_TOOL_NAME/batch/(\d+)\|.*"
        tool = settings.TOOLFORGE_TOOL_NAME
        if tool is not None:
            batch_id = self.batch.id
            return f"[[:toollabs:{tool}/batch/{batch_id}|batch #{batch_id}]]"
        else:
            return ""

    def is_entity_json_patch(self):
        """
        Returns True for commands that work by modifying the entity's json,
        creating a json patch.
        """
        return self.operation in (
            self.Operation.SET_STATEMENT,
            self.Operation.ADD_ALIAS,
        )

    @property
    def can_combine_with_next(self):
        """
        Defines if the command should just return the
        modified entity json, because connecting to the API
        will be done by the next command.
        """
        return getattr(self, "_can_combine_with_next", False)

    def check_combination(self, previous_entity_json: Optional[dict], next: Optional["BatchCommand"]):
        """
        Caches the previous_entity_json as given, even if None.

        Checks combination with next command if available.

        Callers should always pass to previous_entity_json
        the previous command's `final_entity_json` property.
        """
        self._can_combine_with_next = (
            self.is_entity_json_patch()
            and next is not None
            and next.is_entity_json_patch()
            and self.entity_id() == next.entity_id()
        )
        self.previous_entity_json = previous_entity_json

    def get_original_entity_json(self, client: Client):
        """
        Returns the original entity json.

        Used for calculating the final patch send to the API.

        TODO: think of a way of caching this. The first command
        in the sequence would have to store that somewhere.
        Or Batch.run becomes more complicated or we save it
        in a dedicated cache.
        """
        return client.get_entity(self.entity_id())

    def get_previous_entity_json(self, client: Client):
        """
        Returns the previous entity json. Has cache.

        Used for calculating the final entity json to pass along
        to the next command.
        """
        cached = getattr(self, "previous_entity_json", None)
        entity = cached if cached is not None else client.get_entity(self.entity_id())
        logger.debug(f"[{self}] previous_entity_json={entity}")
        return entity

    def get_final_entity_json(self, client: Client) -> dict:
        """
        Returns the final entity json, applying the operations.
        """
        entity = self.get_previous_entity_json(client)
        self.update_entity_json(entity)
        return entity

    def update_entity_json(self, entity: dict):
        """
        Modifies the entity json in-place.
        """
        if self.operation == self.Operation.SET_STATEMENT:
            self._update_entity_statements(entity)
        elif self.operation == self.Operation.ADD_ALIAS:
            self._update_entity_aliases(entity)

    def _update_entity_statements(self, entity: dict):
        """
        Modifies the entity json statements in-place.
        """
        index = None
        statements = entity["statements"].setdefault(self.prop, [])
        for i, statement in enumerate(statements):
            if statement["value"] == self.statement_api_value:
                index = i
        if index is None:
            entity["statements"][self.prop].append(dict())
            index = -1
        self.update_statement(entity["statements"][self.prop][index])

    def _update_entity_aliases(self, entity: dict):
        """
        Modifies the entity aliases in-place.
        """
        entity["aliases"].setdefault(self.language, [])
        for alias in self.value_value:
            entity["aliases"][self.language].append(alias)

    def entity_patch(self, client: Client):
        """
        Calculates the entity json patch to send to the API.

        The cached entity json will be the baseline to work with,
        but the patch needs to be calculated using the original
        entity json, since that's what exists in the wikibase server.

        TODO: maybe cache that original as well to not make
        two requests?
        """
        original = self.get_original_entity_json(client)
        entity = self.get_previous_entity_json(client)
        self.update_entity_json(entity)
        return jsonpatch.JsonPatch.from_diff(original, entity).patch

    def api_payload(self, client: Client):
        """
        Returns the data that is sent to the Wikibase API through the body.
        """
        match self.operation:
            case self.Operation.CREATE_ITEM:
                return {"item": {}}
            case self.Operation.SET_STATEMENT:
                return {"patch": self.entity_patch(client)}
            case self.Operation.SET_SITELINK:
                return {
                    "sitelink": {
                        "title": self.value_value,
                        "badges": [],
                    },
                }
            case self.Operation.SET_LABEL:
                return {"label": self.value_value}
            case self.Operation.SET_DESCRIPTION:
                return {"description": self.value_value}
            case self.Operation.ADD_ALIAS:
                return {"patch": self.entity_patch(client)}
            case _:
                return {}

    def api_body(self, client: Client):
        """
        Returns the final Wikibase API body.

        Joins the api payload with bot marking = False and the edit summary.
        """
        body = self.api_payload(client)
        body["bot"] = False
        body["comment"] = self.edit_summary()
        return body

    def send_to_api(self, client: Client) -> dict:
        """
        Sends the operation to the Wikibase API.

        # Raises

        - `NotImplementedError` if the operation
        is not implemented.
        """
        match self.operation:
            case self.Operation.CREATE_PROPERTY | self.Operation.REMOVE_ALIAS:
                raise NotImplementedError()
            case (
                    self.Operation.CREATE_ITEM |
                    self.Operation.SET_STATEMENT |
                    self.Operation.REMOVE_STATEMENT_BY_ID | 
                    self.Operation.REMOVE_STATEMENT_BY_VALUE |
                    self.Operation.SET_LABEL |
                    self.Operation.SET_DESCRIPTION |
                    self.Operation.SET_SITELINK |
                    self.Operation.ADD_ALIAS
                ):
                return self.send_basic(client)
            case (
                    self.Operation.REMOVE_LABEL |
                    self.Operation.REMOVE_DESCRIPTION |
                    self.Operation.REMOVE_SITELINK
                ):
                return self.send_ignoring_404(client)
        return {}

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

    def operation_method_and_endpoint(self, client: Client):
        """
        Returns a tuple of HTTP method and the endpoint
        necessary for the operation.
        """
        match self.operation:
            case self.Operation.CREATE_ITEM:
                return ("POST", "/entities/items")
            case self.Operation.SET_STATEMENT:
                return ("PATCH", Client.wikibase_entity_endpoint(self.entity_id(), ""))
            case self.Operation.SET_LABEL:
                return ("PUT", Client.wikibase_entity_endpoint(self.entity_id(), f"/labels/{self.language}"))
            case self.Operation.SET_DESCRIPTION:
                return ("PUT", Client.wikibase_entity_endpoint(self.entity_id(), f"/descriptions/{self.language}"))
            case self.Operation.SET_SITELINK:
                return ("PUT", Client.wikibase_entity_endpoint(self.entity_id(), f"/sitelinks/{self.sitelink}"))
            case self.Operation.REMOVE_LABEL:
                return ("DELETE", Client.wikibase_entity_endpoint(self.entity_id(), f"/labels/{self.language}"))
            case self.Operation.REMOVE_DESCRIPTION:
                return ("DELETE", Client.wikibase_entity_endpoint(self.entity_id(), f"/descriptions/{self.language}"))
            case self.Operation.REMOVE_SITELINK:
                return ("DELETE", Client.wikibase_entity_endpoint(self.entity_id(), f"/sitelinks/{self.sitelink}"))
            case self.Operation.ADD_ALIAS:
                return ("PATCH", Client.wikibase_entity_endpoint(self.entity_id(), ""))
            case self.Operation.REMOVE_STATEMENT_BY_ID | self.Operation.REMOVE_STATEMENT_BY_VALUE:
                statement_id = self.statement_id(client)
                return ("DELETE", f"/statements/{statement_id}")

    def send_basic(self, client: Client):
        """
        Sends the request
        """
        method, endpoint = self.operation_method_and_endpoint(client)
        body = self.api_body(client)
        return client.wikibase_request_wrapper(method, endpoint, body)

    def send_ignoring_404(self, client: Client):
        """
        Sends the request ignoring 404 error codes.
        """
        try:
            return self.send_basic(client)
        except UserError as e:
            if e.status == 404:
                return e.response_json
            else:
                raise e

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
            return None

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
