import requests_mock

from django.test import TestCase

from .client import Client


class ClientTests(TestCase):
    def api_client(self):
        return Client("TEST_TOKEN")

    def wikibase_url(self, endpoint):
        return f"{Client.WIKIBASE_URL}{endpoint}"

    @requests_mock.Mocker()
    def test_get_property_data_type(self, mocker):
        mocker.get(
            self.wikibase_url("/entities/properties/P1104"),
            json={"data_type": "quantity"},
            status_code=200,
        )
        data_type = self.api_client().get_property_data_type("P1104")
        self.assertEqual(data_type, "quantity")

    @requests_mock.Mocker()
    def test_get_property_data_type_error(self, mocker):
        mocker.get(
            self.wikibase_url("/entities/properties/P321341234"),
            json={"code": "property-not-found"},
            status_code=404,
        )
        with self.assertRaises(ValueError):
            self.api_client().get_property_data_type("P321341234")
