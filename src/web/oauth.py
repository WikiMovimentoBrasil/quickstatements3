import os

from authlib.integrations.django_client import OAuth

BASE_REST_URL = os.getenv(
    "BASE_REST_URL",
    "https://www.wikidata.org/w/rest.php",
)

oauth = OAuth()
oauth.register(
    name="mediawiki",
    client_id=os.getenv("OAUTH_CLIENT_ID"),
    client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
    access_token_url=f"{BASE_REST_URL}/oauth2/access_token",
    authorize_url=f"{BASE_REST_URL}/oauth2/authorize",
)
