"""
VentureMind AI — Unit tests for utility helpers
"""
from app.utils.helpers import sanitize_json_response, safe_parse_json, truncate_text


def test_sanitize_strips_markdown_fence():
    raw = "```json\n{\"key\": \"value\"}\n```"
    result = sanitize_json_response(raw)
    assert result.startswith("{")


def test_safe_parse_json_valid():
    result = safe_parse_json('{"domain": "Technology"}')
    assert result["domain"] == "Technology"


def test_safe_parse_json_invalid_returns_default():
    result = safe_parse_json("not valid json", default={})
    assert result == {}


def test_truncate_text():
    text = "A" * 300
    result = truncate_text(text, max_chars=100)
    assert len(result) <= 104  # ellipsis adds 1 char
