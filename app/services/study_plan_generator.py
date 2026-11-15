"""Study-plan generation, scheduling and completion tracking."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from flask import current_app

from ..constants import (
    LEARNING_LEVELS,
    STUDY_PLAN_MAX_DAYS,
)
from ..extensions import db
from ..models import StudyPlan, Subject, Topic
from ..utils.validation import (
    ValidationError,
    choice,
    clean_text,
    ensure_list_of_strings,
    parse_date,
    parse_float,
    parse_int,
)
from .ai_service import AIService, AIServiceError
from .demo_bank import DemoUnavailable, get_demo_topic_guide
from .prompts import build_study_plan_prompt


def _validate_payload(payload: dict):
    if not isinstance(payload, dict):
        raise ValidationError("Send a JSON object with the study plan options.")
    subject_id = parse_int(payload.get("subject_id"), "subject_id", label="Subject")
    subject = db.session.get(Subject, subject_id)
    if subject is None:
        raise ValidationError("The selected subject does not exist.", "subject_id")

    topic_ids = payload.get("topic_ids") or payload.get("topics") or []
    if not isinstance(topic_ids, (list, tuple)):
        topic_ids = [topic_ids] if topic_ids else []
    cleaned_ids: list[int] = []
    for value in topic_ids:
        try:
            topic_id = int(value)
            if topic_id not in cleaned_ids:
                cleaned_ids.append(topic_id)
        except (TypeError, ValueError):
            pass

    # Support custom topics in study plans
    custom_topics = payload.get("custom_topics") or []
    if isinstance(custom_topics, str):
        custom_topics = [t.strip() for t in custom_topics.split(",") if t.strip()]
    for ct in custom_topics:
        ct_clean = str(ct).strip()[:160]
        if ct_clean:
            top = Topic.query.filter(
                Topic.subject_id == subject.id,
                db.func.lower(Topic.topic_name) == ct_clean.lower()
            ).first()
            if not top:
                top = Topic(subject_id=subject.id, topic_name=ct_clean, description=f"Custom topic: {ct_clean}")
                db.session.add(top)
                db.session.flush()
            if top.id not in cleaned_ids:
                cleaned_ids.append(top.id)

    if not cleaned_ids:
        raise ValidationError("Select or type at least one topic.", "topic_ids")
    if len(cleaned_ids) > 15:
        raise ValidationError("Choose at most 15 topics for one study plan.", "topic_ids")

    topics = Topic.query.filter(Topic.id.in_(cleaned_ids), Topic.subject_id == subject.id).all()
    if len(topics) != len(cleaned_ids):
        raise ValidationError("Some selected topics do not belong to this subject.", "topic_ids")
    topics_by_id = {t.id: t for t in topics}
    ordered_topics = [topics_by_id[tid] for tid in cleaned_ids]

    hours = parse_float(
        payload.get("hours_per_day"),
        "hours_per_day",
        minimum=0.5,
        maximum=12,
        label="Study hours per day",
    )
    target_date = parse_date(payload.get("target_date"), "target_date", "Target completion date")
    today = date.today()
    if target_date < today:
        raise ValidationError("The target date cannot be in the past.", "target_date")
    max_date = today + timedelta(days=STUDY_PLAN_MAX_DAYS - 1)
    if target_date > max_date:
        raise ValidationError(
            f"Choose a target date within the next {STUDY_PLAN_MAX_DAYS} days.", "target_date"
        )
    days_available = (target_date - today).days + 1
    if days_available < len(ordered_topics):
        raise ValidationError(
            "The target date leaves fewer days than topics. Extend the date or choose fewer topics.",
            "target_date",
        )
    level = choice(
        payload.get("learning_level") or payload.get("level"),
        LEARNING_LEVELS,
        "learning_level",
        "learning level",
    )
    return subject, ordered_topics, hours, target_date, days_available, level


def _fallback_guide(topic: Topic, level: str, hours: float) -> dict:
    return get_demo_topic_guide(topic.topic_name, level, hours)


def _normalise_guides(raw: dict, topics: list[Topic], level: str, hours: float) -> tuple[str, dict[int, dict]]:
    by_name = {topic.topic_name.lower(): topic for topic in topics}
    guides: dict[int, dict] = {}
    items = raw.get("topic_guides") if isinstance(raw, dict) else None
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            name = clean_text(item.get("topic"), 160).lower()
            topic = by_name.get(name)
            if topic is None or topic.id in guides:
                continue
            objectives = ensure_list_of_strings(item.get("objectives"), limit=6, item_limit=500)
            activities = ensure_list_of_strings(item.get("activities"), limit=8, item_limit=500)
            practice = ensure_list_of_strings(
                item.get("practice_questions"), limit=6, item_limit=500
            )
            if not objectives:
                objectives = _fallback_guide(topic, level, hours)["objectives"]
            if not activities:
                activities = _fallback_guide(topic, level, hours)["activities"]
            if not practice:
                practice = _fallback_guide(topic, level, hours)["practice_questions"]
            guides[topic.id] = {
                "topic": topic.topic_name,
                "objectives": objectives,
                "activities": activities,
                "practice_questions": practice,
                "revision_minutes": max(10, round(hours * 60 * 0.2)),
            }
    for topic in topics:
        if topic.id not in guides:
            guides[topic.id] = _fallback_guide(topic, level, hours)

    overview = clean_text(raw.get("overview") if isinstance(raw, dict) else "", 2000)
    if not overview:
        overview = (
            f"This plan distributes {len(topics)} topic(s) across the available study days, "
            f"with roughly {hours:g} hour(s) per day and built-in revision time. "
            "Each day combines reading, active recall and practice, with spaced review of earlier topics."
        )
    return overview, guides


def _build_days(
    topics: list[Topic],
    guides: dict[int, dict],
    *,
    start_date: date,
    days_count: int,
    hours: float,
) -> list[dict]:
    total_minutes = max(30, round(hours * 60))
    revision_minutes = max(10, round(total_minutes * 0.2))
    study_minutes = max(15, total_minutes - revision_minutes)
    days: list[dict] = []

    for index in range(days_count):
        topic = topics[index % len(topics)]
        guide = guides[topic.id]
        is_revision = index >= len(topics)
        day_date = start_date + timedelta(days=index)
        objectives = list(guide["objectives"])
        activities = list(guide["activities"])
        if is_revision:
            objectives = [
                f"Revise and strengthen: {obj}" for obj in objectives[:2]
            ] + ["Complete a mixed recall test without notes"]
            activities = [
                "Revisit the summary and redo the practice questions.",
                "Explain the topic aloud, then fill any gaps in your notes.",
                "Complete a timed mini-quiz and review every mistake.",
            ]
        days.append(
            {
                "day": index + 1,
                "date": day_date.isoformat(),
                "weekday": day_date.strftime("%A"),
                "topic": topic.topic_name,
                "topic_id": topic.id,
                "is_revision": is_revision,
                "objectives": objectives,
                "duration_minutes": study_minutes,
                "revision_minutes": revision_minutes,
                "activities": activities,
                "practice_questions": list(guide["practice_questions"]),
            }
        )
    return days


def generate_study_plan(user, payload: dict) -> StudyPlan:
    subject, topics, hours, target_date, days_available, level = _validate_payload(payload)
    config = current_app.config
    ai = AIService(config)
    profile = user.profile
    mode = "demo"
    note = ""
    overview = ""
    guides: dict[int, dict] = {}

    if ai.is_live_available():
        system_prompt, user_prompt = build_study_plan_prompt(
            subject_name=subject.subject_name,
            topics=[topic.topic_name for topic in topics],
            hours_per_day=hours,
            target_date=target_date.isoformat(),
            days=days_available,
            level=level,
            language=(profile.preferred_language if profile else "English"),
            profile=profile,
        )
        try:
            raw = ai.generate_json(
                system_prompt,
                user_prompt,
                max_tokens=config.get("AI_MAX_TOKENS_PLAN", 4000),
                temperature=0.5,
            )
            overview, guides = _normalise_guides(raw, topics, level, hours)
            mode = "live"
        except AIServiceError as exc:
            current_app.logger.warning("Study plan generation failed: %s", exc.message)
            if config.get("AI_DEMO_MODE") == "off":
                raise
            overview, guides = _normalise_guides({}, topics, level, hours)
            mode = "demo_fallback"
            note = (
                f"Live AI was unavailable: {exc.message} The schedule and study guidance were "
                "assembled offline. This is labelled demo content."
            )
    else:
        if config.get("AI_DEMO_MODE") == "off":
            raise AIServiceError(
                "Live AI is required (AI_DEMO_MODE=off) but AI_API_KEY is not configured.",
                code="ai_not_configured",
                status=503,
            )
        overview, guides = _normalise_guides({}, topics, level, hours)
        mode = "demo"
        note = (
            "Demo mode: this schedule and study guidance were assembled from the offline demo "
            "library, not generated by a live AI model."
        )

    days = _build_days(
        topics,
        guides,
        start_date=date.today(),
        days_count=days_available,
        hours=hours,
    )
    plan_data = {
        "overview": overview,
        "subject": subject.subject_name,
        "level": level,
        "hours_per_day": hours,
        "target_date": target_date.isoformat(),
        "created": datetime.utcnow().date().isoformat(),
        "topic_count": len(topics),
        "days": days,
    }
    plan = StudyPlan(
        user_id=user.id,
        subject_id=subject.id,
        learning_level=level,
        hours_per_day=hours,
        target_date=target_date,
        plan_data=plan_data,
        completion_status={"completed_days": [], "completed": False},
        ai_mode=mode,
        ai_note=note or None,
    )
    db.session.add(plan)
    db.session.commit()
    return plan


def toggle_day(plan: StudyPlan, day_index: int) -> dict:
    if day_index < 0 or day_index >= plan.total_days:
        raise ValidationError("That study day does not exist in this plan.", "day_index")
    completed = set(plan.completed_day_indices)
    if day_index in completed:
        completed.remove(day_index)
    else:
        completed.add(day_index)
    ordered = sorted(completed)
    plan.completion_status = {
        "completed_days": ordered,
        "completed": len(ordered) == plan.total_days,
        "updated_at": datetime.utcnow().isoformat(),
    }
    db.session.commit()
    return {
        "day_index": day_index,
        "completed": day_index in completed,
        "completed_days": len(ordered),
        "total_days": plan.total_days,
        "percentage": plan.completion_percentage,
        "plan_complete": plan.is_complete,
    }
