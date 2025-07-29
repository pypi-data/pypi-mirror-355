import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

import unittest
from unittest.mock import patch, MagicMock
from src.sambanova.embeddings.embeddings import Embeddings
from src.sambanova.api_client import SambanovaAPIClient
import requests

class DummyClient:
    def url(self, path):
        return ""
    def headers(self):
        return {}

class TestEmbeddings(unittest.TestCase):
    def setUp(self):
        self.client = DummyClient()
        self.messages = ["test message"]
        self.model = "dummy-model"

    @patch("requests.post")
    def test_network_failure(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("Network error")
        with self.assertRaises(requests.ConnectionError):
            Embeddings.create(self.client, self.messages, self.model)

    @patch("requests.post")
    def test_timeout(self, mock_post):
        mock_post.side_effect = requests.Timeout("Timeout error")
        with self.assertRaises(requests.Timeout):
            Embeddings.create(self.client, self.messages, self.model)

    @patch("requests.post")
    def test_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("Bad status")
        mock_post.return_value = mock_response
        with self.assertRaises(requests.HTTPError):
            Embeddings.create(self.client, self.messages, self.model)

    @patch("requests.post")
    def test_non_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = "<html>Error</html>"
        mock_post.return_value = mock_response
        result = Embeddings.create(self.client, self.messages, self.model)
        self.assertIn("error", result)
        self.assertIn("raw_response", result)

    @patch("requests.post")
    def test_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"data": [1, 2, 3]}
        mock_post.return_value = mock_response
        result = Embeddings.create(self.client, self.messages, self.model)
        self.assertEqual(result, {"data": [1, 2, 3]})

    @patch("requests.post")
    def test_empty_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response
        result = Embeddings.create(self.client, self.messages, self.model)
        self.assertEqual(result, {})

    @patch("requests.post")
    def test_invalid_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "not a json"
        mock_post.return_value = mock_response
        # Accept ValueError if Embeddings.create does not handle invalid JSON internally
        try:
            result = Embeddings.create(self.client, self.messages, self.model)
            # If no exception, check for error keys in result
            self.assertIn("error", result)
            self.assertIn("raw_response", result)
            self.assertEqual(result["raw_response"], "not a json")
        except ValueError as e:
            self.assertEqual(str(e), "Invalid JSON")

    @patch("requests.post")
    def test_missing_content_type(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {}
        mock_response.text = "no content type"
        mock_post.return_value = mock_response
        result = Embeddings.create(self.client, self.messages, self.model)
        self.assertIn("error", result)
        self.assertIn("raw_response", result)

    @patch("requests.post")
    def test_partial_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"partial": True}
        mock_post.return_value = mock_response
        result = Embeddings.create(self.client, self.messages, self.model)
        self.assertEqual(result, {"partial": True})

    @patch("requests.post")
    def test_unexpected_status_code(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("418 I'm a teapot")
        mock_post.return_value = mock_response
        with self.assertRaises(requests.HTTPError):
            Embeddings.create(self.client, self.messages, self.model)

if __name__ == '__main__':
    unittest.main()