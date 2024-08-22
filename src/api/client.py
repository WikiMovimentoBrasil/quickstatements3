import os
import requests
import logging

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

    def post(self, url, body):
        logger.debug(f"POST request at {url} | sending with body {body}")
        res = requests.post(url, json=body, headers=self.headers())
        logger.debug(f"POST request at {url} | response: {res.json()}")
        return res

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
    # Wikibase GET/reading
    # ---
    def full_wikibase_url(self, endpoint):
        return f"{self.WIKIBASE_URL}{endpoint}"

    def get_property_data_type(self, property_id):
        """
        Returns the expected data type of the property.

        Returns the data type as a string.
        """
        endpoint = f"/entities/properties/{property_id}"
        url = self.full_wikibase_url(endpoint)

        # TODO: add caching
        res = self.get(url).json()

        try:
            data_type = res["data_type"]
            return data_type
        except KeyError:
            raise ValueError("The property does not exist or does not have a data type")

    # ---
    # Wikibase POST/editing
    # ---
    def add_statement(self, item_id, body):
        endpoint = f"/entities/items/{item_id}/statements"
        url = self.full_wikibase_url(endpoint)
        res = self.post(url, body)
        res.raise_for_status()
        return res.json()
