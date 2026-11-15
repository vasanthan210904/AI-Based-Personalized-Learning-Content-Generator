"""Helpers for reading structured JSON out of AI responses."""
from __future__ import annotations

import json
import re


class JsonParseError(ValueError):
    pass


def extract_json(raw: str) -> dict:
    """Extract a JSON object from a model response.

    Handles raw JSON, fenced code blocks and models that wrap JSON in prose.
    """
    if not raw or not str(raw).strip():
        raise JsonParseError("The AI returned an empty response.")

    text = str(raw).strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
        raise JsonParseError("The AI response was not a JSON object.")
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise JsonParseError("No JSON object found in the AI response.")

    candidate = text[start : end + 1]
    try:
        parsed = json.loads(candidate, strict=False)
    except json.JSONDecodeError as exc:
        raise JsonParseError(f"The AI response contained invalid JSON: {exc.msg}.") from None
    if not isinstance(parsed, dict):
        raise JsonParseError("The AI response was not a JSON object.")
    return parsed
