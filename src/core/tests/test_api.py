import requests_mock
from datetime import timedelta

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache as django_cache
from django.utils.timezone import now
from django.conf import settings

from web.models import Token

from core.client import Client
from core.commands import ApiCommandBuilder
from core.exceptions import NonexistantPropertyOrNoDataType
from core.exceptions import NoValueTypeForThisDataType
from core.exceptions import InvalidPropertyValueType
from core.exceptions import UnauthorizedToken
from core.exceptions import ServerError
from core.parsers.v1 import V1CommandParser


class ApiMocker:
    # ---
    # OAuth
    # ---
    @classmethod
    def oauth_profile_endpoint(cls):
        return Client.ENDPOINT_PROFILE

    @classmethod
    def oauth_token_endpoint(cls):
        return f"{Client.BASE_REST_URL}/oauth2/access_token"

    @classmethod
    def access_token(cls, mocker, full_token):
        mocker.post(
            cls.oauth_token_endpoint(),
            json=full_token,
            status_code=200,
        )

    @classmethod
    def access_token_fails(cls, mocker):
        mocker.post(
            cls.oauth_token_endpoint(),
            json={"error": "error"},
            status_code=500,
        )

    @classmethod
    def login_success(cls, mocker, username):
        mocker.get(
            cls.oauth_profile_endpoint(),
            json={"username": username},
            status_code=200,
        )

    @classmethod
    def login_fail(cls, mocker):
        mocker.get(
            cls.oauth_profile_endpoint(),
            json={"error": "access denied"},
            status_code=401,
        )

    @classmethod
    def login_failed_server(cls, mocker):
        mocker.get(
            cls.oauth_profile_endpoint(),
            json={"error": "server error"},
            status_code=500,
        )

    @classmethod
    def is_autoconfirmed(cls, mocker):
        mocker.get(
            cls.oauth_profile_endpoint(),
            json={"groups": ["*", "autoconfirmed"]},
            status_code=200,
        )

    @classmethod
    def is_not_autoconfirmed(cls, mocker):
        mocker.get(
            cls.oauth_profile_endpoint(),
            json={"groups": ["*"]},
            status_code=200,
        )

    @classmethod
    def autoconfirmed_failed_unauthorized(cls, mocker):
        mocker.get(
            cls.oauth_profile_endpoint(),
            json={"error": "unauthorized"},
            status_code=401,
        )

    @classmethod
    def autoconfirmed_failed_server(cls, mocker):
        mocker.get(
            cls.oauth_profile_endpoint(),
            json={"error": "server error"},
            status_code=500,
        )

    # ---
    # Wikibase
    # ---
    WIKIDATA_PROPERTY_DATA_TYPES = {
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

    @classmethod
    def wikibase_url(cls, endpoint):
        return f"{Client.WIKIBASE_URL}{endpoint}"

    @classmethod
    def property_data_type(cls, mocker, property_id, data_type):
        mocker.get(
            cls.wikibase_url(f"/entities/properties/{property_id}"),
            json={"data_type": data_type},
            status_code=200,
        )

    @classmethod
    def property_data_type_not_found(cls, mocker, property_id):
        mocker.get(
            cls.wikibase_url(f"/entities/properties/{property_id}"),
            json={"code": "property-not-found"},
            status_code=404,
        )

    @classmethod
    def create_item_failed_server(cls, mocker):
        mocker.post(
            cls.wikibase_url("/entities/items"),
            json={"error": "my-error-code"},
            status_code=500,
        )

    @classmethod
    def add_statement_successful(cls, mocker, item_id):
        mocker.post(
            cls.wikibase_url(f"/entities/items/{item_id}/statements"),
            json={"id": f"{item_id}$somestuff"},
            status_code=200,
        )

    @classmethod
    def add_statement_failed_server(cls, mocker, item_id):
        mocker.post(
            cls.wikibase_url(f"/entities/items/{item_id}/statements"),
            json={"error": "my-error-code"},
            status_code=500,
        )

    @classmethod
    def labels(cls, mocker, client, entity_id, labels):
        mocker.get(
            client.wikibase_entity_url(entity_id, "/labels"),
            json=labels,
            status_code=200,
        )

    @classmethod
    def create_item(cls, mocker, item_id):
        mocker.post(
            cls.wikibase_url("/entities/items"),
            json={"id": item_id},
            status_code=200,
        )

    @classmethod
    def property_data_types(cls, mocker, mapper):
        mocker.get(
            cls.wikibase_url("/property-data-types"),
            json=mapper,
            status_code=200,
        )

    @classmethod
    def wikidata_property_data_types(cls, mocker):
        cls.property_data_types(
            mocker,
            cls.WIKIDATA_PROPERTY_DATA_TYPES,
        )


class OAuthClientTests(TestCase):
    @requests_mock.Mocker()
    def test_refresh_expired_token(self, mocker):
        # Replacing microseconds to zero for ease of use when comparing
        # because microseconds aren't saved in the database.
        old_expires = now().replace(microsecond=0)
        new_expires = (now() + timedelta(hours=1)).replace(microsecond=0)
        ApiMocker.login_success(mocker, "WikiUser")
        ApiMocker.access_token(
            mocker,
            {
                "refresh_token": "new_refresh",
                "access_token": "new_access",
                "expires_at": new_expires.timestamp(),
            },
        )
        old_token = {
            "access_token": "old_access",
            "refresh_token": "old_refresh",
            "expires_at": old_expires.timestamp(),
        }
        user = User.objects.create(username="u")
        t = Token.objects.create_from_full_token(user, old_token)
        client = Client.from_token(t)
        self.assertTrue(client.token.is_expired())
        self.assertEqual(client.token.user.id, user.id)
        self.assertEqual(client.token.value, "old_access")
        self.assertEqual(client.token.refresh_token, "old_refresh")
        self.assertEqual(client.token.expires_at, old_expires)
        username = client.get_username()
        self.assertEqual(username, "WikiUser")
        self.assertEqual(client.token, t)
        self.assertFalse(client.token.is_expired())
        self.assertEqual(client.token.user.id, user.id)
        self.assertEqual(client.token.value, "new_access")
        self.assertEqual(client.token.refresh_token, "new_refresh")
        self.assertEqual(client.token.expires_at, new_expires)
        username = client.get_username()
        self.assertEqual(username, "WikiUser")
        self.assertEqual(client.token, t)
        self.assertFalse(client.token.is_expired())
        self.assertEqual(client.token.user.id, user.id)
        self.assertEqual(client.token.value, "new_access")
        self.assertEqual(client.token.refresh_token, "new_refresh")
        self.assertEqual(client.token.expires_at, new_expires)

    @requests_mock.Mocker()
    def test_dont_refresh_token(self, mocker):
        expires = (now() + timedelta(hours=2)).replace(microsecond=0)
        ApiMocker.login_success(mocker, "WikiUser")
        ApiMocker.access_token_fails(mocker)
        token = {
            "access_token": "access",
            "refresh_token": "refresh",
            "expires_at": expires.timestamp(),
        }
        user = User.objects.create(username="u")
        t = Token.objects.create_from_full_token(user, token)
        client = Client.from_token(t)
        self.assertFalse(client.token.is_expired())
        self.assertEqual(client.token.user.id, user.id)
        self.assertEqual(client.token.value, "access")
        self.assertEqual(client.token.refresh_token, "refresh")
        self.assertEqual(client.token.expires_at, expires)
        username = client.get_username()
        self.assertEqual(username, "WikiUser")
        self.assertFalse(client.token.is_expired())
        self.assertEqual(client.token.user.id, user.id)
        self.assertEqual(client.token.value, "access")
        self.assertEqual(client.token.refresh_token, "refresh")
        self.assertEqual(client.token.expires_at, expires)

    @requests_mock.Mocker()
    def test_failed_to_refresh_raises_unauthorized_token(self, mocker):
        expires = now().replace(microsecond=0)
        ApiMocker.login_success(mocker, "WikiUser")
        ApiMocker.access_token_fails(mocker)
        old_token = {
            "access_token": "access",
            "refresh_token": "refresh",
            "expires_at": expires.timestamp(),
        }
        user = User.objects.create(username="u")
        t = Token.objects.create_from_full_token(user, old_token)
        client = Client.from_token(t)
        self.assertTrue(client.token.is_expired())
        with self.assertRaises(UnauthorizedToken):
            client.get_username()


class ClientTests(TestCase):
    def tearDown(self):
        # this is needed for the property-data-types to work correctly,
        # since it uses the cache
        django_cache.clear()

    def api_client(self):
        user, _ = User.objects.get_or_create(username="test_token_user")
        token, _ = Token.objects.get_or_create(
            user=user,
            value="TEST_TOKEN",
        )
        return Client.from_token(token)

    def wikibase_url(self, endpoint):
        return f"{Client.WIKIBASE_URL}{endpoint}"

    def test_wikibase_entity_endpoint(self):
        client = self.api_client()
        self.assertEqual(
            client.wikibase_entity_endpoint("Q123", "/labels"),
            "/entities/items/Q123/labels",
        )
        self.assertEqual(
            client.wikibase_entity_endpoint("P444", "/statements"),
            "/entities/properties/P444/statements",
        )

    def test_wikibase_entity_url(self):
        client = self.api_client()
        self.assertEqual(
            client.wikibase_entity_url("P987", "/statements"),
            f"{client.WIKIBASE_URL}/entities/properties/P987/statements",
        )

    @requests_mock.Mocker()
    def test_get_property_value_type(self, mocker):
        ApiMocker.wikidata_property_data_types(mocker)
        ApiMocker.property_data_type(mocker, "P1104", "quantity")
        value_type = self.api_client().get_property_value_type("P1104")
        self.assertEqual(value_type, "quantity")

    @requests_mock.Mocker()
    def test_get_property_value_type_error(self, mocker):
        ApiMocker.wikidata_property_data_types(mocker)
        ApiMocker.property_data_type_not_found(mocker, "P321341234")
        with self.assertRaises(NonexistantPropertyOrNoDataType):
            self.api_client().get_property_value_type("P321341234")

    @requests_mock.Mocker()
    def test_no_value_type_for_a_data_type(self, mocker):
        ApiMocker.wikidata_property_data_types(mocker)
        ApiMocker.property_data_type(mocker, "P1", "idonotexist")
        with self.assertRaises(KeyError):
            self.api_client().data_type_to_value_type("idonotexist")
        with self.assertRaises(NoValueTypeForThisDataType):
            self.api_client().get_property_value_type("P1")

    @requests_mock.Mocker()
    def test_get_labels(self, mocker):
        entity_id = "Q123"
        labels = {
            "en": "English label",
            "pt": "Portuguese label",
        }
        client = self.api_client()
        ApiMocker.labels(mocker, client, entity_id, labels)
        returned_labels = client.get_labels(entity_id)
        self.assertEqual(labels, returned_labels)

    @requests_mock.Mocker()
    def test_verify_value_type(self, mocker):
        ApiMocker.wikidata_property_data_types(mocker)
        ApiMocker.property_data_type(mocker, "P1", "commonsMedia")
        ApiMocker.property_data_type(mocker, "P2", "geo-shape")
        ApiMocker.property_data_type(mocker, "P3", "tabular-data")
        ApiMocker.property_data_type(mocker, "P4", "url")
        ApiMocker.property_data_type(mocker, "P5", "external-id")
        ApiMocker.property_data_type(mocker, "P6", "wikibase-item")
        ApiMocker.property_data_type(mocker, "P7", "wikibase-property")
        ApiMocker.property_data_type(mocker, "P8", "globe-coordinate")
        ApiMocker.property_data_type(mocker, "P9", "monolingualtext")
        ApiMocker.property_data_type(mocker, "P10", "quantity")
        ApiMocker.property_data_type(mocker, "P11", "string")
        ApiMocker.property_data_type(mocker, "P12", "time")
        ApiMocker.property_data_type(mocker, "P13", "musical-notation")
        ApiMocker.property_data_type(mocker, "P14", "math")
        ApiMocker.property_data_type(mocker, "P15", "wikibase-lexeme")
        ApiMocker.property_data_type(mocker, "P16", "wikibase-form")
        ApiMocker.property_data_type(mocker, "P17", "wikibase-sense")
        ApiMocker.property_data_type(mocker, "P18", "entity-schema")

        client = self.api_client()

        all_value_types = (
            "globecoordinate",
            "monolingualtext",
            "quantity",
            "string",
            "time",
            "wikibase-entityid",
        )

        correct_value_types = {
            "P1": "string",
            "P2": "string",
            "P3": "string",
            "P4": "string",
            "P5": "string",
            "P6": "wikibase-entityid",
            "P7": "wikibase-entityid",
            "P8": "globecoordinate",
            "P9": "monolingualtext",
            "P10": "quantity",
            "P11": "string",
            "P12": "time",
            "P13": "string",
            "P14": "string",
            "P15": "wikibase-entityid",
            "P16": "wikibase-entityid",
            "P17": "wikibase-entityid",
            "P18": "wikibase-entityid",
        }

        for i in range(18):
            property_id = f"P{i + 1}"
            client.verify_value_type(property_id, correct_value_types[property_id])

        for i in range(18):
            property_id = f"P{i + 1}"
            for v in all_value_types:
                if v != correct_value_types[property_id]:
                    with self.assertRaises(InvalidPropertyValueType):
                        client.verify_value_type(property_id, v)

    @requests_mock.Mocker()
    def test_is_autoconfirmed(self, mocker):
        ApiMocker.is_autoconfirmed(mocker)
        client = self.api_client()
        self.assertTrue(client.get_is_autoconfirmed())

    @requests_mock.Mocker()
    def test_is_not_autoconfirmed(self, mocker):
        ApiMocker.is_not_autoconfirmed(mocker)
        client = self.api_client()
        self.assertFalse(client.get_is_autoconfirmed())

    @requests_mock.Mocker()
    def test_autoconfirmed_failed(self, mocker):
        ApiMocker.autoconfirmed_failed_server(mocker)
        client = self.api_client()
        with self.assertRaises(ServerError):
            client.get_is_autoconfirmed()

    @requests_mock.Mocker()
    def test_autoconfirmed_unauthorized(self, mocker):
        ApiMocker.autoconfirmed_failed_unauthorized(mocker)
        client = self.api_client()
        with self.assertRaises(UnauthorizedToken):
            client.get_is_autoconfirmed()

    @requests_mock.Mocker()
    def test_login(self, mocker):
        ApiMocker.login_success(mocker, "username")
        client = self.api_client()
        self.assertEqual(client.get_username(), "username")

    @requests_mock.Mocker()
    def test_login_unauthorized(self, mocker):
        ApiMocker.login_fail(mocker)
        client = self.api_client()
        with self.assertRaises(UnauthorizedToken):
            client.get_profile()
        with self.assertRaises(UnauthorizedToken):
            client.get_username()
        with self.assertRaises(UnauthorizedToken):
            client.get_user_groups()
        with self.assertRaises(UnauthorizedToken):
            client.get_is_autoconfirmed()

    @requests_mock.Mocker()
    def test_login_failed_server(self, mocker):
        ApiMocker.login_failed_server(mocker)
        client = self.api_client()
        with self.assertRaises(ServerError):
            client.get_profile()
        with self.assertRaises(ServerError):
            client.get_username()
        with self.assertRaises(ServerError):
            client.get_user_groups()
        with self.assertRaises(ServerError):
            client.get_is_autoconfirmed()

    @requests_mock.Mocker()
    def test_arbitrary_property_data_types(self, mocker):
        mapper = {"data1": "value1", "data2": "value2"}
        ApiMocker.property_data_types(mocker, mapper)

        client = self.api_client()
        self.assertEqual(client.get_property_data_types(), mapper)

        # ---

        ApiMocker.property_data_type(mocker, "P1", "data1")
        ApiMocker.property_data_type(mocker, "P2", "data2")

        client.verify_value_type("P1", "value1")
        client.verify_value_type("P2", "value2")

        # ---

        with self.assertRaises(InvalidPropertyValueType):
            client.verify_value_type("P1", "value2")

        with self.assertRaises(InvalidPropertyValueType):
            client.verify_value_type("P2", "value1")

        with self.assertRaises(InvalidPropertyValueType):
            client.verify_value_type("P2", "abcdef")

        # ---

        # not present in mapper:
        ApiMocker.property_data_type(mocker, "P3", "data3")

        with self.assertRaises(NoValueTypeForThisDataType):
            client.verify_value_type("P3", "value3")
