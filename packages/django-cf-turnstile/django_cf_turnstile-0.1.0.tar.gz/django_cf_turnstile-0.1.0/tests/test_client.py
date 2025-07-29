import json
import unittest
import urllib.error
import urllib.request
from unittest import mock

from django_cf_turnstile import client


class PostFormClientTest(unittest.TestCase):
    @mock.patch("urllib.request.urlopen")
    @mock.patch("urllib.request.Request")
    def test_post_form_success_string_response(self, mock_request_class, mock_urlopen):
        mock_response_context = mock_urlopen.return_value.__enter__.return_value
        mock_response_context.status = 200
        mock_response_context.read.return_value = b"Success"
        mock_response_context.headers.get_content_charset.return_value = "utf-8"

        # Mock the Request instance to check headers later if needed
        mock_req_instance = mock.Mock()
        mock_req_instance.headers = {}  # Simulate initial state
        mock_request_class.return_value = mock_req_instance

        status, body = client.post_form("https://example.com", {"key": "value"})

        self.assertEqual(status, 200)
        self.assertEqual(body, "Success")
        mock_request_class.assert_called_once_with(
            "https://example.com",
            data=b"key=value",
            headers={},
            method="POST",
        )
        mock_urlopen.assert_called_once_with(mock_req_instance, timeout=10)

    @mock.patch("urllib.request.urlopen")
    def test_post_form_success_json_response(self, mock_urlopen):
        mock_response_context = mock_urlopen.return_value.__enter__.return_value
        mock_response_context.status = 200
        json_data = {"message": "ok"}
        mock_response_context.read.return_value = json.dumps(json_data).encode("utf-8")
        mock_response_context.headers.get_content_charset.return_value = "utf-8"

        status, body = client.post_form(
            "https://example.com", {"key": "value"}, as_json=True
        )

        self.assertEqual(status, 200)
        self.assertEqual(body, json_data)

    @mock.patch("urllib.request.urlopen")
    def test_post_form_invalid_json_when_as_json_true(self, mock_urlopen):
        mock_response_context = mock_urlopen.return_value.__enter__.return_value
        mock_response_context.status = 200
        mock_response_context.read.return_value = b"not valid json"
        mock_response_context.headers.get_content_charset.return_value = "utf-8"

        status, body = client.post_form(
            "https://example.com", {"key": "value"}, as_json=True
        )

        self.assertIsNone(status)
        self.assertIsNone(body)

    @mock.patch("urllib.request.urlopen")
    def test_post_form_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://example.com", 404, "Not Found", {}, None
        )
        status, body = client.post_form("https://example.com", {"key": "value"})

        self.assertEqual(status, 404)
        self.assertIsNone(body)

    @mock.patch("urllib.request.urlopen")
    def test_post_form_url_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        status, body = client.post_form("https://example.com", {"key": "value"})

        self.assertIsNone(status)
        self.assertIsNone(body)

    @mock.patch("urllib.request.urlopen")
    def test_post_form_unexpected_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Something went wrong")
        status, body = client.post_form("https://example.com", {"key": "value"})

        self.assertIsNone(status)
        self.assertIsNone(body)
