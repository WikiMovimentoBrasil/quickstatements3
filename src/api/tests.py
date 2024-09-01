import requests_mock

from django.test import TestCase

from .client import Client


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
    def add_statement_successful(cls, mocker, item_id):
        mocker.post(
            cls.wikibase_url(f"/entities/items/{item_id}/statements"),
            json={"id": f"{item_id}$somestuff"},
            status_code=200,
        )


class ClientTests(TestCase):
    def api_client(self):
        return Client("TEST_TOKEN")

    def wikibase_url(self, endpoint):
        return f"{Client.WIKIBASE_URL}{endpoint}"

    @requests_mock.Mocker()
    def test_get_property_data_type(self, mocker):
        ApiMocker.property_data_type(mocker, "P1104", "quantity")
        data_type = self.api_client().get_property_data_type("P1104")
        self.assertEqual(data_type, "quantity")

    @requests_mock.Mocker()
    def test_get_property_data_type_error(self, mocker):
        ApiMocker.property_data_type_not_found(mocker, "P321341234")
        with self.assertRaises(ValueError):
            self.api_client().get_property_data_type("P321341234")
