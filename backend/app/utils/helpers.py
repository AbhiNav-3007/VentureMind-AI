"""
VentureMind AI — Utility helpers
"""

from __future__ import annotations
import re
import json
from typing import Any


def sanitize_json_response(raw: str) -> str:
    """
    Strip markdown fences and extract the first valid JSON block from a
    Granite response. Returns the cleaned JSON string or the original.
    """
    text = raw.strip()

    # Remove ```json ... ``` or ``` ... ``` fences
    if "```" in text:
        parts = text.split("```")
        for part in parts[1:]:
            candidate = part.lstrip("json").lstrip("JSON").strip()
            if candidate.startswith("{") or candidate.startswith("["):
                text = candidate
                break

    # Try to find first { or [ and extract from there
    match = re.search(r"[\[{]", text)
    if match:
        text = text[match.start():]

    return text


def repair_truncated_json(text: str) -> str:
    """
    Attempt to repair a JSON string that was cut off mid-generation
    (e.g. due to max_new_tokens limit).

    Strategy:
    1. Remove the last incomplete key-value pair (anything after the last
       complete value ending with }, ], " or a number).
    2. Close all open arrays and objects in reverse order.
    """
    # Strip trailing whitespace and commas
    text = text.rstrip().rstrip(",").rstrip()

    # Track open containers using a simple stack scan
    stack = []
    in_string = False
    escape_next = False

    for ch in text:
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            stack.append("}")
        elif ch == "[":
            stack.append("]")
        elif ch in "}]":
            if stack and stack[-1] == ch:
                stack.pop()

    # Close any open string first if we are still inside one
    prefix = ""
    if in_string:
        prefix = '"'
    # Close any open containers in reverse order
    closing = "".join(reversed(stack))
    return text + prefix + closing


def safe_parse_json(raw: str, default: Any = None) -> Any:
    """
    Attempt to parse JSON from a Granite response.

    Steps:
    1. Sanitize (strip fences, find first { or [)
    2. Try direct parse
    3. If that fails, repair truncated JSON and try again
    4. Return default if all attempts fail
    """
    if not raw or not raw.strip():
        return default

    cleaned = sanitize_json_response(raw)

    # Attempt 1: direct parse
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass

    # Attempt 2: repair truncated JSON then parse
    try:
        repaired = repair_truncated_json(cleaned)
        return json.loads(repaired)
    except (json.JSONDecodeError, ValueError):
        pass

    return default


def truncate_text(text: str, max_chars: int = 200) -> str:
    """Truncate text to max_chars with ellipsis."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"
