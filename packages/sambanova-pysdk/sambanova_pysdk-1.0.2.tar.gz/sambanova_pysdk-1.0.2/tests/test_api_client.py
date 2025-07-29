import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.sambanova.api_client import SambanovaAPIClient

def test_headers_default():
    client = SambanovaAPIClient("test-key")
    headers = client.headers()
    assert headers["Accept"] == "application/json"
    assert headers["Content-Type"] == "application/json"
    assert headers["Authorization"] == "Bearer test-key"

def test_headers_custom_content_type():
    client = SambanovaAPIClient("test-key", contentType="application/text")
    headers = client.headers()
    assert headers["Content-Type"] == "application/text"

def test_headers_bearer_auth_flag():
    client = SambanovaAPIClient("test-key", use_bearer_auth=True)
    headers = client.headers()
    assert headers["Authorization"] == "Bearer test-key"

def test_url_trailing_and_leading_slash():
    client = SambanovaAPIClient("test-key")
    # path with leading slash
    assert client.url("/foo/bar") == "https://api.sambanova.ai/foo/bar"
    # path without leading slash
    assert client.url("foo/bar") == "https://api.sambanova.ai/foo/bar"
    # base_url with trailing slash
    client.base_url = "https://api.sambanova.ai/"
    assert client.url("/foo") == "https://api.sambanova.ai/foo"
    # base_url without trailing slash
    client.base_url = "https://api.sambanova.ai"
    assert client.url("/foo") == "https://api.sambanova.ai/foo"

def test_headers_missing_api_key():
    # Should still set Authorization even if api_key is empty
    client = SambanovaAPIClient("")
    headers = client.headers()
    assert headers["Authorization"] == "Bearer "

def test_url_empty_path():
    client = SambanovaAPIClient("test-key")
    assert client.url("") == "https://api.sambanova.ai/"

def test_url_root_path():
    client = SambanovaAPIClient("test-key")
    assert client.url("/") == "https://api.sambanova.ai/"

def test_api_key_is_set():
    client = SambanovaAPIClient("my-key")
    assert client.api_key == "my-key"

def test_api_key_is_empty_string():
    client = SambanovaAPIClient("")
    assert client.api_key == ""

def test_api_key_is_none():
    client = SambanovaAPIClient(None)
    # Should set api_key to None, but headers will include 'Bearer None'
    headers = client.headers()
    assert headers["Authorization"] == "Bearer None"

def test_url_with_spaces_and_special_chars():
    client = SambanovaAPIClient("test-key")
    path = "/foo bar/!@#"
    expected = "https://api.sambanova.ai/foo bar/!@#"
    assert client.url(path) == expected

def test_url_with_multiple_slashes():
    client = SambanovaAPIClient("test-key")
    assert client.url("///foo///bar") == "https://api.sambanova.ai/foo///bar"

def test_headers_content_type_override():
    client = SambanovaAPIClient("test-key", contentType="application/xml")
    headers = client.headers()
    assert headers["Content-Type"] == "application/xml"

def test_headers_accept_header():
    client = SambanovaAPIClient("test-key")
    headers = client.headers()
    assert "Accept" in headers
    assert headers["Accept"] == "application/json"

def test_url_with_full_url_path():
    client = SambanovaAPIClient("test-key")
    full_url = "https://otherhost.com/api"
    assert client.url(full_url) == "https://api.sambanova.ai/https://otherhost.com/api"
