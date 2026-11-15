"""Quiz generation, taking, evaluation and history."""
from __future__ import annotations

from flask import Blueprint, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import desc

from ..constants import QUIZ_DIFFICULTIES
from ..decorators import student_required
from ..models import Quiz, QuizAttempt, Topic
from ..services.demo_bank import DEMO_TOPICS
from ..services.quiz_generator import build_review, evaluate_quiz, generate_quiz
from ..utils.catalog import subjects_with_topics
from ..utils.pagination import paginate
from ..utils.rate_limit import rate_limit
from ..utils.responses import api_success
from ..utils.security import get_owned_or_404
from ..utils.serializers import attempt_dict, quiz_public, quiz_summary
from ..utils.validation import parse_int, slugify

quiz_bp = Blueprint("quiz", __name__)


@quiz_bp.get("/quiz/generate")
@student_required
def generate_page():
    profile = current_user.profile
    recent = (
        Quiz.query.filter_by(user_id=current_user.id)
        .order_by(desc(Quiz.created_at))
        .limit(4)
        .all()
    )
    requested_difficulty = request.args.get("difficulty")
    defaults = {
        "subject_id": request.args.get("subject", type=int),
        "topic_id": request.args.get("topic", type=int),
        "difficulty": requested_difficulty
        if requested_difficulty in QUIZ_DIFFICULTIES
        else "Medium",
        "num_questions": 5,
        "level": profile.learning_level if profile else "Beginner",
    }
    return render_template(
        "quiz/generator.html",
        subjects_data=subjects_with_topics(),
        demo_topics=DEMO_TOPICS,
        defaults=defaults,
        recent=recent,
    )


@quiz_bp.get("/quiz/<int:quiz_id>/take")
@student_required
def take(quiz_id: int):
    quiz = get_owned_or_404(Quiz, quiz_id)
    questions = quiz.public_questions()
    if not questions:
        return render_template(
            "errors/error.html",
            code=422,
            title="Quiz unavailable",
            message="This quiz does not contain any questions.",
        ), 422
    return render_template(
        "quiz/take.html",
        quiz=quiz,
        questions=questions,
        previous_attempts=len(quiz.attempts),
    )


@quiz_bp.get("/quiz/results/<int:attempt_id>")
@student_required
def results(attempt_id: int):
    attempt = get_owned_or_404(QuizAttempt, attempt_id)
    quiz = attempt.quiz
    review = build_review(attempt)
    recommended = []
    if quiz and quiz.topic:
        recommended = (
            Topic.query.filter(
                Topic.subject_id == quiz.subject_id, Topic.id != quiz.topic_id
            )
            .order_by(Topic.topic_name)
            .limit(3)
            .all()
        )
    profile = current_user.profile
    next_level = (
        "Beginner"
        if attempt.percentage < 50
        else (profile.learning_level if profile else "Beginner")
    )
    return render_template(
        "quiz/results.html",
        attempt=attempt,
        quiz=quiz,
        review=review,
        recommended=recommended,
        performance=attempt.performance,
        next_level=next_level or "Beginner",
    )


@quiz_bp.get("/quiz/history")
@student_required
def history():
    page = request.args.get("page", 1, type=int)
    query = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(
        desc(QuizAttempt.attempted_at)
    )
    pagination = paginate(query, page=page, per_page=10)
    attempts = QuizAttempt.query.filter_by(user_id=current_user.id).all()
    stats = {
        "total": len(attempts),
        "average": round(sum(a.percentage for a in attempts) / len(attempts), 1)
        if attempts
        else 0,
        "best": max((a.percentage for a in attempts), default=0),
        "correct": sum(a.correct_count for a in attempts),
    }
    return render_template(
        "quiz/history.html", pagination=pagination, stats=stats
    )


# ----------------------------------------------------------------------
# JSON API
# ----------------------------------------------------------------------
@quiz_bp.post("/api/generate-quiz")
@student_required
@rate_limit(
    "generate-quiz",
    message="You have generated several quizzes recently. Please wait a few minutes.",
)
def api_generate_quiz():
    payload = request.get_json(silent=True) or {}
    quiz = generate_quiz(current_user, payload)
    return api_success(
        {
            **quiz_public(quiz),
            "redirect_url": url_for("quiz.take", quiz_id=quiz.id),
        },
        message="Quiz generated successfully.",
        status=201,
    )


@quiz_bp.post("/api/submit-quiz")
@student_required
def api_submit_quiz():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        from ..utils.validation import ValidationError

        raise ValidationError("Send a JSON object with quiz_id and answers.")
    quiz_id = parse_int(payload.get("quiz_id"), "quiz_id", label="Quiz")
    quiz = get_owned_or_404(Quiz, quiz_id)
    attempt = evaluate_quiz(quiz, current_user, payload.get("answers"))
    return api_success(
        {
            "attempt": attempt_dict(attempt),
            "review": build_review(attempt),
            "feedback": attempt.performance["message"],
            "results_url": url_for("quiz.results", attempt_id=attempt.id),
        },
        message="Quiz evaluated successfully.",
    )


@quiz_bp.get("/api/quiz-history")
@student_required
def api_quiz_history():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    query = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(
        desc(QuizAttempt.attempted_at)
    )
    pagination = paginate(query, page=page, per_page=min(per_page, 50))
    attempts = QuizAttempt.query.filter_by(user_id=current_user.id).all()
    return api_success(
        {
            "items": [attempt_dict(item) for item in pagination["items"]],
            "pagination": {
                key: pagination[key]
                for key in ("total", "page", "pages", "per_page", "has_prev", "has_next")
            },
            "stats": {
                "total_attempts": len(attempts),
                "average_percentage": round(
                    sum(a.percentage for a in attempts) / len(attempts), 1
                )
                if attempts
                else 0,
                "best_percentage": max((a.percentage for a in attempts), default=0),
            },
        }
    )
