"""Small, shared validation helpers."""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any


class ValidationError(Exception):
    """A user-correctable input error, surfaced as HTTP 422."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field


def clean_text(value: Any, max_length: int | None = None) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").strip()
    text = re.sub(r"[ \t]+", " ", text)
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip()
    return text


def clean_multiline(value: Any, max_length: int | None = None) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip()
    return text


def require_text(value: Any, field: str, label: str, max_length: int = 500) -> str:
    text = clean_text(value, max_length)
    if not text:
        raise ValidationError(f"{label} is required.", field)
    return text


def parse_int(
    value: Any,
    field: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
    label: str | None = None,
) -> int:
    label = label or field.replace("_", " ").title()
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{label} must be a whole number.", field) from None
    if minimum is not None and number < minimum:
        raise ValidationError(f"{label} must be at least {minimum}.", field)
    if maximum is not None and number > maximum:
        raise ValidationError(f"{label} must be at most {maximum}.", field)
    return number


def parse_float(
    value: Any,
    field: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    label: str | None = None,
) -> float:
    label = label or field.replace("_", " ").title()
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{label} must be a number.", field) from None
    if minimum is not None and number < minimum:
        raise ValidationError(f"{label} must be at least {minimum}.", field)
    if maximum is not None and number > maximum:
        raise ValidationError(f"{label} must be at most {maximum}.", field)
    return round(number, 2)


def parse_date(value: Any, field: str, label: str = "Date") -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValidationError(f"{label} must use YYYY-MM-DD format.", field) from None


def choice(value: Any, options: list[str], field: str, label: str) -> str:
    cleaned = clean_text(value, 80)
    if cleaned not in options:
        raise ValidationError(f"Choose a valid {label.lower()}.", field)
    return cleaned


def password_problem(password: str) -> str | None:
    if len(password or "") < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"[A-Za-z]", password):
        return "Password must include at least one letter."
    if not re.search(r"\d", password):
        return "Password must include at least one number."
    return None


def slugify(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "document"


def ensure_list_of_strings(value: Any, limit: int = 20, item_limit: int = 400) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, dict):
            item = item.get("text") or item.get("value") or ""
        text = clean_text(item, item_limit)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result
