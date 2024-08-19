import requests


class Client:
    BASE_URL = "https://www.mediawiki.org/w/rest.php/"
    ENDPOINT_PROFILE = f"{BASE_URL}oauth2/resource/profile"
    WIKIDATA_URL = "https://www.wikidata.org/w/rest.php/wikibase/v0"

    def __init__(self, token):
        self.token = token

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

    def wikidata_post(self, endpoint, body):
        print(f"Sending request at {endpoint} with body {body}")
        res = requests.post(
            f"{self.WIKIDATA_URL}{endpoint}",
            headers=self.headers(),
            json=body,
        )
        print(f"Response content: {res.json()}")
        res.raise_for_status()

    def wikidata_statement_post(self, item_id, body):
        endpoint = f"/entities/items/{item_id}/statements"
        return self.wikidata_post(endpoint, body)
