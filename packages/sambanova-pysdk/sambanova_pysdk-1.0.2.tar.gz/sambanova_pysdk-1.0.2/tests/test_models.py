import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import patch, MagicMock
from src.sambanova.model_list import models

class DummyClient:
    def url(self, path):
        return f"https://api.sambanova.ai{path}"
    def headers(self):
        return {"Authorization": "Bearer test"}

@patch("src.sambanova.model_list.models.requests.get")
def test_get_available_models_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": [{"id": "model1"}]}
    mock_get.return_value = mock_resp
    client = DummyClient()
    result = models.get_available_models(client)
    assert result == [{"id": "model1"}]

@patch("src.sambanova.model_list.models.requests.get")
def test_get_available_models_error(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.text = "Not Found"
    mock_get.return_value = mock_resp
    client = DummyClient()
    with pytest.raises(RuntimeError) as excinfo:
        models.get_available_models(client)
    assert "Failed to fetch models" in str(excinfo.value)

@patch("src.sambanova.model_list.models.requests.get")
def test_get_available_models_empty(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": []}
    mock_get.return_value = mock_resp
    client = DummyClient()
    result = models.get_available_models(client)
    assert result == []

@patch("src.sambanova.model_list.models.requests.get")
def test_get_available_models_no_data_key(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"other": 123}
    mock_get.return_value = mock_resp
    client = DummyClient()
    result = models.get_available_models(client)
    assert result == []

@patch("src.sambanova.model_list.models.requests.get")
def test_get_available_models_data_is_none(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": None}
    mock_get.return_value = mock_resp
    client = DummyClient()
    result = models.get_available_models(client)
    assert result == []

@patch("src.sambanova.model_list.models.requests.get")
def test_get_available_models_json_raises(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = ValueError("Invalid JSON")
    mock_get.return_value = mock_resp
    client = DummyClient()
    with pytest.raises(ValueError):
        models.get_available_models(client)

@patch("src.sambanova.model_list.models.requests.get")
def test_get_model_details_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "model1", "name": "Test Model"}
    mock_get.return_value = mock_resp
    client = DummyClient()
    result = models.get_model_details(client, "model1")
    assert result == {"id": "model1", "name": "Test Model"}

@patch("src.sambanova.model_list.models.requests.get")
def test_get_model_details_error(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    mock_get.return_value = mock_resp
    client = DummyClient()
    with pytest.raises(RuntimeError) as excinfo:
        models.get_model_details(client, "model1")
    assert "Failed to fetch model details" in str(excinfo.value)

@patch("src.sambanova.model_list.models.requests.get")
def test_get_model_details_non_json(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = ValueError("No JSON object could be decoded")
    mock_get.return_value = mock_resp
    client = DummyClient()
    with pytest.raises(ValueError):
        models.get_model_details(client, "model1")

@patch("src.sambanova.model_list.models.requests.get")
def test_get_model_details_partial_data(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "model1"}
    mock_get.return_value = mock_resp
    client = DummyClient()
    result = models.get_model_details(client, "model1")
    assert result == {"id": "model1"}

@patch("src.sambanova.model_list.models.requests.get")
def test_get_model_details_empty_dict(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {}
    mock_get.return_value = mock_resp
    client = DummyClient()
    result = models.get_model_details(client, "model1")
    assert result == {}

@patch("src.sambanova.model_list.models.requests.get")
def test_get_model_details_non_200_and_non_json(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.text = "Forbidden"
    mock_resp.json.side_effect = Exception("Should not be called")
    mock_get.return_value = mock_resp
    client = DummyClient()
    with pytest.raises(RuntimeError) as excinfo:
        models.get_model_details(client, "model1")
    assert "Failed to fetch model details" in str(excinfo.value)
