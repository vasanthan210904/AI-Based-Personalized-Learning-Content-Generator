"""Student dashboard, profile and learning preferences."""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from ..constants import LANGUAGES, LEARNING_LEVELS, LEARNING_STYLES, YEARS
from ..decorators import student_required
from ..extensions import db
from ..forms import PreferencesForm, ProfileForm
from ..models import StudentProfile, Subject, User
from ..services.progress_service import learning_summary, recent_study_activity
from ..utils.responses import api_success, form_errors
from ..utils.serializers import user_dict
from ..utils.validation import (
    ValidationError,
    choice,
    clean_multiline,
    clean_text,
    require_text,
)

student_bp = Blueprint("student", __name__)


def _ensure_profile(user) -> StudentProfile:
    if user.profile:
        return user.profile
    profile = StudentProfile(user_id=user.id)
    db.session.add(profile)
    db.session.commit()
    return profile


@student_bp.get("/dashboard")
@student_required
def dashboard():
    _ensure_profile(current_user)
    summary = learning_summary(current_user)
    activity = recent_study_activity(current_user, 6)
    subjects = Subject.query.order_by(Subject.subject_name).all()
    return render_template(
        "student/dashboard.html",
        summary=summary,
        activity=activity,
        subjects=subjects,
    )


@student_bp.route("/profile", methods=["GET", "POST"])
@student_required
def profile():
    record = _ensure_profile(current_user)
    form = ProfileForm(obj=record)
    if request.method == "GET":
        form.name.data = current_user.name
    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        record.course = form.course.data.strip()
        record.department = form.department.data.strip()
        record.year = form.year.data
        db.session.commit()
        flash("Your profile has been updated.", "success")
        return redirect(url_for("student.profile"))
    elif request.method == "POST":
        flash("Please correct the highlighted fields.", "danger")

    summary = learning_summary(current_user)
    return render_template("student/profile.html", form=form, profile=record, summary=summary)


@student_bp.route("/preferences", methods=["GET", "POST"])
@student_required
def preferences():
    record = _ensure_profile(current_user)
    form = PreferencesForm()
    subjects = Subject.query.order_by(Subject.subject_name).all()
    form.interested_subjects.choices = [
        (subject.subject_name, subject.subject_name) for subject in subjects
    ]

    if request.method == "GET":
        form.learning_level.data = record.learning_level
        form.learning_style.data = record.learning_style
        form.preferred_language.data = record.preferred_language
        form.learning_goals.data = record.learning_goals
        form.interested_subjects.data = record.subject_list

    if form.validate_on_submit():
        record.learning_level = form.learning_level.data
        record.learning_style = form.learning_style.data
        record.preferred_language = form.preferred_language.data
        record.learning_goals = clean_multiline(form.learning_goals.data, 1000) or None
        record.set_subjects(form.interested_subjects.data)
        db.session.commit()
        flash(
            "Preferences saved. Future materials and quizzes will use these settings.",
            "success",
        )
        return redirect(url_for("student.dashboard"))
    elif request.method == "POST":
        flash("Please correct the highlighted fields.", "danger")

    return render_template(
        "student/preferences.html",
        form=form,
        profile=record,
        subjects=subjects,
    )


# ----------------------------------------------------------------------
# JSON API
# ----------------------------------------------------------------------
@student_bp.get("/api/profile")
@login_required
def api_profile_get():
    return api_success(user_dict(current_user))


@student_bp.put("/api/profile")
@login_required
def api_profile_update():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Send a JSON object with profile fields.")
    record = _ensure_profile(current_user)
    updated = False

    if "name" in payload:
        current_user.name = require_text(payload.get("name"), "name", "Full name", 120)
        if len(current_user.name) < 3:
            raise ValidationError("Full name must be at least 3 characters.", "name")
        updated = True
    if "course" in payload:
        record.course = require_text(payload.get("course"), "course", "Course", 120)
        updated = True
    if "department" in payload:
        record.department = require_text(
            payload.get("department"), "department", "Department", 120
        )
        updated = True
    if "year" in payload:
        record.year = choice(payload.get("year"), YEARS, "year", "year of study")
        updated = True
    if "learning_level" in payload:
        record.learning_level = choice(
            payload.get("learning_level"), LEARNING_LEVELS, "learning_level", "learning level"
        )
        updated = True
    if "learning_style" in payload:
        record.learning_style = choice(
            payload.get("learning_style"), LEARNING_STYLES, "learning_style", "learning style"
        )
        updated = True
    if "preferred_language" in payload:
        record.preferred_language = choice(
            payload.get("preferred_language"), LANGUAGES, "preferred_language", "language"
        )
        updated = True
    if "learning_goals" in payload:
        record.learning_goals = clean_multiline(payload.get("learning_goals"), 1000) or None
        updated = True
    if "interested_subjects" in payload:
        raw = payload.get("interested_subjects") or []
        if isinstance(raw, str):
            raw = [part.strip() for part in raw.split(",") if part.strip()]
        if not isinstance(raw, (list, tuple)):
            raise ValidationError(
                "Interested subjects must be a list of subject names.",
                "interested_subjects",
            )
        chosen = []
        for name in raw:
            cleaned = clean_text(name, 120)
            subject = Subject.query.filter(
                func.lower(Subject.subject_name) == cleaned.lower()
            ).first()
            if subject is None:
                raise ValidationError(
                    f"Unknown subject: {cleaned}.", "interested_subjects"
                )
            if subject.subject_name not in chosen:
                chosen.append(subject.subject_name)
        record.set_subjects(chosen)
        updated = True

    if not updated:
        raise ValidationError("No supported profile fields were provided.")
    db.session.commit()
    return api_success(user_dict(current_user), message="Profile updated.")
