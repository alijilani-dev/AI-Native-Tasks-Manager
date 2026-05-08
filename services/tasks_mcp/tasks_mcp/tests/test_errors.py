from unittest.mock import Mock

import httpx

from tasks_mcp.errors import handle_api_error


def test_404_error():
    response = Mock(status_code=404)
    error = httpx.HTTPStatusError("Not found", request=Mock(), response=response)
    result = handle_api_error(error)
    assert "not found" in result.lower()


def test_403_error():
    response = Mock(status_code=403)
    error = httpx.HTTPStatusError("Forbidden", request=Mock(), response=response)
    result = handle_api_error(error)
    assert "permission" in result.lower()


def test_429_error():
    response = Mock(status_code=429)
    error = httpx.HTTPStatusError("Rate limit", request=Mock(), response=response)
    result = handle_api_error(error)
    assert "rate limit" in result.lower()


def test_timeout_error():
    error = httpx.TimeoutException("Timed out", request=Mock())
    result = handle_api_error(error)
    assert "timed out" in result.lower()


def test_generic_http_error():
    response = Mock(status_code=500)
    error = httpx.HTTPStatusError("Server error", request=Mock(), response=response)
    result = handle_api_error(error)
    assert "500" in result


def test_unexpected_error():
    result = handle_api_error(ValueError("something broke"))
    assert "unexpected" in result.lower()
