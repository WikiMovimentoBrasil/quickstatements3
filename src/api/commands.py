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
        return {
            "statement": {
                "property": {
                    "id": self.property_id,
                },
                "value": {
                    "content": self.value,
                    "type": "value",
                },
            }
        }

    def send(self):
        full_body = self.full_body()
        client = self.client()
        return client.wikidata_statement_post(self.item_id, full_body)
