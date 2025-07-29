import unittest
from unittest.mock import patch, Mock

from pyproxy_sdk.client import PyProxyClient
from pyproxy_sdk.exceptions import (
    PyProxyConfigurationError,
    PyProxyAlreadyExists,
    PyProxyNotFound,
    PyProxyInvalidInput,
    PyProxyServerError,
)


class TestPyProxyClient(unittest.TestCase):

    def setUp(self):
        self.client = PyProxyClient(
            base_url="http://localhost:5000",
            username="admin",
            password="password",
        )

    def test_missing_base_url(self):
        with self.assertRaises(PyProxyConfigurationError):
            PyProxyClient(
                base_url=None,
                username="admin",
                password="password",
            )

    def test_missing_username(self):
        with self.assertRaises(PyProxyConfigurationError):
            PyProxyClient(
                base_url="http://localhost:5000",
                username=None,
                password="password",
            )

    def test_missing_password(self):
        with self.assertRaises(PyProxyConfigurationError):
            PyProxyClient(
                base_url="http://localhost:5000",
                username="admin",
                password=None,
            )

    @patch("pyproxy_sdk.client.requests.get")
    def test_get_status_success(self, mock_get):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_response

        result = self.client.get_status()
        self.assertEqual(result, {"status": "ok"})

    @patch("pyproxy_sdk.client.requests.get")
    def test_server_error(self, mock_get):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Server Error"}
        mock_get.return_value = mock_response

        with self.assertRaises(PyProxyServerError):
            self.client.get_status()

    @patch("pyproxy_sdk.client.requests.post")
    def test_add_filtering_already_exists(self, mock_post):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 409
        mock_response.json.return_value = {"message": "Already blocked"}
        mock_post.return_value = mock_response

        with self.assertRaises(PyProxyAlreadyExists):
            self.client.add_filtering("domain", "example.com")

    @patch("pyproxy_sdk.client.requests.delete")
    def test_delete_filtering_not_found(self, mock_delete):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "not found"}
        mock_delete.return_value = mock_response

        with self.assertRaises(PyProxyNotFound):
            self.client.delete_filtering("domain", "example.com")

    @patch("pyproxy_sdk.client.requests.post")
    def test_invalid_input(self, mock_post):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "invalid input"}
        mock_post.return_value = mock_response

        with self.assertRaises(PyProxyInvalidInput):
            self.client.add_filtering("domain", "")


if __name__ == "__main__":
    unittest.main()
