"""Personalized learning-content generation (live AI or labelled demo)."""
from __future__ import annotations

from flask import current_app

from ..constants import CONTENT_TYPES, LANGUAGES, LEARNING_LEVELS, LEARNING_STYLES
from ..extensions import db
from ..models import LearningContent, Subject, Topic
from ..utils.validation import (
    ValidationError,
    clean_text,
    clean_multiline,
    choice,
    ensure_list_of_strings,
    parse_int,
)
from .ai_service import AIService, AIServiceError
from .demo_bank import build_demo_content
from .prompts import build_content_prompt

CONTENT_KEYS = [
    "title",
    "introduction",
    "learning_objectives",
    "basic_concepts",
    "detailed_explanation",
    "important_definitions",
    "key_terms",
    "step_by_step",
    "real_world_examples",
    "practical_applications",
    "advantages",
    "disadvantages",
    "important_points",
    "summary",
    "revision_tips",
    "faqs",
]


def _text(value, limit: int = 24000) -> str:
    return clean_multiline(value, limit)


def _dict_items(value, first_key: str, second_key: str, limit: int = 20) -> list[dict]:
    if not isinstance(value, (list, tuple)):
        return []
    result: list[dict] = []
    for item in value:
        if isinstance(item, dict):
            first = clean_text(
                item.get(first_key) or item.get("heading") or item.get("title") or item.get("term"), 200
            )
            second = clean_multiline(
                item.get(second_key) or item.get("explanation") or item.get("definition") or item.get("answer"),
                3000,
            )
        else:
            first = f"Concept {len(result) + 1}"
            second = clean_multiline(item, 3000)
        if first and second:
            result.append({first_key: first, second_key: second})
        elif second:
            result.append({first_key: f"Concept {len(result) + 1}", second_key: second})
        if len(result) >= limit:
            break
    return result


def normalize_content(raw: dict, topic_name: str) -> dict:
    if not isinstance(raw, dict):
        raise AIServiceError(
            "The AI response was not a valid content object.", code="ai_invalid_response"
        )

    content = {
        "title": clean_text(raw.get("title") or topic_name, 220) or topic_name,
        "introduction": _text(raw.get("introduction") or raw.get("intro")),
        "learning_objectives": ensure_list_of_strings(
            raw.get("learning_objectives") or raw.get("objectives"), limit=10, item_limit=500
        ),
        "basic_concepts": _dict_items(
            raw.get("basic_concepts") or raw.get("concepts"), "heading", "explanation", limit=10
        ),
        "detailed_explanation": _text(
            raw.get("detailed_explanation") or raw.get("explanation") or raw.get("detailed_explanation_text")
        ),
        "important_definitions": _dict_items(
            raw.get("important_definitions") or raw.get("definitions"), "term", "definition", limit=20
        ),
        "key_terms": ensure_list_of_strings(raw.get("key_terms"), limit=20, item_limit=200),
        "step_by_step": ensure_list_of_strings(
            raw.get("step_by_step") or raw.get("steps"), limit=20, item_limit=1000
        ),
        "real_world_examples": ensure_list_of_strings(
            raw.get("real_world_examples") or raw.get("examples"), limit=10, item_limit=3000
        ),
        "practical_applications": ensure_list_of_strings(
            raw.get("practical_applications") or raw.get("applications"), limit=10, item_limit=1000
        ),
        "advantages": ensure_list_of_strings(raw.get("advantages"), limit=8, item_limit=800),
        "disadvantages": ensure_list_of_strings(raw.get("disadvantages"), limit=8, item_limit=800),
        "important_points": ensure_list_of_strings(
            raw.get("important_points"), limit=15, item_limit=1000
        ),
        "summary": _text(raw.get("summary")),
        "revision_tips": ensure_list_of_strings(
            raw.get("revision_tips"), limit=10, item_limit=600
        ),
        "faqs": _dict_items(raw.get("faqs"), "question", "answer", limit=10),
    }

    has_body = any(
        [
            content["introduction"],
            content["detailed_explanation"],
            content["basic_concepts"],
            content["summary"],
            content["learning_objectives"],
        ]
    )
    if not has_body:
        raise AIServiceError(
            "The AI response did not include usable learning content. Please try again.",
            code="ai_invalid_response",
        )
    return content


def _validate_payload(payload: dict) -> tuple[Subject, Topic, str, str, str, str]:
    if not isinstance(payload, dict):
        raise ValidationError("Send a JSON object with the generation options.")

    # Subject resolution
    custom_subject = clean_text(payload.get("custom_subject") or "", 120)
    subject_id_raw = payload.get("subject_id")
    subject = None
    if subject_id_raw:
        try:
            subject = db.session.get(Subject, int(subject_id_raw))
        except (TypeError, ValueError):
            pass
    if subject is None:
        if custom_subject:
            subject = Subject.query.filter(db.func.lower(Subject.subject_name) == custom_subject.lower()).first()
            if not subject:
                subject = Subject(subject_name=custom_subject, description=f"Custom curriculum: {custom_subject}")
                db.session.add(subject)
                db.session.flush()
        else:
            raise ValidationError("The selected subject does not exist.", "subject_id")

    # Topic resolution (supports custom_topic or topic_id)
    custom_topic = clean_text(payload.get("custom_topic") or payload.get("custom_topic_name") or "", 160)
    topic_id_raw = payload.get("topic_id")
    topic = None

    if custom_topic:
        topic = Topic.query.filter(
            Topic.subject_id == subject.id,
            db.func.lower(Topic.topic_name) == custom_topic.lower()
        ).first()
        if not topic:
            topic = Topic(subject_id=subject.id, topic_name=custom_topic, description=f"Custom topic: {custom_topic}")
            db.session.add(topic)
            db.session.flush()
    else:
        topic_id = parse_int(topic_id_raw, "topic_id", label="Topic")
        topic = db.session.get(Topic, topic_id)
        if topic is None or topic.subject_id != subject.id:
            raise ValidationError("Choose a topic that belongs to the selected subject.", "topic_id")

    level = choice(
        payload.get("learning_level") or payload.get("level"),
        LEARNING_LEVELS,
        "learning_level",
        "learning level",
    )
    content_type = choice(
        payload.get("content_type"), CONTENT_TYPES, "content_type", "content type"
    )
    language = choice(
        payload.get("language") or payload.get("preferred_language"),
        LANGUAGES,
        "language",
        "language",
    )
    style = choice(
        payload.get("explanation_style") or payload.get("style"),
        LEARNING_STYLES,
        "explanation_style",
        "learning style",
    )
    return subject, topic, level, content_type, language, style


def generate_learning_content(user, payload: dict) -> LearningContent:
    subject, topic, level, content_type, language, style = _validate_payload(payload)
    config = current_app.config

    ai_engine = str(payload.get("ai_engine") or payload.get("ai_model") or "").strip()
    custom_prov, custom_mod = None, None
    if ":" in ai_engine:
        custom_prov, custom_mod = ai_engine.split(":", 1)
    elif ai_engine:
        custom_prov = ai_engine

    if custom_prov == "offline":
        ai = None
    else:
        ai = AIService(config, provider=custom_prov, model=custom_mod)

    profile = user.profile

    content: dict | None = None
    mode = "demo"
    note = ""

    if ai and ai.is_live_available():
        system_prompt, user_prompt = build_content_prompt(
            subject_name=subject.subject_name,
            subject_description=subject.description or "",
            topic_name=topic.topic_name,
            topic_description=topic.description or "",
            level=level,
            content_type=content_type,
            language=language,
            style=style,
            profile=profile,
        )
        try:
            raw = ai.generate_json(
                system_prompt,
                user_prompt,
                max_tokens=config.get("AI_MAX_TOKENS_CONTENT", 6000),
            )
            content = normalize_content(raw, topic.topic_name)
            mode = "live"
        except AIServiceError as exc:
            current_app.logger.warning("Content generation failed: %s", exc.message)
            if config.get("AI_DEMO_MODE") == "off":
                raise
            content, demo_note = build_demo_content(
                subject_name=subject.subject_name,
                topic_name=topic.topic_name,
                level=level,
                content_type=content_type,
                language=language,
                style=style,
            )
            mode = "demo_fallback"
            note = f"Live AI was unavailable: {exc.message} {demo_note}"
    else:
        if config.get("AI_DEMO_MODE") == "off":
            raise AIServiceError(
                "Live AI is required (AI_DEMO_MODE=off) but AI_API_KEY is not configured.",
                code="ai_not_configured",
                status=503,
            )
        content, note = build_demo_content(
            subject_name=subject.subject_name,
            topic_name=topic.topic_name,
            level=level,
            content_type=content_type,
            language=language,
            style=style,
        )
        mode = "demo"

    record = LearningContent(
        user_id=user.id,
        subject_id=subject.id,
        topic_id=topic.id,
        title=(content.get("title") or topic.topic_name)[:220],
        learning_level=level,
        content_type=content_type,
        language=language,
        explanation_style=style,
        generated_content=content,
        ai_mode=mode,
        ai_note=note or None,
    )
    db.session.add(record)
    db.session.commit()

    if payload.get("create_flashcards"):
        try:
            from .flashcard_service import generate_deck
            generate_deck(user, {"content_id": record.id})
        except Exception as e:
            current_app.logger.warning("Auto-flashcard creation skipped: %s", e)

    return record
