import os
import requests
import logging

from web.models import Token

from .exceptions import EntityTypeNotImplemented
from .exceptions import NonexistantPropertyOrNoDataType
from .exceptions import UserError
from .exceptions import ServerError
from .exceptions import NoToken
from .exceptions import InvalidPropertyValueType
from .exceptions import NoValueTypeForThisDataType

logger = logging.getLogger("qsts3")


def cache_with_first_arg(cache_name):
    """
    Returns a decorator that caches the value in a dictionary cache with `cache_name`,
    using as key the first argument of the method.

    If there is not first argument or first keyword argument, it uses a generic key.
    """

    def decorator(method):
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, cache_name):
                setattr(self, cache_name, {})

            if len(args) >= 1:
                key = args[0]
            elif len(kwargs) >= 1:
                key = next(iter(kwargs.values()))
            else:
                key = "key"

            cache = getattr(self, cache_name)

            if cache.get(key) is not None:
                return cache.get(key)
            else:
                value = method(self, *args, **kwargs)
                cache[key] = value
                return value

        return wrapper

    return decorator


class Client:
    BASE_URL = "https://www.mediawiki.org/w/rest.php/"
    ENDPOINT_PROFILE = f"{BASE_URL}oauth2/resource/profile"
    WIKIBASE_URL = os.getenv(
        "WIKIBASE_URL",
        "https://www.wikidata.org/w/rest.php/wikibase/v0",
    )
    # TODO: get this from /property-data-types
    DATA_TYPE_TO_VALUE_TYPE = {
        "commonsMedia": "string",
        "geo-shape": "string",
        "tabular-data": "string",
        "url": "string",
        "external-id": "string",
        "wikibase-item": "wikibase-entityid",
        "wikibase-property": "wikibase-entityid",
        "globe-coordinate": "globecoordinate",
        "monolingualtext": "monolingualtext",
        "quantity": "quantity",
        "string": "string",
        "time": "time",
        "musical-notation": "string",
        "math": "string",
        "wikibase-lexeme": "wikibase-entityid",
        "wikibase-form": "wikibase-entityid",
        "wikibase-sense": "wikibase-entityid",
        "entity-schema": "wikibase-entityid",
    }

    def __init__(self, token):
        self.token = token
        self.value_type_cache = {}
        self.labels_cache = {}

    def __str__(self):
        return "API Client with token [redacted]"

    # ---
    # Constructors
    # ---

    @classmethod
    def from_token(cls, token):
        return cls(token)

    @classmethod
    def from_user(cls, user):
        return cls.from_username(user.username)

    @classmethod
    def from_username(cls, username):
        try:
            token = Token.objects.get(user__username=username).value
            return cls.from_token(token)
        except Token.DoesNotExist:
            raise NoToken(username)

    # ---
    # Utilities
    # ----

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

    def wikibase_entity_url(self, entity_id, entity_endpoint):
        endpoint = self.wikibase_entity_endpoint(entity_id, entity_endpoint)
        return self.wikibase_url(endpoint)

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
    @cache_with_first_arg("value_type_cache")
    def get_property_value_type(self, property_id):
        """
        Returns the expected value type of the property.

        Returns the value type as a string.

        Uses a dictionary attribute for caching.
        """
        endpoint = f"/entities/properties/{property_id}"
        url = self.wikibase_url(endpoint)

        res = self.get(url).json()

        try:
            data_type = res["data_type"]
        except KeyError:
            raise NonexistantPropertyOrNoDataType(property_id)

        try:
            value_type = self.data_type_to_value_type(data_type)
        except KeyError:
            raise NoValueTypeForThisDataType(property_id, data_type)

        return value_type

    def data_type_to_value_type(self, data_type):
        """
        Gets the associated value type for a property's data type.

        # Raises

        - `KeyError` if there is no associated value type.
        """
        return self.DATA_TYPE_TO_VALUE_TYPE[data_type]

    def verify_value_type(self, property_id, value_type):
        """
        Verifies if the value type of the property with `property_id` matches `value_type`.

        If not, raises `InvalidPropertyValueType`.

        Value types "somevalue" and "novalue" are allowed for every property.
        """
        if value_type not in ["somevalue", "novalue"]:
            needed = self.get_property_value_type(property_id)
            if needed != value_type:
                raise InvalidPropertyValueType(property_id, value_type, needed)

    @cache_with_first_arg("label_cache")
    def get_labels(self, entity_id):
        """
        Returns all labels for an entity: a dictionary with the language
        code as the keys.
        """
        url = self.wikibase_entity_url(entity_id, "/labels")
        return self.get(url).json()

    def get_statements(self, entity_id):
        """
        Returns all statements for an entity in the form of a dictionary.

        The key is the property id, and the value is an array with
        the statement objects.
        """
        url = self.wikibase_entity_url(entity_id, "/statements")
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
        self.label_cache = {}
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
