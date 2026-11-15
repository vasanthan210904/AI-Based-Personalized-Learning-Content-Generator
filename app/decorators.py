"""Role-based access decorators."""
from __future__ import annotations

from functools import wraps

from flask import abort
from flask_login import current_user

from .extensions import login_manager


def role_required(role: str):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role != role:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


student_required = role_required("student")
admin_required = role_required("admin")
