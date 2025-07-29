import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.sambanova.utils import parse_sse_stream

class DummyResponse:
    def __init__(self, lines):
        self._lines = lines
    def iter_lines(self, decode_unicode=True):
        for line in self._lines:
            yield line

def test_parse_sse_stream_basic():
    lines = [
        "data: {\"foo\": 1}",
        "data: {\"bar\": 2}",
        "notdata: ignore",
        "data: [DONE]"
    ]
    resp = DummyResponse(lines)
    result = list(parse_sse_stream(resp))
    assert result == ['{"foo": 1}', '{"bar": 2}', '[DONE]']

def test_parse_sse_stream_empty():
    resp = DummyResponse([])
    result = list(parse_sse_stream(resp))
    assert result == []

def test_parse_sse_stream_no_data_lines():
    lines = [
        "notdata: ignore",
        "something else"
    ]
    resp = DummyResponse(lines)
    result = list(parse_sse_stream(resp))
    assert result == []

def test_parse_sse_stream_data_with_spaces():
    lines = [
        "data:    {\"foo\": 1}   ",
        "data: [DONE]   "
    ]
    resp = DummyResponse(lines)
    result = list(parse_sse_stream(resp))
    assert result == ['{"foo": 1}', '[DONE]']

def test_parse_sse_stream_data_colon_but_not_prefix():
    lines = [
        "data:{\"foo\": 1}", 
        "data: {\"bar\": 2}"
    ]
    resp = DummyResponse(lines)
    result = list(parse_sse_stream(resp))
    assert result == ['{"bar": 2}']

def test_parse_sse_stream_unicode():
    lines = [
        "data: {\"text\": \"hello\"}"
    ]
    resp = DummyResponse(lines)
    result = list(parse_sse_stream(resp))
    assert result == ['{"text": "hello"}']
