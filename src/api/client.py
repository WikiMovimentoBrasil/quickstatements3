import requests


class Client:
    BASE_URL = "https://www.mediawiki.org/w/rest.php/"
    ENDPOINT_PROFILE = f"{BASE_URL}oauth2/resource/profile"

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
            endpoint, headers=self.headers()
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
