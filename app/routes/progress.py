"""Learning progress page and API."""
from __future__ import annotations

from flask import Blueprint, render_template
from flask_login import current_user

from ..decorators import student_required
from ..services.progress_service import progress_data
from ..utils.responses import api_success
from ..utils.serializers import attempt_dict, content_summary, study_plan_summary

progress_bp = Blueprint("progress", __name__)


def _serializable(data: dict) -> dict:
    summary = dict(data["summary"])
    summary["recent_contents"] = [
        content_summary(item) for item in summary.get("recent_contents", [])
    ]
    summary["recent_attempts"] = [
        attempt_dict(item) for item in summary.get("recent_attempts", [])
    ]
    active_plan = summary.get("active_plan")
    summary["active_plan"] = study_plan_summary(active_plan) if active_plan else None
    return {**data, "summary": summary}


@progress_bp.get("/progress")
@student_required
def index():
    data = progress_data(current_user)
    chart_data = {
        "activity": data["activity"],
        "score_trend": data["score_trend"],
        "subject_distribution": data["subject_distribution"],
        "accuracy": data["accuracy"],
        "summary": {
            "coverage": data["summary"]["coverage"],
            "mastery": data["summary"]["mastery"],
            "learning_progress": data["summary"]["learning_progress"],
        },
    }
    return render_template(
        "progress/index.html", progress=data, summary=data["summary"], chart_data=chart_data
    )


@progress_bp.get("/api/progress")
@student_required
def api_progress():
    data = _serializable(progress_data(current_user))
    return api_success(data)
