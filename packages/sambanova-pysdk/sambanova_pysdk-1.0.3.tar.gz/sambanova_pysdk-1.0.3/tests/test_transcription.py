import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock, mock_open
from src.sambanova.transcription.transcription import Transcription
import requests

class DummyClient:
    def url(self, path):
        return "http://dummy"
    def headers(self):
        return {}

class TestTranscription(unittest.TestCase):
    def setUp(self):
        self.client = DummyClient()
        self.messages = [{"role": "user", "content": "audio"}]
        self.model = "dummy-model"
        self.audio_file_path = "dummy.mp3"

    @patch("requests.post")
    def test_create_network_failure(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("Network error")
        with self.assertRaises(requests.ConnectionError):
            Transcription.create(self.client, self.messages, self.model)

    @patch("requests.post")
    def test_create_timeout(self, mock_post):
        mock_post.side_effect = requests.Timeout("Timeout error")
        with self.assertRaises(requests.Timeout):
            Transcription.create(self.client, self.messages, self.model)

    @patch("requests.post")
    def test_create_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"data": [1, 2, 3]}
        mock_post.return_value = mock_response
        result = Transcription.create(self.client, self.messages, self.model)
        self.assertEqual(result, {"data": [1, 2, 3]})

    @patch("requests.post")
    def test_create_non_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = "<html>Error</html>"
        mock_post.return_value = mock_response
        result = Transcription.create(self.client, self.messages, self.model)
        self.assertEqual(result, "<html>Error</html>")

    @patch("requests.post")
    def test_create_invalid_json(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "not a json"
        mock_post.return_value = mock_response
        with self.assertRaises(ValueError):
            Transcription.create(self.client, self.messages, self.model)

    @patch("requests.post")
    def test_create_missing_content_type(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.text = "no content type"
        mock_post.return_value = mock_response
        result = Transcription.create(self.client, self.messages, self.model)
        self.assertEqual(result, "no content type")

    @patch("requests.post")
    def test_create_content_type_case_insensitive(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "Application/Json"}
        mock_response.json.return_value = {"data": "ok"}
        mock_post.return_value = mock_response
        result = Transcription.create(self.client, self.messages, self.model)
        self.assertEqual(result, {"data": "ok"})

    @patch("requests.post")
    def test_create_content_type_with_charset(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json; charset=utf-8"}
        mock_response.json.return_value = {"data": "ok"}
        mock_post.return_value = mock_response
        result = Transcription.create(self.client, self.messages, self.model)
        self.assertEqual(result, {"data": "ok"})

    @patch("requests.post")
    def test_create_content_type_none(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = None
        mock_response.text = "no headers"
        mock_post.return_value = mock_response
        result = Transcription.create(self.client, self.messages, self.model)
        self.assertEqual(result, "no headers")

    @patch("requests.post")
    def test_create_empty_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response
        result = Transcription.create(self.client, self.messages, self.model)
        self.assertEqual(result, {})

    @patch("requests.post")
    def test_create_partial_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"partial": True}
        mock_post.return_value = mock_response
        result = Transcription.create(self.client, self.messages, self.model)
        self.assertEqual(result, {"partial": True})

    @patch("requests.post")
    def test_create_streaming_like_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/event-stream"}
        mock_response.text = "data: {\"choices\": [{\"delta\": {\"content\": \"hello\"}}]}\ndata: [DONE]"
        mock_post.return_value = mock_response
        result = Transcription.create(self.client, self.messages, self.model)
        self.assertTrue(isinstance(result, str))
        self.assertTrue(result.startswith("data:") or result == mock_response.text)

    @patch("requests.post")
    def test_transcribe_audio_file_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"text": "hello world"}
        mock_post.return_value = mock_response
        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = Transcription.transcribe_audio_file(self.client, self.model, self.audio_file_path)
            self.assertEqual(result, {"text": "hello world"})

    @patch("requests.post")
    def test_transcribe_audio_file_non_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = "plain text response"
        mock_post.return_value = mock_response
        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = Transcription.transcribe_audio_file(self.client, self.model, self.audio_file_path)
            self.assertEqual(result, "plain text response")

    @patch("requests.post")
    def test_transcribe_audio_file_invalid_json(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "not a json"
        mock_post.return_value = mock_response
        with patch("builtins.open", mock_open(read_data=b"audio")):
            with self.assertRaises(ValueError):
                Transcription.transcribe_audio_file(self.client, self.model, self.audio_file_path)

    @patch("requests.post")
    def test_transcribe_audio_file_missing_content_type(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.text = "no content type"
        mock_post.return_value = mock_response
        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = Transcription.transcribe_audio_file(self.client, self.model, self.audio_file_path)
            self.assertEqual(result, "no content type")

    @patch("requests.post")
    def test_transcribe_audio_file_content_type_none(self, mock_post):
        mock_response = MagicMock()
        mock_response.headers = None
        mock_response.text = "no headers"
        mock_post.return_value = mock_response
        with patch("builtins.open", mock_open(read_data=b"audio")):
            result = Transcription.transcribe_audio_file(self.client, self.model, self.audio_file_path)
            self.assertEqual(result, "no headers")

if __name__ == '__main__':
    unittest.main()
