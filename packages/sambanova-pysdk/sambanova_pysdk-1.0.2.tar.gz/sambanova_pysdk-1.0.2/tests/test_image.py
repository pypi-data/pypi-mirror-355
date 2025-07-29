import pytest
from unittest.mock import patch, MagicMock
from sambanova.image.image import Image
from sambanova.api_client import SambanovaAPIClient

@pytest.fixture
def client():
    return SambanovaAPIClient("fake-api-key")

@patch("sambanova.image.image.requests.post")
def test_image_create_json_response(mock_post, client):
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"choices": [{"message": {"content": "A test response"}}]}
    mock_post.return_value = mock_response

    messages = [{"role": "user", "content": "Test"}]
    result = Image.create(client, messages, "test-model", max_tokens=123, temperature=0.5, stream=False)
    assert "choices" in result
    assert result["choices"][0]["message"]["content"] == "A test response"

    # Check payload
    _, kwargs = mock_post.call_args
    payload = kwargs["json"]
    assert payload["max_tokens"] == 123
    assert payload["temperature"] == 0.5
    assert payload["stream"] is False

@patch("sambanova.image.image.requests.post")
def test_image_create_non_json_response(mock_post, client, capsys):
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.text = "<html>Not JSON</html>"
    mock_post.return_value = mock_response

    messages = [{"role": "user", "content": "Test"}]
    result = Image.create(client, messages, "test-model")
    assert result == "<html>Not JSON</html>"
    captured = capsys.readouterr()
    assert "Warning: Response is not JSON" in captured.out

@patch("sambanova.image.image.requests.post")
def test_image_create_custom_args(mock_post, client):
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"choices": []}
    mock_post.return_value = mock_response

    messages = [{"role": "user", "content": "Test"}]
    Image.create(
        client,
        messages,
        "test-model",
        max_tokens=222,
        temperature=0.9,
        stream=True
    )
    _, kwargs = mock_post.call_args
    payload = kwargs["json"]
    assert payload["max_tokens"] == 222
    assert payload["temperature"] == 0.9
    assert payload["stream"] is True

@patch("sambanova.image.image.requests.post")
def test_image_create_empty_messages(mock_post, client):
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"choices": []}
    mock_post.return_value = mock_response

    result = Image.create(client, [], "test-model")
    assert "choices" in result

@patch("sambanova.image.image.requests.post")
def test_image_create_http_error(mock_post, client):
    def raise_http_error(*args, **kwargs):
        raise Exception("HTTP error")
    mock_post.side_effect = Exception("HTTP error")

    with pytest.raises(Exception) as excinfo:
        Image.create(client, [{"role": "user", "content": "Test"}], "test-model")
    assert "HTTP error" in str(excinfo.value)
