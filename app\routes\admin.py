"""Admin dashboard, user overview, catalog management and admin API."""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time, timedelta

from flask import Blueprint, abort, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import desc, func, or_

from ..constants import LEARNING_LEVELS
from ..decorators import admin_required
from ..extensions import db
from ..models import (
    LearningContent,
    Quiz,
    QuizAttempt,
    StudyPlan,
    Subject,
    Topic,
    User,
)
from ..utils.pagination import paginate
from ..utils.responses import api_error, api_success
from ..utils.validation import (
    ValidationError,
    clean_multiline,
    clean_text,
    parse_int,
    require_text,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
admin_api_bp = Blueprint("admin_api", __name__, url_prefix="/api/admin")


def _dashboard_stats() -> dict:
    today = date.today()
    start_day = today - timedelta(days=13)
    start_dt = datetime.combine(start_day, time.min)

    total_students = User.query.filter_by(role="student").count()
    total_contents = LearningContent.query.count()
    total_quizzes = Quiz.query.count()
    total_attempts = QuizAttempt.query.count()
    total_plans = StudyPlan.query.count()
    avg_score = round(
        float(db.session.query(func.avg(QuizAttempt.percentage)).scalar() or 0), 1
    )

    active_ids = {
        user_id for (user_id,) in db.session.query(LearningContent.user_id).distinct().all()
    }
    active_ids.update(
        user_id for (user_id,) in db.session.query(QuizAttempt.user_id).distinct().all()
    )

    subject_rows = (
        db.session.query(Subject.subject_name, func.count(LearningContent.id))
        .join(LearningContent, LearningContent.subject_id == Subject.id)
        .group_by(Subject.id)
        .order_by(func.count(LearningContent.id).desc())
        .limit(6)
        .all()
    )
    subject_popularity = [
        {"subject": name, "count": count} for name, count in subject_rows
    ]

    topic_rows = (
        db.session.query(Topic.topic_name, Subject.subject_name, func.count(LearningContent.id))
        .join(LearningContent, LearningContent.topic_id == Topic.id)
        .join(Subject, Subject.id == Topic.subject_id)
        .group_by(Topic.id)
        .order_by(func.count(LearningContent.id).desc())
        .limit(6)
        .all()
    )
    topic_popularity = [
        {"topic": topic, "subject": subject, "count": count}
        for topic, subject, count in topic_rows
    ]

    level_counts = dict(
        db.session.query(LearningContent.learning_level, func.count(LearningContent.id))
        .group_by(LearningContent.learning_level)
        .all()
    )
    level_distribution = [
        {"level": level, "count": level_counts.get(level, 0)} for level in LEARNING_LEVELS
    ]

    registrations = User.query.filter(
        User.role == "student", User.created_at >= start_dt
    ).all()
    reg_counts = Counter(user.created_at.date() for user in registrations)
    contents_recent = LearningContent.query.filter(
        LearningContent.created_at >= start_dt
    ).all()
    attempts_recent = QuizAttempt.query.filter(
        QuizAttempt.attempted_at >= start_dt
    ).all()
    activity_counts: Counter = Counter()
    for content in contents_recent:
        activity_counts[content.created_at.date()] += 1
    for attempt in attempts_recent:
        activity_counts[attempt.attempted_at.date()] += 1

    series = []
    for offset in range(13, -1, -1):
        day = today - timedelta(days=offset)
        series.append(
            {
                "date": day.isoformat(),
                "label": day.strftime("%d %b"),
                "registrations": reg_counts.get(day, 0),
                "activity": activity_counts.get(day, 0),
            }
        )

    recent_students = (
        User.query.filter_by(role="student").order_by(desc(User.created_at)).limit(6).all()
    )
    recent_contents = (
        LearningContent.query.order_by(desc(LearningContent.created_at)).limit(6).all()
    )
    recent_attempts = (
        QuizAttempt.query.order_by(desc(QuizAttempt.attempted_at)).limit(6).all()
    )

    events = []
    for user in recent_students:
        events.append(
            {
                "kind": "user",
                "icon": "bi-person-plus",
                "tone": "primary",
                "title": f"{user.name} joined",
                "detail": user.email,
                "at": user.created_at,
                "url": url_for("admin.users"),
            }
        )
    for content in recent_contents:
        events.append(
            {
                "kind": "content",
                "icon": "bi-journal-plus",
                "tone": "success",
                "title": f"{content.user.name if content.user else 'A student'} generated {content.content_type}",
                "detail": f"{content.subject.subject_name if content.subject else ''} · {content.topic.topic_name if content.topic else content.title}",
                "at": content.created_at,
                "url": None,
            }
        )
    for attempt in recent_attempts:
        quiz = attempt.quiz
        events.append(
            {
                "kind": "quiz",
                "icon": "bi-patch-check",
                "tone": "warning",
                "title": f"{attempt.user.name if attempt.user else 'A student'} scored {attempt.percentage:g}%",
                "detail": quiz.topic.topic_name if quiz and quiz.topic else "Quiz attempt",
                "at": attempt.attempted_at,
                "url": None,
            }
        )
    events.sort(key=lambda item: item["at"], reverse=True)

    return {
        "total_students": total_students,
        "active_students": len(active_ids),
        "total_contents": total_contents,
        "total_quizzes": total_quizzes,
        "total_attempts": total_attempts,
        "total_plans": total_plans,
        "avg_score": avg_score,
        "subjects_count": Subject.query.count(),
        "topics_count": Topic.query.count(),
        "subject_popularity": subject_popularity,
        "topic_popularity": topic_popularity,
        "level_distribution": level_distribution,
        "series": series,
        "recent_students": recent_students,
        "recent_events": events[:10],
    }


@admin_bp.get("/")
@admin_required
def dashboard():
    stats = _dashboard_stats()
    chart_data = {
        "series": stats["series"],
        "subjects": stats["subject_popularity"],
        "topics": stats["topic_popularity"],
        "levels": stats["level_distribution"],
    }
    return render_template("admin/dashboard.html", stats=stats, chart_data=chart_data)


@admin_bp.get("/users")
@admin_required
def users():
    q = clean_text(request.args.get("q", ""), 120)
    page = request.args.get("page", 1, type=int)
    query = User.query.filter_by(role="student")
    if q:
        pattern = f"%{q}%"
        query = query.filter(or_(User.name.ilike(pattern), User.email.ilike(pattern)))
    pagination = paginate(query.order_by(desc(User.created_at)), page=page, per_page=12)

    ids = [user.id for user in pagination["items"]]
    content_counts = {}
    attempt_counts = {}
    if ids:
        content_counts = dict(
            db.session.query(LearningContent.user_id, func.count(LearningContent.id))
            .filter(LearningContent.user_id.in_(ids))
            .group_by(LearningContent.user_id)
            .all()
        )
        attempt_counts = dict(
            db.session.query(QuizAttempt.user_id, func.count(QuizAttempt.id))
            .filter(QuizAttempt.user_id.in_(ids))
            .group_by(QuizAttempt.user_id)
            .all()
        )
    return render_template(
        "admin/users.html",
        pagination=pagination,
        q=q,
        content_counts=content_counts,
        attempt_counts=attempt_counts,
    )


@admin_bp.get("/subjects")
@admin_required
def subjects():
    rows = Subject.query.order_by(Subject.subject_name).all()
    content_counts = dict(
        db.session.query(LearningContent.subject_id, func.count(LearningContent.id))
        .group_by(LearningContent.subject_id)
        .all()
    )
    return render_template(
        "admin/subjects.html",
        subjects=rows,
        content_counts=content_counts,
        api_base=url_for("admin_api.create_subject"),
    )


@admin_bp.get("/topics")
@admin_required
def topics():
    subject_id = request.args.get("subject", type=int)
    query = Topic.query.join(Subject)
    if subject_id:
        query = query.filter(Topic.subject_id == subject_id)
    rows = query.order_by(Subject.subject_name, Topic.topic_name).all()
    subjects_list = Subject.query.order_by(Subject.subject_name).all()
    content_counts = dict(
        db.session.query(LearningContent.topic_id, func.count(LearningContent.id))
        .group_by(LearningContent.topic_id)
        .all()
    )
    return render_template(
        "admin/topics.html",
        topics=rows,
        subjects=subjects_list,
        subject_id=subject_id,
        content_counts=content_counts,
    )


# ----------------------------------------------------------------------
# Admin API
# ----------------------------------------------------------------------
def _json_payload() -> dict:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Send a JSON object with the required fields.")
    return payload


@admin_api_bp.get("/stats")
@admin_required
def api_stats():
    stats = _dashboard_stats()
    return api_success(
        {
            "total_students": stats["total_students"],
            "active_students": stats["active_students"],
            "total_contents": stats["total_contents"],
            "total_quizzes": stats["total_quizzes"],
            "total_attempts": stats["total_attempts"],
            "avg_score": stats["avg_score"],
            "subjects_count": stats["subjects_count"],
            "topics_count": stats["topics_count"],
            "subject_popularity": stats["subject_popularity"],
            "topic_popularity": stats["topic_popularity"],
        }
    )


@admin_api_bp.post("/subjects")
@admin_required
def create_subject():
    payload = _json_payload()
    name = require_text(
        payload.get("subject_name") or payload.get("name"), "subject_name", "Subject name", 120
    )
    description = clean_multiline(payload.get("description"), 1000)
    if Subject.query.filter(func.lower(Subject.subject_name) == name.lower()).first():
        return api_error(
            "A subject with that name already exists.", status=409, code="duplicate_subject"
        )
    subject = Subject(subject_name=name, description=description or None)
    db.session.add(subject)
    db.session.commit()
    return api_success(
        {"id": subject.id, "subject_name": subject.subject_name},
        message="Subject created.",
        status=201,
    )


@admin_api_bp.put("/subjects/<int:subject_id>")
@admin_required
def update_subject(subject_id: int):
    subject = db.session.get(Subject, subject_id)
    if subject is None:
        abort(404)
    payload = _json_payload()
    if "subject_name" in payload or "name" in payload:
        name = require_text(
            payload.get("subject_name") or payload.get("name"),
            "subject_name",
            "Subject name",
            120,
        )
        duplicate = Subject.query.filter(
            func.lower(Subject.subject_name) == name.lower(), Subject.id != subject.id
        ).first()
        if duplicate:
            return api_error(
                "A subject with that name already exists.", status=409, code="duplicate_subject"
            )
        subject.subject_name = name
    if "description" in payload:
        subject.description = clean_multiline(payload.get("description"), 1000) or None
    db.session.commit()
    return api_success(
        {"id": subject.id, "subject_name": subject.subject_name}, message="Subject updated."
    )


@admin_api_bp.delete("/subjects/<int:subject_id>")
@admin_required
def delete_subject(subject_id: int):
    subject = db.session.get(Subject, subject_id)
    if subject is None:
        abort(404)
    used = {
        "learning materials": LearningContent.query.filter_by(subject_id=subject.id).count(),
        "quizzes": Quiz.query.filter_by(subject_id=subject.id).count(),
        "study plans": StudyPlan.query.filter_by(subject_id=subject.id).count(),
    }
    active = [f"{count} {label}" for label, count in used.items() if count]
    if active:
        return api_error(
            "This subject is used by " + ", ".join(active) + ". Remove those records first.",
            status=409,
            code="subject_in_use",
        )
    db.session.delete(subject)
    db.session.commit()
    return api_success({"id": subject_id}, message="Subject deleted.")


@admin_api_bp.post("/topics")
@admin_required
def create_topic():
    payload = _json_payload()
    subject_id = parse_int(payload.get("subject_id"), "subject_id", label="Subject")
    subject = db.session.get(Subject, subject_id)
    if subject is None:
        raise ValidationError("The selected subject does not exist.", "subject_id")
    name = require_text(
        payload.get("topic_name") or payload.get("name"), "topic_name", "Topic name", 160
    )
    description = clean_multiline(payload.get("description"), 1000)
    duplicate = Topic.query.filter(
        Topic.subject_id == subject.id, func.lower(Topic.topic_name) == name.lower()
    ).first()
    if duplicate:
        return api_error(
            "That topic already exists in this subject.",
            status=409,
            code="duplicate_topic",
        )
    topic = Topic(subject_id=subject.id, topic_name=name, description=description or None)
    db.session.add(topic)
    db.session.commit()
    return api_success(
        {
            "id": topic.id,
            "topic_name": topic.topic_name,
            "subject_id": topic.subject_id,
            "subject_name": subject.subject_name,
        },
        message="Topic created.",
        status=201,
    )


@admin_api_bp.put("/topics/<int:topic_id>")
@admin_required
def update_topic(topic_id: int):
    topic = db.session.get(Topic, topic_id)
    if topic is None:
        abort(404)
    payload = _json_payload()
    subject_id = topic.subject_id
    if "subject_id" in payload:
        subject_id = parse_int(payload.get("subject_id"), "subject_id", label="Subject")
        if db.session.get(Subject, subject_id) is None:
            raise ValidationError("The selected subject does not exist.", "subject_id")
    if "topic_name" in payload or "name" in payload:
        name = require_text(
            payload.get("topic_name") or payload.get("name"),
            "topic_name",
            "Topic name",
            160,
        )
        duplicate = Topic.query.filter(
            Topic.subject_id == subject_id,
            func.lower(Topic.topic_name) == name.lower(),
            Topic.id != topic.id,
        ).first()
        if duplicate:
            return api_error(
                "That topic already exists in this subject.",
                status=409,
                code="duplicate_topic",
            )
        topic.topic_name = name
    topic.subject_id = subject_id
    if "description" in payload:
        topic.description = clean_multiline(payload.get("description"), 1000) or None
    db.session.commit()
    return api_success(
        {
            "id": topic.id,
            "topic_name": topic.topic_name,
            "subject_id": topic.subject_id,
        },
        message="Topic updated.",
    )


@admin_api_bp.delete("/topics/<int:topic_id>")
@admin_required
def delete_topic(topic_id: int):
    topic = db.session.get(Topic, topic_id)
    if topic is None:
        abort(404)
    used = {
        "learning materials": LearningContent.query.filter_by(topic_id=topic.id).count(),
        "quizzes": Quiz.query.filter_by(topic_id=topic.id).count(),
    }
    active = [f"{count} {label}" for label, count in used.items() if count]
    if active:
        return api_error(
            "This topic is used by " + ", ".join(active) + ". Remove those records first.",
            status=409,
            code="topic_in_use",
        )
    db.session.delete(topic)
    db.session.commit()
    return api_success({"id": topic_id}, message="Topic deleted.")
