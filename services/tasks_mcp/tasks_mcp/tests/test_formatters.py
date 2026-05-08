import json

from tasks_mcp.formatters import enforce_char_limit, format_json, format_markdown


def test_format_json_has_required_fields():
    items = [{"id": "1", "title": "Test"}]
    result = json.loads(format_json(items, total=1, offset=0, limit=20))
    assert result["total"] == 1
    assert result["count"] == 1
    assert result["offset"] == 0
    assert result["has_more"] is False
    assert result["next_offset"] is None
    assert len(result["items"]) == 1


def test_format_json_has_more():
    items = [{"id": str(i)} for i in range(20)]
    result = json.loads(format_json(items, total=50, offset=0, limit=20))
    assert result["has_more"] is True
    assert result["next_offset"] == 20


def test_format_markdown_has_header():
    items = [{"id": "1", "title": "Buy milk"}]
    result = format_markdown(items, total=1, offset=0, limit=20)
    assert result.startswith("#")
    assert "Buy milk" in result


def test_format_markdown_empty_list():
    result = format_markdown([], total=0, offset=0, limit=20)
    assert "0 items" in result


def test_truncation_at_limit():
    long_text = "x" * 30000
    result, truncated = enforce_char_limit(long_text, limit=100)
    assert truncated is True
    assert len(result) <= 100 + 200  # text + truncation message


def test_no_truncation_under_limit():
    short_text = "hello world"
    result, truncated = enforce_char_limit(short_text, limit=25000)
    assert truncated is False
    assert result == short_text
