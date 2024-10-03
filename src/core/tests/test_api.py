import requests_mock

from django.test import TestCase

from core.client import Client
from core.exceptions import NonexistantPropertyOrNoDataType


class ApiMocker:
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


class ClientTests(TestCase):
    def api_client(self):
        return Client("TEST_TOKEN")

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
    def test_get_property_data_type(self, mocker):
        ApiMocker.property_data_type(mocker, "P1104", "quantity")
        data_type = self.api_client().get_property_data_type("P1104")
        self.assertEqual(data_type, "quantity")

    @requests_mock.Mocker()
    def test_get_property_data_type_error(self, mocker):
        ApiMocker.property_data_type_not_found(mocker, "P321341234")
        with self.assertRaises(NonexistantPropertyOrNoDataType):
            self.api_client().get_property_data_type("P321341234")

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
