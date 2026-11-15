"""A small in-process rate limiter for expensive endpoints.

This is intentionally dependency-free and suitable for a single-process Flask
deployment (the development server / a single gunicorn worker). For a
multi-process production deployment use Redis-backed Flask-Limiter instead.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from functools import wraps

from flask import current_app, request
from flask_login import current_user


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int, message: str):
        super().__init__(message)
        self.retry_after = max(1, retry_after)
        self.message = message


_buckets: dict[str, deque[float]] = {}
_lock = threading.Lock()


def reset_rate_limits() -> None:
    with _lock:
        _buckets.clear()


def rate_limit(
    name: str,
    *,
    limit_key: str = "RATE_LIMIT_AI",
    window_key: str = "RATE_LIMIT_AI_WINDOW",
    methods: tuple[str, ...] = ("POST",),
    message: str = "Too many requests. Please wait a moment and try again.",
):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_app.config.get("RATE_LIMIT_ENABLED", True):
                return view(*args, **kwargs)
            if request.method not in methods:
                return view(*args, **kwargs)

            limit = current_app.config.get(limit_key, 8)
            window = current_app.config.get(window_key, 600)
            identity = f"u{current_user.id}" if current_user.is_authenticated else f"ip{request.remote_addr}"
            bucket_key = f"{name}:{identity}"
            now = time.monotonic()

            with _lock:
                bucket = _buckets.setdefault(bucket_key, deque())
                cutoff = now - window
                while bucket and bucket[0] < cutoff:
                    bucket.popleft()
                if len(bucket) >= limit:
                    retry_after = int(window - (now - bucket[0])) + 1
                    raise RateLimitExceeded(retry_after, message)
                bucket.append(now)

            return view(*args, **kwargs)

        return wrapped

    return decorator
