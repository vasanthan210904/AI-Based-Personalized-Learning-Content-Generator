"""Public landing page."""
from __future__ import annotations

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user

from ..constants import LEARNING_LEVELS
from ..models import Subject, Topic

public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def landing():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("student.dashboard"))
    counts = {
        "subjects": Subject.query.count(),
        "topics": Topic.query.count(),
        "levels": len(LEARNING_LEVELS),
    }
    return render_template("index.html", counts=counts)
