"""JSON serializers. Quiz serializers never expose answer keys."""
from __future__ import annotations

from ..constants import AI_MODES


def _iso(value):
    return value.isoformat() if value else None


def user_dict(user, include_profile: bool = True) -> dict:
    data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "created_at": _iso(user.created_at),
        "last_login_at": _iso(user.last_login_at),
    }
    if include_profile:
        profile = user.profile
        data["profile"] = (
            {
                "course": profile.course,
                "department": profile.department,
                "year": profile.year,
                "learning_level": profile.learning_level,
                "learning_style": profile.learning_style,
                "preferred_language": profile.preferred_language,
                "learning_goals": profile.learning_goals,
                "interested_subjects": profile.subject_list,
                "profile_completeness": None,
            }
            if profile
            else None
        )
    return data


def content_summary(content) -> dict:
    return {
        "id": content.id,
        "title": content.title,
        "subject_id": content.subject_id,
        "subject": content.subject.subject_name if content.subject else "",
        "topic_id": content.topic_id,
        "topic": content.topic.topic_name if content.topic else "",
        "learning_level": content.learning_level,
        "content_type": content.content_type,
        "language": content.language,
        "explanation_style": content.explanation_style,
        "ai_mode": content.ai_mode,
        "mode_label": AI_MODES.get(content.ai_mode, AI_MODES["demo"])["label"],
        "ai_note": content.ai_note,
        "created_at": _iso(content.created_at),
        "view_url": f"/learning/content/{content.id}",
        "pdf_url": f"/api/download-pdf/{content.id}",
        "markdown_url": f"/api/download-markdown/{content.id}",
    }


def content_detail(content) -> dict:
    data = content_summary(content)
    data["generated_content"] = content.generated_content
    return data


def quiz_summary(quiz) -> dict:
    return {
        "id": quiz.id,
        "subject_id": quiz.subject_id,
        "subject": quiz.subject.subject_name if quiz.subject else "",
        "topic_id": quiz.topic_id,
        "topic": quiz.topic.topic_name if quiz.topic else "",
        "difficulty": quiz.difficulty,
        "num_questions": quiz.num_questions,
        "ai_mode": quiz.ai_mode,
        "mode_label": AI_MODES.get(quiz.ai_mode, AI_MODES["demo"])["label"],
        "ai_note": quiz.ai_note,
        "created_at": _iso(quiz.created_at),
        "take_url": f"/quiz/{quiz.id}/take",
    }


def quiz_public(quiz) -> dict:
    data = quiz_summary(quiz)
    data["questions"] = quiz.public_questions()
    return data


def attempt_dict(attempt) -> dict:
    quiz = attempt.quiz
    return {
        "id": attempt.id,
        "quiz_id": attempt.quiz_id,
        "subject": quiz.subject.subject_name if quiz and quiz.subject else "",
        "topic": quiz.topic.topic_name if quiz and quiz.topic else "",
        "difficulty": quiz.difficulty if quiz else "",
        "score": attempt.score,
        "total_questions": attempt.total_questions,
        "correct_count": attempt.correct_count,
        "wrong_count": attempt.wrong_count,
        "unanswered_count": attempt.unanswered_count,
        "percentage": attempt.percentage,
        "performance": attempt.performance["label"],
        "attempted_at": _iso(attempt.attempted_at),
        "results_url": f"/quiz/results/{attempt.id}",
    }


def study_plan_summary(plan) -> dict:
    return {
        "id": plan.id,
        "subject_id": plan.subject_id,
        "subject": plan.subject.subject_name if plan.subject else "",
        "learning_level": plan.learning_level,
        "hours_per_day": plan.hours_per_day,
        "target_date": plan.target_date.isoformat() if plan.target_date else None,
        "total_days": plan.total_days,
        "completed_days": plan.completed_days,
        "completion_percentage": plan.completion_percentage,
        "is_complete": plan.is_complete,
        "ai_mode": plan.ai_mode,
        "ai_note": plan.ai_note,
        "created_at": _iso(plan.created_at),
        "view_url": f"/study-plans/{plan.id}",
    }


def study_plan_detail(plan) -> dict:
    data = study_plan_summary(plan)
    data["overview"] = (plan.plan_data or {}).get("overview", "")
    data["days"] = [
        {**day, "completed": plan.is_day_completed(index)}
        for index, day in enumerate(plan.days)
    ]
    data["completed_day_indices"] = plan.completed_day_indices
    return data


def bookmark_dict(bookmark) -> dict:
    content = bookmark.content
    return {
        **content_summary(content),
        "bookmark": {
            "id": bookmark.id,
            "note": bookmark.note or "",
            "created_at": _iso(bookmark.created_at),
            "updated_at": _iso(bookmark.updated_at),
        },
    }


def flashcard_dict(card) -> dict:
    return {
        "id": card.id,
        "front": card.front,
        "back": card.back,
        "position": card.position,
        "status": card.status,
        "review_count": card.review_count,
        "last_reviewed_at": _iso(card.last_reviewed_at),
    }


def flashcard_deck_summary(deck) -> dict:
    return {
        "id": deck.id,
        "title": deck.title,
        "subject_id": deck.subject_id,
        "subject": deck.subject.subject_name if deck.subject else "",
        "topic_id": deck.topic_id,
        "topic": deck.topic.topic_name if deck.topic else "",
        "content_id": deck.content_id,
        "source": deck.source,
        "total_cards": deck.total_cards,
        "known_cards": deck.known_cards,
        "review_cards": deck.review_cards,
        "new_cards": deck.new_cards,
        "mastery_percentage": deck.mastery_percentage,
        "created_at": _iso(deck.created_at),
        "last_studied_at": _iso(deck.last_studied_at),
        "study_url": f"/flashcards/{deck.id}",
    }


def flashcard_deck_detail(deck) -> dict:
    data = flashcard_deck_summary(deck)
    data["cards"] = [flashcard_dict(card) for card in deck.cards]
    return data


def share_dict(share) -> dict:
    return {
        "id": share.id,
        "token": share.token,
        "url": f"/shared/{share.token}",
        "views": share.views,
        "created_at": _iso(share.created_at),
        "last_viewed_at": _iso(share.last_viewed_at),
    }
