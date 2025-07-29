import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock, mock_open
from src.sambanova.translation.translation import Translation
import requests

class DummyClient:
    def url(self, path):
        return "http://dummy"
    def headers(self):
        return {}

class TestTranslation(unittest.TestCase):
    def setUp(self):
        self.client = DummyClient()
        self.audio_file_path = "dummy.mp3"
        self.model = "dummy-model"

    @patch("requests.post")
    def test_network_failure(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("Network error")
        with self.assertRaises(requests.ConnectionError):
            with patch("builtins.open", mock_open(read_data=b"audio")):
                Translation.create(self.client, self.audio_file_path, self.model)

    @patch("requests.post")
    def test_timeout(self, mock_post):
        mock_post.side_effect = requests.Timeout("Timeout error")
        with self.assertRaises(requests.Timeout):
            with patch("builtins.open", mock_open(read_data=b"audio")):
                Translation.create(self.client, self.audio_file_path, self.model)

    @patch("requests.post")
    def test_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"translated": "hello"}
        mock_post.return_value = mock_response
        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = Translation.create(self.client, self.audio_file_path, self.model)
            self.assertEqual(result, {"translated": "hello"})

    @patch("requests.post")
    def test_non_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = "plain text translation"
        mock_post.return_value = mock_response
        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = Translation.create(self.client, self.audio_file_path, self.model)
            self.assertEqual(result, "plain text translation")

    @patch("requests.post")
    def test_invalid_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "not a json"
        mock_post.return_value = mock_response
        with patch("builtins.open", mock_open(read_data=b"audio")):
            with self.assertRaises(ValueError):
                Translation.create(self.client, self.audio_file_path, self.model)

    @patch("requests.post")
    def test_missing_content_type(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.text = "no content type"
        mock_post.return_value = mock_response
        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = Translation.create(self.client, self.audio_file_path, self.model)
            self.assertEqual(result, "no content type")

    @patch("requests.post")
    def test_content_type_case_insensitive(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "Application/Json"}
        mock_response.json.return_value = {"translated": "ok"}
        mock_post.return_value = mock_response
        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = Translation.create(self.client, self.audio_file_path, self.model)
            self.assertEqual(result, {"translated": "ok"})

    @patch("requests.post")
    def test_content_type_with_charset(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json; charset=utf-8"}
        mock_response.json.return_value = {"translated": "ok"}
        mock_post.return_value = mock_response
        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = Translation.create(self.client, self.audio_file_path, self.model)
            self.assertEqual(result, {"translated": "ok"})

    @patch("requests.post")
    def test_content_type_none(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = None
        mock_response.text = "no headers"
        mock_post.return_value = mock_response
        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = Translation.create(self.client, self.audio_file_path, self.model)
            self.assertEqual(result, "no headers")

    @patch("requests.post")
    def test_empty_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response
        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = Translation.create(self.client, self.audio_file_path, self.model)
            self.assertEqual(result, {})

    @patch("requests.post")
    def test_partial_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"partial": True}
        mock_post.return_value = mock_response
        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = Translation.create(self.client, self.audio_file_path, self.model)
            self.assertEqual(result, {"partial": True})

    @patch("requests.post")
    def test_streaming_like_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/event-stream"}
        mock_response.text = "data: {\"choices\": [{\"delta\": {\"content\": \"hello\"}}]}\ndata: [DONE]"
        mock_post.return_value = mock_response
        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = Translation.create(self.client, self.audio_file_path, self.model)
            self.assertTrue(isinstance(result, str))
            self.assertTrue(result.startswith("data:") or result == mock_response.text)

if __name__ == '__main__':
    unittest.main()
