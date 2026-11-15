"""Personalized study planner pages and API."""
from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO

from flask import Blueprint, render_template, request, send_file, url_for
from flask_login import current_user
from sqlalchemy import desc

from ..constants import STUDY_PLAN_MAX_DAYS
from ..decorators import student_required
from ..models import StudyPlan
from ..services.export_service import build_plan_ics
from ..services.study_plan_generator import generate_study_plan, toggle_day
from ..utils.catalog import subjects_with_topics
from ..utils.rate_limit import rate_limit
from ..utils.responses import api_success
from ..utils.security import get_owned_or_404
from ..utils.serializers import study_plan_detail, study_plan_summary
from ..utils.validation import ValidationError, parse_int, slugify

study_bp = Blueprint("study", __name__)


@study_bp.get("/study-planner")
@student_required
def planner():
    profile = current_user.profile
    plans = (
        StudyPlan.query.filter_by(user_id=current_user.id)
        .order_by(desc(StudyPlan.created_at))
        .all()
    )
    today = date.today()
    return render_template(
        "study_plan/planner.html",
        subjects_data=subjects_with_topics(),
        plans=plans,
        defaults={
            "learning_level": profile.learning_level if profile else "Beginner",
            "hours_per_day": 2,
            "subject_id": request.args.get("subject", type=int),
            "target_date": (today + timedelta(days=13)).isoformat(),
            "min_date": today.isoformat(),
            "max_date": (today + timedelta(days=STUDY_PLAN_MAX_DAYS - 1)).isoformat(),
        },
    )


@study_bp.get("/study-plans/<int:plan_id>")
@student_required
def detail(plan_id: int):
    plan = get_owned_or_404(StudyPlan, plan_id)
    return render_template(
        "study_plan/detail.html",
        plan=plan,
        days=plan.days,
        completed_indices=set(plan.completed_day_indices),
    )


@study_bp.get("/study-plans/<int:plan_id>/calendar.ics")
@student_required
def download_calendar(plan_id: int):
    plan = get_owned_or_404(StudyPlan, plan_id)
    subject = plan.subject.subject_name if plan.subject else "study-plan"
    filename = f"{slugify(subject)}_study_plan.ics"
    return send_file(
        BytesIO(build_plan_ics(plan)),
        mimetype="text/calendar; charset=utf-8",
        as_attachment=True,
        download_name=filename,
    )


@study_bp.post("/api/generate-study-plan")
@student_required
@rate_limit(
    "generate-study-plan",
    message="Several study plans were requested recently. Please wait a few minutes.",
)
def api_generate_plan():
    payload = request.get_json(silent=True) or {}
    plan = generate_study_plan(current_user, payload)
    return api_success(
        {
            **study_plan_summary(plan),
            "redirect_url": url_for("study.detail", plan_id=plan.id),
        },
        message="Study plan generated successfully.",
        status=201,
    )


@study_bp.get("/api/study-plans")
@student_required
def api_list_plans():
    plans = (
        StudyPlan.query.filter_by(user_id=current_user.id)
        .order_by(desc(StudyPlan.created_at))
        .all()
    )
    return api_success({"items": [study_plan_summary(plan) for plan in plans]})


@study_bp.get("/api/study-plans/<int:plan_id>")
@student_required
def api_get_plan(plan_id: int):
    plan = get_owned_or_404(StudyPlan, plan_id)
    return api_success(study_plan_detail(plan))


@study_bp.post("/api/study-plans/<int:plan_id>/toggle")
@student_required
def api_toggle_day(plan_id: int):
    plan = get_owned_or_404(StudyPlan, plan_id)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Send a JSON object with the day_index to toggle.")
    day_index = parse_int(payload.get("day_index"), "day_index", minimum=0)
    result = toggle_day(plan, day_index)
    return api_success(result, message="Study day updated.")
