import os
import requests
import logging

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

    @staticmethod
    def from_token(token):
        return Client(token)

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
        else:
            raise ValueError("not implemented")

        logger.debug(f"{method} request at {url} | response: {res.json()}")
        self.raise_for_status(res)
        return res.json()

    def wikibase_post(self, endpoint, body):
        return self.wikibase_request_wrapper("POST", endpoint, body)

    def wikibase_patch(self, endpoint, body):
        return self.wikibase_request_wrapper("PATCH", endpoint, body)

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

    # ---
    # Wikibase POST/editing
    # ---
    def create_entity(self, body):
        endpoint = "/entities/items"
        return self.wikibase_post(endpoint, body)

    def add_statement(self, item_id, body):
        endpoint = f"/entities/items/{item_id}/statements"
        return self.wikibase_post(endpoint, body)

    def add_label(self, item_id, body):
        endpoint = f"/entities/items/{item_id}/labels"
        return self.wikibase_patch(endpoint, body)

    def add_description(self, item_id, body):
        endpoint = f"/entities/items/{item_id}/descriptions"
        return self.wikibase_patch(endpoint, body)

    def add_alias(self, item_id, body):
        endpoint = f"/entities/items/{item_id}/aliases"
        return self.wikibase_patch(endpoint, body)

    def add_sitelink(self, item_id, body):
        endpoint = f"/entities/items/{item_id}/sitelinks"
        return self.wikibase_patch(endpoint, body)
