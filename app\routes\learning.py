"""Learning content generation pages and API."""
from __future__ import annotations

from io import BytesIO

from flask import Blueprint, render_template, request, send_file, url_for
from flask_login import current_user

from ..constants import CONTENT_TYPES
from ..decorators import student_required
from ..extensions import db
from ..models import ContentBookmark, ContentShare, FlashcardDeck, LearningContent, Subject, Topic
from ..services.ai_service import AIServiceError  # noqa: F401 (re-exported for clarity)
from ..services.content_generator import generate_learning_content
from ..services.demo_bank import DEMO_TOPICS
from ..services.export_service import build_content_markdown
from ..services.pdf_service import build_content_pdf
from ..utils.catalog import subjects_with_topics
from ..utils.pagination import paginate
from ..utils.rate_limit import rate_limit
from ..utils.responses import api_success
from ..utils.security import get_owned_or_404
from ..utils.serializers import content_detail, content_summary
from ..utils.validation import clean_text, slugify

learning_bp = Blueprint("learning", __name__)


def _history_query(user, q: str, subject_id: int | None):
    query = LearningContent.query.filter_by(user_id=user.id)
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            db.or_(
                LearningContent.title.ilike(pattern),
                LearningContent.topic.has(Topic.topic_name.ilike(pattern)),
                LearningContent.subject.has(Subject.subject_name.ilike(pattern)),
            )
        )
    if subject_id:
        query = query.filter(LearningContent.subject_id == subject_id)
    return query.order_by(LearningContent.created_at.desc())


@learning_bp.get("/generate")
@student_required
def generate():
    profile = current_user.profile
    requested_type = request.args.get("type")
    defaults = {
        "subject_id": request.args.get("subject", type=int),
        "topic_id": request.args.get("topic", type=int),
        "learning_level": request.args.get("level")
        or (profile.learning_level if profile else "Beginner"),
        "content_type": requested_type
        if requested_type in CONTENT_TYPES
        else "Detailed Notes",
        "language": profile.preferred_language if profile else "English",
        "explanation_style": profile.learning_style if profile else "Simple Explanation",
    }
    return render_template(
        "learning/generator.html",
        subjects_data=subjects_with_topics(),
        defaults=defaults,
        demo_topics=DEMO_TOPICS,
    )


@learning_bp.get("/learning/content/<int:content_id>")
@student_required
def view_content(content_id: int):
    content = get_owned_or_404(LearningContent, content_id)
    bookmark = ContentBookmark.query.filter_by(
        user_id=current_user.id, content_id=content.id
    ).first()
    share = ContentShare.query.filter_by(content_id=content.id).first()
    return render_template(
        "learning/viewer.html",
        content=content,
        data=content.generated_content or {},
        bookmark=bookmark,
        share=share,
    )


@learning_bp.get("/learning/history")
@student_required
def history():
    q = clean_text(request.args.get("q", ""), 120)
    subject_id = request.args.get("subject", type=int)
    page = request.args.get("page", 1, type=int)
    pagination = paginate(_history_query(current_user, q, subject_id), page=page, per_page=8)
    subjects = Subject.query.order_by(Subject.subject_name).all()
    saved_ids = {
        item.content_id
        for item in ContentBookmark.query.filter_by(user_id=current_user.id).all()
    }
    return render_template(
        "learning/history.html",
        pagination=pagination,
        q=q,
        subject_id=subject_id,
        subjects=subjects,
        saved_ids=saved_ids,
    )


@learning_bp.post("/api/generate-content")
@student_required
@rate_limit(
    "generate-content",
    message="You have generated a lot of material recently. Please wait a few minutes before trying again.",
)
def api_generate_content():
    payload = request.get_json(silent=True) or {}
    record = generate_learning_content(current_user, payload)
    return api_success(
        content_detail(record), message="Learning material generated successfully.", status=201
    )


@learning_bp.get("/api/learning-content")
@student_required
def api_list_content():
    q = clean_text(request.args.get("q", ""), 120)
    subject_id = request.args.get("subject", type=int)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 9, type=int)
    pagination = paginate(
        _history_query(current_user, q, subject_id), page=page, per_page=min(per_page, 50)
    )
    return api_success(
        {
            "items": [content_summary(item) for item in pagination["items"]],
            "pagination": {
                key: pagination[key]
                for key in ("total", "page", "pages", "per_page", "has_prev", "has_next")
            },
        }
    )


@learning_bp.get("/api/learning-content/<int:content_id>")
@student_required
def api_get_content(content_id: int):
    record = get_owned_or_404(LearningContent, content_id)
    return api_success(content_detail(record))


@learning_bp.delete("/api/learning-content/<int:content_id>")
@student_required
def api_delete_content(content_id: int):
    record = get_owned_or_404(LearningContent, content_id)
    FlashcardDeck.query.filter_by(content_id=record.id).update(
        {FlashcardDeck.content_id: None}, synchronize_session=False
    )
    db.session.delete(record)
    db.session.commit()
    return api_success({"id": content_id}, message="Learning material deleted.")


@learning_bp.post("/api/learning-content/<int:content_id>/ask-tutor")
@student_required
@rate_limit("ai")
def api_ask_tutor(content_id: int):
    record = get_owned_or_404(LearningContent, content_id)
    payload = request.get_json(silent=True) or {}
    question = clean_text(payload.get("question", ""), 500)
    if not question:
        from ..utils.validation import ValidationError
        raise ValidationError("Please ask a question about this topic.", "question")

    from ..services.ai_service import AIService
    from flask import current_app
    ai = AIService(current_app.config)

    subject_str = record.subject.subject_name if record.subject else "General"
    topic_str = record.topic.topic_name if record.topic else record.title
    summary_snippet = (record.generated_content or {}).get("summary", "")[:300]

    system_prompt = (
        f"You are LearnForge AI Tutor, a friendly, encouraging college professor assisting a {record.learning_level} student "
        f"studying '{topic_str}' in {subject_str}. Topic overview: {summary_snippet}. "
        "Answer the student's question clearly, accurately, and concisely (1-2 short paragraphs or bullet points). "
        "Always return ONLY a JSON object formatted as: "
        '{"answer": "markdown-formatted clear explanation", "suggested_followups": ["Short follow-up question 1?", "Short follow-up question 2?"]}'
    )
    user_prompt = f"Student question regarding '{topic_str}':\n\n{question}"

    answer = ""
    followups = [
        f"How does {topic_str} connect to real-world engineering?",
        f"What is the most common exam question on {topic_str}?",
    ]

    if ai.is_live_available():
        try:
            res = ai.generate_json(system_prompt, user_prompt, max_tokens=1200, temperature=0.6)
            if isinstance(res, dict):
                answer = str(res.get("answer") or "").strip()
                if isinstance(res.get("suggested_followups"), list):
                    followups = [str(f) for f in res["suggested_followups"][:3]]
        except Exception as exc:
            current_app.logger.warning("Ask tutor fallback: %s", exc)

    if not answer:
        answer = (
            f"**Regarding '{question}' in {topic_str}:**\n\n"
            f"In {record.learning_level} studies of {topic_str}, focus on how the core principles apply "
            f"to practical problem-solving. Review **Section 05 (Important Definitions)** and **Section 08 (Real-World Examples)** "
            f"in your notes above to see concrete applications."
        )

    return api_success({
        "question": question,
        "answer": answer,
        "suggested_followups": followups,
    })


@learning_bp.get("/api/download-pdf/<int:content_id>")
@student_required
def download_pdf(content_id: int):
    record = get_owned_or_404(LearningContent, content_id)
    pdf_buffer = build_content_pdf(record, current_user.name)
    subject_name = record.subject.subject_name if record.subject else "learning"
    filename = f"{slugify(record.topic.topic_name if record.topic else record.title)}_{slugify(record.learning_level)}_notes.pdf"
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@learning_bp.get("/api/download-markdown/<int:content_id>")
@student_required
def download_markdown(content_id: int):
    record = get_owned_or_404(LearningContent, content_id)
    markdown = build_content_markdown(record)
    filename = (
        f"{slugify(record.topic.topic_name if record.topic else record.title)}_"
        f"{slugify(record.learning_level)}_notes.md"
    )
    return send_file(
        BytesIO(markdown.encode("utf-8")),
        mimetype="text/markdown; charset=utf-8",
        as_attachment=True,
        download_name=filename,
    )
