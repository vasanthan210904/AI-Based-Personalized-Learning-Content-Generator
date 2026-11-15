"""Access-control and redirect helpers."""
from __future__ import annotations

from urllib.parse import urljoin, urlparse

from flask import abort, request
from flask_login import current_user

from ..extensions import db


def get_owned_or_404(model, object_id: int, owner_attr: str = "user_id"):
    """Fetch a record by id and enforce that the signed-in user owns it."""
    obj = db.session.get(model, object_id)
    if obj is None or getattr(obj, owner_attr, None) != current_user.id:
        abort(404)
    return obj


def is_safe_redirect(target: str | None) -> bool:
    if not target:
        return False
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return redirect_url.scheme in ("http", "https") and host_url.netloc == redirect_url.netloc
