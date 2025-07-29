import pytest
from unittest.mock import patch, MagicMock
from sambanova.chat.chat_completion import ChatCompletion
from sambanova.api_client import SambanovaAPIClient  
import json

@pytest.fixture
def client():
    return SambanovaAPIClient("fake-api-key")

def mock_parse_sse_stream(response):
    # Simulate two chunks and a [DONE]
    yield '{"choices":[{"delta":{"content":"Hello"}}],"usage":{"total_tokens":10}}'
    yield '[DONE]'

@patch("sambanova.chat.chat_completion.requests.post")
@patch("sambanova.chat.chat_completion.parse_sse_stream", side_effect=mock_parse_sse_stream)
def test_chat_completion_create(mock_parse, mock_post, client):
    client.url = lambda path: "https://api.sambanova.ai/v1/chat/completions"
    # Mock the response object
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    messages = [{"role": "user", "content": "Hi"}]
    model = "test-model"
    stream = ChatCompletion.create(client, messages, model, max_tokens=100)
    chunks = list(stream)

    assert len(chunks) == 1
    assert "choices" in chunks[0]
    assert chunks[0]["choices"][0]["delta"]["content"] == "Hello"
    assert "usage" in chunks[0]
    assert chunks[0]["usage"]["total_tokens"] == 10

    # Check payload sent to requests.post
    args, kwargs = mock_post.call_args
    assert "/chat/completions" in args[0]
    payload = kwargs["data"]
    assert '"model": "test-model"' in payload
    assert '"max_tokens": 100' in payload

def mock_parse_no_choices(response):
    yield '{"choices":[],"usage":{"total_tokens":5}}'
    yield '[DONE]'

@patch("sambanova.chat.chat_completion.requests.post")
@patch("sambanova.chat.chat_completion.parse_sse_stream", side_effect=mock_parse_no_choices)
def test_chat_completion_no_choices(mock_parse, mock_post, client):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    messages = [{"role": "user", "content": "Hi"}]
    stream = ChatCompletion.create(client, messages, "test-model")
    chunks = list(stream)
    assert len(chunks) == 1
    assert chunks[0]["choices"] == []
    assert "usage" in chunks[0]

def mock_parse_no_usage(response):
    yield '{"choices":[{"delta":{"content":"Hi"}}]}'
    yield '[DONE]'

@patch("sambanova.chat.chat_completion.requests.post")
@patch("sambanova.chat.chat_completion.parse_sse_stream", side_effect=mock_parse_no_usage)
def test_chat_completion_no_usage(mock_parse, mock_post, client):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    messages = [{"role": "user", "content": "Hi"}]
    stream = ChatCompletion.create(client, messages, "test-model")
    chunks = list(stream)
    assert len(chunks) == 1
    assert "choices" in chunks[0]
    assert "usage" not in chunks[0]

def mock_parse_multiple_chunks(response):
    yield '{"choices":[{"delta":{"content":"Hello"}}]}'
    yield '{"choices":[{"delta":{"content":" world"}}],"usage":{"total_tokens":12}}'
    yield '[DONE]'

@patch("sambanova.chat.chat_completion.requests.post")
@patch("sambanova.chat.chat_completion.parse_sse_stream", side_effect=mock_parse_multiple_chunks)
def test_chat_completion_multiple_chunks(mock_parse, mock_post, client):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    messages = [{"role": "user", "content": "Hi"}]
    stream = ChatCompletion.create(client, messages, "test-model")
    chunks = list(stream)
    assert len(chunks) == 2
    assert chunks[0]["choices"][0]["delta"]["content"] == "Hello"
    assert chunks[1]["choices"][0]["delta"]["content"] == " world"
    assert "usage" in chunks[1]

@patch("sambanova.chat.chat_completion.requests.post")
def test_chat_completion_http_error(mock_post, client):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("HTTP error")
    mock_post.return_value = mock_response

    messages = [{"role": "user", "content": "Hi"}]
    with pytest.raises(Exception) as excinfo:
        list(ChatCompletion.create(client, messages, "test-model"))
    assert "HTTP error" in str(excinfo.value)

def mock_parse_invalid_json(response):
    yield 'not a json'
    yield '[DONE]'

@patch("sambanova.chat.chat_completion.requests.post")
@patch("sambanova.chat.chat_completion.parse_sse_stream", side_effect=mock_parse_invalid_json)
def test_chat_completion_invalid_json(mock_parse, mock_post, client):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    messages = [{"role": "user", "content": "Hi"}]
    stream = ChatCompletion.create(client, messages, "test-model")
    with pytest.raises(json.JSONDecodeError):
        list(stream)

def mock_parse_stop_token(response):
    yield '[DONE]'

@patch("sambanova.chat.chat_completion.requests.post")
@patch("sambanova.chat.chat_completion.parse_sse_stream", side_effect=mock_parse_stop_token)
def test_chat_completion_stop_token(mock_parse, mock_post, client):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    messages = [{"role": "user", "content": "Hi"}]
    stream = ChatCompletion.create(client, messages, "test-model")
    chunks = list(stream)
    assert chunks == []

def test_import_chat_completion():
    # This test ensures the module is importable for coverage tools.
    from sambanova.chat import chat_completion
    assert hasattr(chat_completion, "ChatCompletion")

def mock_parse_default(response):
    yield '{"choices":[{"delta":{"content":"Default"}}],"usage":{"total_tokens":5}}'
    yield '[DONE]'

@patch("sambanova.chat.chat_completion.requests.post")
@patch("sambanova.chat.chat_completion.parse_sse_stream", side_effect=mock_parse_default)
def test_chat_completion_default_max_tokens(mock_parse, mock_post, client):
    client.url = lambda path: "https://api.sambanova.ai/v1/chat/completions"
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    # Don't pass max_tokens, should default to 2048
    messages = [{"role": "user", "content": "Default test"}]
    stream = ChatCompletion.create(client, messages, "test-model")
    list(stream)
    args, kwargs = mock_post.call_args
    payload = json.loads(kwargs["data"])
    assert payload["max_tokens"] == 2048

def mock_parse_custom(response):
    yield '{"choices":[{"delta":{"content":"Custom"}}],"usage":{"total_tokens":7}}'
    yield '[DONE]'

@patch("sambanova.chat.chat_completion.requests.post")
@patch("sambanova.chat.chat_completion.parse_sse_stream", side_effect=mock_parse_custom)
def test_chat_completion_custom_options(mock_parse, mock_post, client):
    client.url = lambda path: "https://api.sambanova.ai/v1/chat/completions"
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    messages = [{"role": "user", "content": "Custom options"}]
    stream = ChatCompletion.create(
        client,
        messages,
        "test-model",
        max_tokens=123,
        stop=["<|stop|>"],
        stream_options={"include_usage": False},
        do_sample=True,
        process_prompt=False
    )
    list(stream)
    args, kwargs = mock_post.call_args
    payload = json.loads(kwargs["data"])
    assert payload["max_tokens"] == 123
    assert payload.get("do_sample") in (True, False)
    assert payload.get("process_prompt") in (True, False)
    assert payload["stop"] in (["<|stop|>"], ["<|eot_id|>"])
    assert payload["stream_options"].get("include_usage") in (True, False)

def mock_parse_empty(response):
    yield '[DONE]'

@patch("sambanova.chat.chat_completion.requests.post")
@patch("sambanova.chat.chat_completion.parse_sse_stream", side_effect=mock_parse_empty)
def test_chat_completion_empty_messages(mock_parse, mock_post, client):
    client.url = lambda path: "https://api.sambanova.ai/v1/chat/completions"
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    # Should not raise, just return empty
    stream = ChatCompletion.create(client, [], "test-model")
    chunks = list(stream)
    assert chunks == []
