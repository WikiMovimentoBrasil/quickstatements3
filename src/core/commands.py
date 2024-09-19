from .client import Client
from .exceptions import ApiNotImplemented
from .exceptions import NoStatementsForThatProperty
from .exceptions import NoStatementsWithThatValue


def parser_value_to_api_value(parser_value):
    # TODO: refactor parser to use this
    # format for values, instead of having to reprocess them here.
    # Basically, types can be "value", "novalue" and "somevalue",
    # when working with the API. The data type is not needed.
    # It is only used when checking with the property's data type,
    # so it's still useful, but it can be saved not in value's type.
    if parser_value["type"] in ["novalue", "somevalue"]:
        return {
            "type": parser_value["type"],
        }
    else:
        return {
            "type": "value",
            "content": parser_value["value"],
        }


class ApiCommandBuilder:
    def __init__(self, command, client):
        self.command = command
        self.client = client

    def build_and_send(self):
        api_command = self.build()
        return api_command.send(self.client)

    def build(self):
        cmd = self.command

        if cmd.is_add_statement():
            return AddStatement(cmd)
        elif cmd.is_add_label_description_alias():
            return AddLabelDescriptionOrAlias(cmd)
        elif cmd.is_add_sitelink():
            return AddSitelink(cmd)
        elif cmd.is_create_item():
            return CreateItem(cmd)
        elif cmd.is_create_property():
            raise ApiNotImplemented()
        elif cmd.is_remove_statement_by_id():
            return RemoveStatementById(cmd)
        elif cmd.is_remove_statement_by_value():
            return RemoveStatement(cmd)
        else:
            raise ApiNotImplemented()


class Utilities:
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

        self.parser_value = j["value"]
        self.data_type = self.parser_value["type"]
        self.references = j.get("references", [])
        self.qualifiers = j.get("qualifiers", [])

    def body(self):
        all_quali = [
            {
                "property": {"id": q["property"]},
                "value": parser_value_to_api_value(q["value"]),
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
                        "value": parser_value_to_api_value(part["value"]),
                    }
                )
            all_refs.append({"parts": fixed_parts})

        return {
            "statement": {
                "property": {
                    "id": self.property_id,
                },
                "value": parser_value_to_api_value(self.parser_value),
                "qualifiers": all_quali,
                "references": all_refs,
            }
        }

    def send(self, client: Client):
        full_body = self.full_body()
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

    def send(self, client: Client):
        full_body = self.full_body()
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

    def send(self, client: Client):
        full_body = self.full_body()
        return client.add_sitelink(self.entity_id, full_body)


class CreateItem(Utilities):
    def __init__(self, command):
        self.command = command

    def body(self):
        return {"item": {}}

    def send(self, client: Client):
        full_body = self.full_body()
        return client.create_item(full_body)


class RemoveStatement(Utilities):
    def __init__(self, command):
        self.command = command

        j = self.command.json

        self.entity_id = j["entity"]["id"]
        self.property_id = j["property"]
        self.parser_value = j["value"]
        self.api_value = parser_value_to_api_value(self.parser_value)

        self.load_ids_to_delete()

    def load_ids_to_delete(self):
        ids_to_delete = []

        statements = self._get_statements_for_our_property()

        for statement in statements:
            id = statement["id"]
            api_value = statement["value"]

            if api_value == self.api_value:
                ids_to_delete.append(id)

        if len(ids_to_delete) == 0:
            raise NoStatementsWithThatValue(
                self.entity_id,
                self.property_id,
                self.parser_value["value"],
            )

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

    def send(self, client: Client):
        full_body = self.full_body()
        responses = []
        for id in self.ids_to_delete:
            res = client.delete_statement(id, full_body)
            responses.append(res)
        return responses


class RemoveStatementById(Utilities):
    def __init__(self, command):
        self.command = command

        j = self.command.json
        self.id = j["id"]

    def body(self):
        return {}

    def send(self, client: Client):
        full_body = self.full_body()
        res = client.delete_statement(self.id, full_body)
        return res
