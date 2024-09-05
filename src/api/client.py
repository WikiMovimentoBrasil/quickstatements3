import os
import requests
import logging

from web.models import Token

from .exceptions import EntityTypeNotImplemented
from .exceptions import NonexistantPropertyOrNoDataType
from .exceptions import UserError
from .exceptions import ServerError

logger = logging.getLogger("qsts3")


class Client:
    BASE_URL = "https://www.mediawiki.org/w/rest.php/"
    ENDPOINT_PROFILE = f"{BASE_URL}oauth2/resource/profile"
    WIKIBASE_URL = os.getenv(
        "WIKIBASE_URL",
        "https://www.wikidata.org/w/rest.php/wikibase/v0",
    )

    def __init__(self, token):
        self.token = token

    def __str__(self):
        return "API Client with token [redacted]"

    @classmethod
    def from_token(cls, token):
        return cls(token)

    @classmethod
    def from_user(cls, user):
        token = Token.objects.get(user=user).value
        return cls.from_token(token)

    @classmethod
    def from_username(cls, username):
        token = Token.objects.get(user__username=username).value
        return cls.from_token(token)

    def headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def get(self, url):
        logger.debug(f"Sending GET request at {url}")
        return requests.get(url, headers=self.headers())

    def raise_for_status(self, response):
        j = response.json()
        status = response.status_code
        if 400 <= status <= 499:
            raise UserError(j.get("code"), j.get("message"))
        if 500 <= status <= 599:
            raise ServerError(j)

    # ---
    # Auth
    # ---
    def get_username(self):
        response = self.get(self.ENDPOINT_PROFILE).json()
        try:
            username = response["username"]
            return username
        except KeyError:
            raise ValueError(
                "The token did not return a valid username.",
                response,
            )

    # ---
    # Wikibase utilities
    # ---
    def wikibase_url(self, endpoint):
        return f"{self.WIKIBASE_URL}{endpoint}"

    def wikibase_entity_endpoint(self, entity_id, entity_endpoint):
        if entity_id.startswith("Q"):
            base = "/entities/items"
        elif entity_id.startswith("P"):
            base = "/entities/properties"
        else:
            raise EntityTypeNotImplemented(entity_id)

        return f"{base}/{entity_id}{entity_endpoint}"

    def wikibase_request_wrapper(self, method, endpoint, body):
        kwargs = {
            "json": body,
            "headers": self.headers(),
        }

        url = self.wikibase_url(endpoint)

        logger.debug(f"{method} request at {url} | sending with body {body}")

        if method == "POST":
            res = requests.post(url, **kwargs)
        elif method == "PATCH":
            res = requests.patch(url, **kwargs)
        elif method == "DELETE":
            res = requests.delete(url, **kwargs)
        else:
            raise ValueError("not implemented")

        logger.debug(f"{method} request at {url} | response: {res.json()}")
        self.raise_for_status(res)
        return res.json()

    def wikibase_post(self, endpoint, body):
        return self.wikibase_request_wrapper("POST", endpoint, body)

    def wikibase_patch(self, endpoint, body):
        return self.wikibase_request_wrapper("PATCH", endpoint, body)

    def wikibase_delete(self, endpoint, body):
        return self.wikibase_request_wrapper("DELETE", endpoint, body)

    # ---
    # Wikibase GET/reading
    # ---
    def get_property_data_type(self, property_id):
        """
        Returns the expected data type of the property.

        Returns the data type as a string.
        """
        endpoint = f"/entities/properties/{property_id}"
        url = self.wikibase_url(endpoint)

        # TODO: add caching
        res = self.get(url).json()

        try:
            data_type = res["data_type"]
            return data_type
        except KeyError:
            raise NonexistantPropertyOrNoDataType(property_id)

    def get_statements(self, entity_id):
        """
        Returns all statements for an entity in the form of a dictionary.

        The key is the property id, and the value is an array with
        the statement objects.
        """
        endpoint = self.wikibase_entity_endpoint(entity_id, "/statements")
        url = self.wikibase_url(endpoint)
        return self.get(url).json()

    # ---
    # Wikibase POST/editing
    # ---
    def create_item(self, body):
        endpoint = "/entities/items"
        return self.wikibase_post(endpoint, body)

    def add_statement(self, entity_id, body):
        endpoint = self.wikibase_entity_endpoint(entity_id, "/statements")
        return self.wikibase_post(endpoint, body)

    def add_label(self, entity_id, body):
        endpoint = self.wikibase_entity_endpoint(entity_id, "/labels")
        return self.wikibase_patch(endpoint, body)

    def add_description(self, entity_id, body):
        endpoint = self.wikibase_entity_endpoint(entity_id, "/descriptions")
        return self.wikibase_patch(endpoint, body)

    def add_alias(self, entity_id, body):
        endpoint = self.wikibase_entity_endpoint(entity_id, "/aliases")
        return self.wikibase_patch(endpoint, body)

    def add_sitelink(self, entity_id, body):
        endpoint = self.wikibase_entity_endpoint(entity_id, "/sitelinks")
        return self.wikibase_patch(endpoint, body)

    def delete_statement(self, statement_id, body):
        endpoint = f"/statements/{statement_id}"
        return self.wikibase_delete(endpoint, body)
