import os
import requests


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

    def request_get(self, endpoint):
        return requests.get(
            endpoint,
            headers=self.headers(),
        ).json()

    def get_username(self):
        response = self.request_get(self.ENDPOINT_PROFILE)
        try:
            username = response["username"]
            return username
        except KeyError:
            raise ValueError(
                "The token did not return a valid username.",
                response,
            )

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
        res = requests.get(url, headers=self.headers()).json()

        try:
            data_type = res["data_type"]
            return data_type
        except KeyError:
            raise ValueError("The property does not exist or does not have a data type")

    def wikidata_post(self, endpoint, body):
        print(f"Sending request at {endpoint} with body {body}")
        url = self.full_wikibase_url(endpoint)
        res = requests.post(
            url,
            headers=self.headers(),
            json=body,
        )
        print(f"Response content: {res.json()}")
        res.raise_for_status()

    def wikidata_statement_post(self, item_id, body):
        endpoint = f"/entities/items/{item_id}/statements"
        return self.wikidata_post(endpoint, body)
