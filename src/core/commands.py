from .client import Client


def parser_value_to_api_value(parser_value):
    # TODO: refactor parser to use this
    # format for values, instead of having to reprocess them here.
    # Basically, types can be "value", "novalue" and "somevalue",
    # when working with the API. The value type is not needed.
    # It is only used when checking with the property's value type,
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
        else:
            raise NotImplementedError()


class Utilities:
    def full_body(self):
        body = self.body()
        body["comment"] = self.command.edit_summary()
        body["bot"] = False
        return body


class AddStatement(Utilities):
    def __init__(self, command):
        self.command = command

        j = self.command.json
        self.entity_id = j["entity"]["id"]
        self.property_id = j["property"]

        self.parser_value = j["value"]
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
