from core.models import BatchCommand
from .client import Client

from web.models import Token


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
        elif self.command.action == BatchCommand.ACTION_CREATE:
            return CreateItem(self.command)

        raise ValueError("Not Implemented")


class Utilities:
    def client(self):
        try:
            # TODO: maybe save the user directly in the Batch,
            # so that we don't have to query by username?
            token = Token.objects.get(user__username=self.command.batch.user).value
            return Client.from_token(token)
        except Token.DoesNotExist:
            raise ValueError("We don't have a token for that user")

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
        self.item_id = j["entity"]["id"]
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
            raise ValueError(
                (
                    f"Invalid data type for the property {self.property_id}: "
                    f"{self.data_type} was provided but it needs {needed_data_type}."
                )
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
        return client.add_statement(self.item_id, full_body)


class AddLabelDescriptionOrAlias(Utilities):
    def __init__(self, command):
        self.command = command

        j = self.command.json

        self.what = j["what"]
        self.item_id = j["item"]
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
            return client.add_label(self.item_id, full_body)
        elif self.what == "description":
            return client.add_description(self.item_id, full_body)
        elif self.what == "alias":
            return client.add_alias(self.item_id, full_body)
        else:
            raise ValueError("'what' is not label, description or alias.")


class AddSitelink(Utilities):
    def __init__(self, command):
        self.command = command

        j = self.command.json

        self.what = j["what"]
        self.item_id = j["item"]
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
        return client.add_sitelink(self.item_id, full_body)


class CreateItem(Utilities):
    def __init__(self, command):
        self.command = command

    def body(self):
        return {"item": {}}

    def send(self):
        full_body = self.full_body()
        client = self.client()
        return client.create_entity(full_body)
