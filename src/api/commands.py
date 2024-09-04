from core.models import BatchCommand
from web.models import Token

from .client import Client
from .exceptions import ApiNotImplemented
from .exceptions import InvalidPropertyDataType
from .exceptions import NoToken
from .exceptions import NoStatementsForThatProperty
from .exceptions import NoStatementsWithThatValue


class ApiCommandBuilder:
    def __init__(self, command):
        self.command = command

    def build_and_send(self):
        api_command = self.build()
        return api_command.send()

    def build(self):
        if self.command.action == BatchCommand.ACTION_ADD:
            if self.command.json["what"] == "statement":
                return AddStatement(self.command)
            elif self.command.json["what"] in ["label", "description", "alias"]:
                return AddLabelDescriptionOrAlias(self.command)
            elif self.command.json["what"] == "sitelink":
                return AddSitelink(self.command)
        elif (
            self.command.action == BatchCommand.ACTION_CREATE
            and self.command.json["type"] == "item"
        ):
            return CreateItem(self.command)
        elif (
            self.command.action == BatchCommand.ACTION_REMOVE
            and self.command.json["what"] == "statement"
        ):
            return RemoveStatement(self.command)

        raise ApiNotImplemented()


class Utilities:
    def client(self):
        try:
            username = self.command.batch.user
            # TODO: maybe save the user directly in the Batch,
            # so that we don't have to query by username?
            token = Token.objects.get(user__username=username).value
            return Client.from_token(token)
        except Token.DoesNotExist:
            raise NoToken(username)

    def full_body(self):
        body = self.body()
        body["comment"] = self._comment()
        body["bot"] = False
        return body

    def _comment(self):
        """
        Returns the command's summary if it has one
        """
        return self.command.json.get("summary", "")


class AddStatement(Utilities):
    def __init__(self, command):
        self.command = command

        j = self.command.json
        self.entity_id = j["entity"]["id"]
        self.property_id = j["property"]

        value = j["value"]
        self.data_type = value["type"]
        self.value = value["value"]
        self.references = j.get("references", [])
        self.qualifiers = j.get("qualifiers", [])

        self.verify_data_type()

    def verify_data_type(self):
        client = self.client()
        needed_data_type = client.get_property_data_type(self.property_id)

        if needed_data_type != self.data_type:
            raise InvalidPropertyDataType(
                self.property_id,
                self.data_type,
                needed_data_type,
            )

    def body(self):
        all_quali = [
            {
                "property": {"id": q["property"]},
                "value": {
                    "content": q["value"]["value"],
                    "type": "value",
                },
            }
            for q in self.qualifiers
        ]

        all_refs = []
        for ref in self.references:
            fixed_parts = []
            for part in ref:
                fixed_parts.append(
                    {
                        "property": {"id": part["property"]},
                        "value": {
                            "content": part["value"]["value"],
                            "type": "value",
                        },
                    }
                )
            all_refs.append({"parts": fixed_parts})

        return {
            "statement": {
                "property": {
                    "id": self.property_id,
                },
                "value": {
                    "content": self.value,
                    "type": "value",
                },
                "qualifiers": all_quali,
                "references": all_refs,
            }
        }

    def send(self):
        full_body = self.full_body()
        client = self.client()
        return client.add_statement(self.entity_id, full_body)


class AddLabelDescriptionOrAlias(Utilities):
    def __init__(self, command):
        self.command = command

        j = self.command.json

        self.what = j["what"]
        self.entity_id = j["item"]
        self.language = j["language"]
        self.value = j["value"]["value"]

    def body(self):
        if self.what != "alias":
            path = f"/{self.language}"
        else:
            path = f"/{self.language}/0"

        return {
            "patch": [
                {
                    "op": "add",
                    "path": path,
                    "value": self.value,
                }
            ]
        }

    def send(self):
        full_body = self.full_body()
        client = self.client()
        if self.what == "label":
            return client.add_label(self.entity_id, full_body)
        elif self.what == "description":
            return client.add_description(self.entity_id, full_body)
        elif self.what == "alias":
            return client.add_alias(self.entity_id, full_body)
        else:
            raise ValueError("'what' is not label, description or alias.")


class AddSitelink(Utilities):
    def __init__(self, command):
        self.command = command

        j = self.command.json

        self.what = j["what"]
        self.entity_id = j["item"]
        self.site = j["site"]
        self.value = j["value"]["value"]

    def body(self):
        return {
            "patch": [
                {
                    "op": "replace",
                    "path": f"/{self.site}/title",
                    "value": self.value,
                }
            ]
        }

    def send(self):
        full_body = self.full_body()
        client = self.client()
        return client.add_sitelink(self.entity_id, full_body)


class CreateItem(Utilities):
    def __init__(self, command):
        self.command = command

    def body(self):
        return {"item": {}}

    def send(self):
        full_body = self.full_body()
        client = self.client()
        return client.create_item(full_body)


class RemoveStatement(Utilities):
    def __init__(self, command):
        self.command = command

        j = self.command.json

        self.entity_id = j["entity"]["id"]
        self.property_id = j["property"]
        self.value = j["value"]["value"]

        self.load_ids_to_delete()

    def load_ids_to_delete(self):
        ids_to_delete = []

        statements = self._get_statements_for_our_property()

        for statement in statements:
            id = statement["id"]
            value = statement["value"]["content"]

            if value == self.value:
                ids_to_delete.append(id)

        if len(ids_to_delete) == 0:
            raise NoStatementsWithThatValue(self.entity_id, self.property_id, self.value)

        self.ids_to_delete = ids_to_delete

    def _get_statements_for_our_property(self):
        client = self.client()

        all_statements = client.get_statements(self.entity_id)
        our_statements = all_statements.get(self.property_id, [])

        if len(our_statements) == 0:
            raise NoStatementsForThatProperty(self.entity_id, self.property_id)

        return our_statements

    def body(self):
        return {}

    def send(self):
        full_body = self.full_body()
        client = self.client()
        responses = []
        for id in self.ids_to_delete:
            res = client.delete_statement(id, full_body)
            responses.append(res)
        return responses
