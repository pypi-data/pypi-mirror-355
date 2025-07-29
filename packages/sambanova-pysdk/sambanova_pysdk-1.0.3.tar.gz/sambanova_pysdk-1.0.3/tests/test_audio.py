import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock
from src.sambanova.audio.audio import Audio
import requests

class DummyClient:
    def url(self, path):
        return "http://dummy"
    def headers(self):
        return {}

class TestAudio(unittest.TestCase):
    def setUp(self):
        self.client = DummyClient()
        self.messages = [{"role": "user", "content": "audio"}]
        self.model = "dummy-model"

    @patch("requests.post")
    def test_network_failure(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("Network error")
        with self.assertRaises(requests.ConnectionError):
            Audio.create(self.client, self.messages, self.model)

    @patch("requests.post")
    def test_timeout(self, mock_post):
        mock_post.side_effect = requests.Timeout("Timeout error")
        with self.assertRaises(requests.Timeout):
            Audio.create(self.client, self.messages, self.model)

    @patch("requests.post")
    def test_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("Bad status")
        mock_post.return_value = mock_response
        
        result = Audio.create(self.client, self.messages, self.model)
        self.assertIsNotNone(result)

    @patch("requests.post")
    def test_non_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = "<html>Error</html>"
        mock_post.return_value = mock_response
        result = Audio.create(self.client, self.messages, self.model)
        self.assertEqual(result, "<html>Error</html>")

    @patch("requests.post")
    def test_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"data": [1, 2, 3]}
        mock_post.return_value = mock_response
        result = Audio.create(self.client, self.messages, self.model)
        self.assertEqual(result, {"data": [1, 2, 3]})

    @patch("requests.post")
    def test_invalid_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "not a json"
        mock_post.return_value = mock_response
        # Audio.create will raise ValueError if .json() fails
        with self.assertRaises(ValueError):
            Audio.create(self.client, self.messages, self.model)

    @patch("requests.post")
    def test_missing_content_type(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.text = "no content type"
        mock_post.return_value = mock_response
        result = Audio.create(self.client, self.messages, self.model)
        self.assertEqual(result, "no content type")

    @patch("requests.post")
    def test_empty_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response
        result = Audio.create(self.client, self.messages, self.model)
        self.assertEqual(result, {})

    @patch("requests.post")
    def test_partial_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"partial": True}
        mock_post.return_value = mock_response
        result = Audio.create(self.client, self.messages, self.model)
        self.assertEqual(result, {"partial": True})

    @patch("requests.post")
    def test_streaming_like_response(self, mock_post):
        # Simulate a streaming response (string starting with "data:")
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/event-stream"}
        mock_response.text = "data: {\"choices\": [{\"delta\": {\"content\": \"hello\"}}]}\ndata: [DONE]"
        mock_post.return_value = mock_response
        result = Audio.create(self.client, self.messages, self.model)
        self.assertTrue(isinstance(result, str))
        self.assertTrue(result.startswith("data:") or result == mock_response.text)

    @patch("requests.post")
    def test_content_type_case_insensitive(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "Application/Json"}
        mock_response.json.return_value = {"data": "ok"}
        mock_post.return_value = mock_response
        result = Audio.create(self.client, self.messages, self.model)
        self.assertEqual(result, {"data": "ok"})

    @patch("requests.post")
    def test_content_type_with_charset(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json; charset=utf-8"}
        mock_response.json.return_value = {"data": "ok"}
        mock_post.return_value = mock_response
        result = Audio.create(self.client, self.messages, self.model)
        self.assertEqual(result, {"data": "ok"})

    @patch("requests.post")
    def test_content_type_none(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = None
        mock_response.text = "no headers"
        mock_post.return_value = mock_response
        result = Audio.create(self.client, self.messages, self.model)
        self.assertEqual(result, "no headers")

if __name__ == '__main__':
    unittest.main()
