"""Real, database-derived learning analytics and recommendations.

No statistic in this module is invented: every number is computed from the
student's stored learning materials, quiz attempts and study plans.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta

from ..models import (
    FlashcardDeck,
    LearningContent,
    QuizAttempt,
    StudyPlan,
    Subject,
    Topic,
)
from .achievement_service import evaluate_achievements


def _load(user):
    contents = (
        LearningContent.query.filter_by(user_id=user.id)
        .order_by(LearningContent.created_at.asc())
        .all()
    )
    attempts = (
        QuizAttempt.query.filter_by(user_id=user.id)
        .order_by(QuizAttempt.attempted_at.asc())
        .all()
    )
    plans = (
        StudyPlan.query.filter_by(user_id=user.id)
        .order_by(StudyPlan.created_at.asc())
        .all()
    )
    return contents, attempts, plans


def _scope_topics(profile) -> list[Topic]:
    names = profile.subject_list if profile else []
    query = Topic.query.join(Subject)
    if names:
        scoped = query.filter(Subject.subject_name.in_(names)).all()
        if scoped:
            return scoped
    return query.all()


def _profile_completeness(profile) -> int:
    if not profile:
        return 0
    fields = [
        profile.course,
        profile.department,
        profile.year,
        profile.learning_goals,
        profile.subject_list,
    ]
    filled = sum(1 for field in fields if field)
    return round(filled / len(fields) * 100)


def _streak(activity_dates: set[date]) -> int:
    if not activity_dates:
        return 0
    today = date.today()
    cursor = today if today in activity_dates else today - timedelta(days=1)
    streak = 0
    while cursor in activity_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _topic_performance(attempts: list[QuizAttempt]) -> list[dict]:
    grouped: dict[int, dict] = {}
    for attempt in attempts:
        quiz = attempt.quiz
        if not quiz or not quiz.topic:
            continue
        topic = quiz.topic
        entry = grouped.setdefault(
            topic.id,
            {
                "topic_id": topic.id,
                "topic_name": topic.topic_name,
                "subject_id": quiz.subject_id,
                "subject_name": quiz.subject.subject_name if quiz.subject else "",
                "attempts": 0,
                "total": 0.0,
                "best": 0.0,
                "last": attempt.attempted_at,
            },
        )
        entry["attempts"] += 1
        entry["total"] += attempt.percentage
        entry["best"] = max(entry["best"], attempt.percentage)
        entry["last"] = max(entry["last"], attempt.attempted_at)

    result = []
    for entry in grouped.values():
        entry["average"] = round(entry["total"] / entry["attempts"], 1)
        entry["last_label"] = entry["last"].strftime("%d %b %Y")
        entry.pop("total", None)
        result.append(entry)
    return sorted(result, key=lambda item: (item["average"], -item["attempts"]))


def _recommendations(user, contents, attempts, plans, studied_ids: set[int]) -> list[dict]:
    performance = _topic_performance(attempts)
    recommendations: list[dict] = []
    seen: set[int] = set()

    for item in performance:
        if item["average"] < 70 and item["topic_id"] not in seen:
            recommendations.append(
                {
                    "topic_id": item["topic_id"],
                    "topic_name": item["topic_name"],
                    "subject_id": item["subject_id"],
                    "subject_name": item["subject_name"],
                    "reason": f"Your quiz average is {item['average']:g}% - revisit this topic.",
                    "kind": "weak",
                    "badge": "Needs review",
                }
            )
            seen.add(item["topic_id"])
        if len(recommendations) >= 2:
            break

    incomplete_plans = [plan for plan in plans if plan.total_days and not plan.is_complete]
    if incomplete_plans:
        plan = sorted(incomplete_plans, key=lambda p: p.created_at, reverse=True)[0]
        completed = set(plan.completed_day_indices)
        for index, day in enumerate(plan.days):
            if index in completed:
                continue
            topic_id = day.get("topic_id")
            if topic_id and topic_id not in seen and plan.subject:
                recommendations.append(
                    {
                        "topic_id": topic_id,
                        "topic_name": day.get("topic", ""),
                        "subject_id": plan.subject_id,
                        "subject_name": plan.subject.subject_name,
                        "reason": f"Next up in your study plan (day {index + 1}).",
                        "kind": "plan",
                        "badge": "In your plan",
                    }
                )
                seen.add(topic_id)
            break

    available = _scope_topics(user.profile)
    for topic in sorted(available, key=lambda t: (t.subject.subject_name, t.topic_name)):
        if len(recommendations) >= 4:
            break
        if topic.id in studied_ids or topic.id in seen:
            continue
        recommendations.append(
            {
                "topic_id": topic.id,
                "topic_name": topic.topic_name,
                "subject_id": topic.subject_id,
                "subject_name": topic.subject.subject_name,
                "reason": "Not started yet - generate your first notes for this topic.",
                "kind": "new",
                "badge": "Explore",
            }
        )
        seen.add(topic.id)

    return recommendations[:4]


def learning_summary(user) -> dict:
    contents, attempts, plans = _load(user)
    profile = user.profile
    studied_ids = {c.topic_id for c in contents}
    studied_ids.update(a.quiz.topic_id for a in attempts if a.quiz)

    available = _scope_topics(profile)
    available_ids = {t.id for t in available}
    studied_in_scope = studied_ids & available_ids
    coverage = (
        round(len(studied_in_scope) / len(available_ids) * 100) if available_ids else 0
    )
    mastery = (
        round(sum(a.percentage for a in attempts) / len(attempts), 1) if attempts else 0.0
    )
    best_score = max((a.percentage for a in attempts), default=0)
    decks = (
        FlashcardDeck.query.filter_by(user_id=user.id)
        .order_by(FlashcardDeck.created_at.asc())
        .all()
    )
    has_activity = bool(contents or attempts)
    learning_progress = round((coverage + mastery) / 2) if has_activity else 0

    completed_topics: set[str] = set()
    for plan in plans:
        completed = set(plan.completed_day_indices)
        for index, day in enumerate(plan.days):
            if index in completed:
                completed_topics.add(day.get("topic", ""))

    total_plan_days = sum(plan.total_days for plan in plans)
    completed_plan_days = sum(plan.completed_days for plan in plans)
    plan_completion = (
        round(completed_plan_days / total_plan_days * 100) if total_plan_days else 0
    )

    activity_dates = {c.created_at.date() for c in contents}
    activity_dates.update(a.attempted_at.date() for a in attempts)
    activity_dates.update(deck.created_at.date() for deck in decks)
    activity_dates.update(
        deck.last_studied_at.date() for deck in decks if deck.last_studied_at
    )

    plans_completed = sum(1 for plan in plans if plan.is_complete)
    flashcard_cards_known = sum(deck.known_cards for deck in decks)

    active_plan = None
    next_plan_day = None
    for plan in sorted(plans, key=lambda p: p.created_at, reverse=True):
        if plan.total_days and not plan.is_complete:
            active_plan = plan
            completed = set(plan.completed_day_indices)
            for index, day in enumerate(plan.days):
                if index not in completed:
                    next_plan_day = {**day, "index": index}
                    break
            break

    summary = {
        "materials": len(contents),
        "quiz_attempts": len(attempts),
        "quizzes_taken": len({a.quiz_id for a in attempts}),
        "avg_score": mastery,
        "best_score": best_score,
        "coverage": coverage,
        "mastery": round(mastery),
        "learning_progress": learning_progress,
        "topics_studied": len(studied_in_scope),
        "total_topics_available": len(available_ids),
        "completed_topics": len(completed_topics),
        "plan_total_days": total_plan_days,
        "plan_completed_days": completed_plan_days,
        "plan_completion": plan_completion,
        "plans_count": len(plans),
        "plans_completed": plans_completed,
        "streak": _streak(activity_dates),
        "flashcard_decks": len(decks),
        "flashcard_cards_total": sum(deck.total_cards for deck in decks),
        "flashcard_cards_known": flashcard_cards_known,
        "has_activity": has_activity,
        "profile_completeness": _profile_completeness(profile),
        "recent_contents": list(reversed(contents[-4:])),
        "recent_attempts": list(reversed(attempts[-4:])),
        "recent_decks": list(reversed(decks[-3:])),
        "recommendations": _recommendations(user, contents, attempts, plans, studied_ids),
        "active_plan": active_plan,
        "next_plan_day": next_plan_day,
    }
    summary["achievements"] = evaluate_achievements(summary)
    return summary


def progress_data(user) -> dict:
    contents, attempts, plans = _load(user)
    summary = learning_summary(user)

    counts: Counter = Counter()
    for content in contents:
        counts[content.created_at.date()] += 1
    for attempt in attempts:
        counts[attempt.attempted_at.date()] += 1
    today = date.today()
    activity = []
    for offset in range(13, -1, -1):
        day = today - timedelta(days=offset)
        activity.append(
            {
                "date": day.isoformat(),
                "label": day.strftime("%d %b"),
                "count": counts.get(day, 0),
            }
        )

    score_trend = [
        {
            "label": attempt.attempted_at.strftime("%d %b"),
            "percentage": attempt.percentage,
            "topic": attempt.quiz.topic.topic_name if attempt.quiz and attempt.quiz.topic else "",
        }
        for attempt in attempts[-10:]
    ]

    subject_counts: Counter = Counter()
    for content in contents:
        if content.subject:
            subject_counts[content.subject.subject_name] += 1
    subject_distribution = [
        {"subject": name, "materials": count}
        for name, count in subject_counts.most_common()
    ]

    accuracy = {
        "correct": sum(a.correct_count for a in attempts),
        "wrong": sum(a.wrong_count for a in attempts),
        "unanswered": sum(a.unanswered_count for a in attempts),
    }

    plan_summaries = [
        {
            "id": plan.id,
            "subject": plan.subject.subject_name if plan.subject else "",
            "created": plan.created_at.strftime("%d %b %Y"),
            "total_days": plan.total_days,
            "completed_days": plan.completed_days,
            "percentage": plan.completion_percentage,
            "complete": plan.is_complete,
        }
        for plan in sorted(plans, key=lambda p: p.created_at, reverse=True)
    ]

    return {
        "summary": summary,
        "activity": activity,
        "score_trend": score_trend,
        "subject_distribution": subject_distribution,
        "topic_performance": _topic_performance(attempts),
        "accuracy": accuracy,
        "recommendations": summary["recommendations"],
        "plans": plan_summaries,
    }


def recent_study_activity(user, limit: int = 6) -> list[dict]:
    """A merged recent-activity feed for the student dashboard."""
    contents, attempts, _ = _load(user)
    events = []
    for content in contents[-limit:]:
        events.append(
            {
                "type": "content",
                "label": f"Generated {content.content_type}",
                "subject": content.subject.subject_name if content.subject else "",
                "topic": content.topic.topic_name if content.topic else content.title,
                "at": content.created_at,
                "url": f"/learning/content/{content.id}",
            }
        )
    for attempt in attempts[-limit:]:
        quiz = attempt.quiz
        events.append(
            {
                "type": "quiz",
                "label": f"Scored {attempt.percentage:g}% on a quiz",
                "subject": quiz.subject.subject_name if quiz and quiz.subject else "",
                "topic": quiz.topic.topic_name if quiz and quiz.topic else "",
                "at": attempt.attempted_at,
                "url": f"/quiz/results/{attempt.id}",
            }
        )
    decks = (
        FlashcardDeck.query.filter_by(user_id=user.id)
        .order_by(FlashcardDeck.created_at.desc())
        .limit(limit)
        .all()
    )
    for deck in decks:
        events.append(
            {
                "type": "flashcards",
                "label": f"Studied {deck.total_cards} flashcards"
                if deck.last_studied_at
                else "Created a flashcard deck",
                "subject": deck.subject.subject_name if deck.subject else "",
                "topic": deck.topic.topic_name if deck.topic else deck.title,
                "at": deck.last_studied_at or deck.created_at,
                "url": f"/flashcards/{deck.id}",
            }
        )
    events.sort(key=lambda item: item["at"], reverse=True)
    return events[:limit]
