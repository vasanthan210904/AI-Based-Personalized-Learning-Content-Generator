"""Consistent JSON response envelopes."""
from __future__ import annotations

from flask import jsonify


def api_success(data=None, *, message: str | None = None, status: int = 200):
    payload = {"success": True, "data": data}
    if message:
        payload["message"] = message
    return jsonify(payload), status


def api_error(
    message: str,
    *,
    status: int = 400,
    code: str = "bad_request",
    fields: dict | None = None,
):
    payload = {
        "success": False,
        "error": {"code": code, "message": message},
    }
    if fields:
        payload["error"]["fields"] = fields
    return jsonify(payload), status


def form_errors(form) -> dict:
    return {
        field: (messages[0] if messages else "Invalid value")
        for field, messages in form.errors.items()
    }
