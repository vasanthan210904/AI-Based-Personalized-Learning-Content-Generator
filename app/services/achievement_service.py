"""Achievement definitions evaluated from real student activity."""
from __future__ import annotations


def _entry(key, label, description, icon, tone, current, target, earned=None) -> dict:
    current = round(current or 0, 1)
    target = max(1, target)
    progress = min(100, round(current / target * 100))
    if earned is None:
        earned = current >= target
    return {
        "key": key,
        "label": label,
        "description": description,
        "icon": icon,
        "tone": tone,
        "current": current,
        "target": target,
        "progress": 100 if earned else progress,
        "earned": bool(earned),
    }


def evaluate_achievements(summary: dict) -> dict:
    """Turn a learning summary into earned and in-progress achievements."""
    best = summary.get("best_score", 0) or 0
    coverage = summary.get("coverage", 0) or 0
    mastery = summary.get("mastery", 0) or 0
    rounded_progress = round(
        (min(coverage, 50) / 50) * 50 + (min(mastery, 70) / 70) * 50
    )

    achievements = [
        _entry(
            "first_material",
            "First material",
            "Generate your first personalized learning material.",
            "bi-journal-plus",
            "indigo",
            summary.get("materials", 0),
            1,
        ),
        _entry(
            "library_builder",
            "Library builder",
            "Save five learning materials to your history.",
            "bi-collection",
            "violet",
            summary.get("materials", 0),
            5,
        ),
        _entry(
            "first_quiz",
            "Quiz starter",
            "Complete your first quiz attempt.",
            "bi-patch-question",
            "teal",
            summary.get("quiz_attempts", 0),
            1,
        ),
        _entry(
            "high_scorer",
            "High scorer",
            "Score 85% or higher on any quiz.",
            "bi-award",
            "amber",
            best,
            85,
        ),
        _entry(
            "perfect_score",
            "Perfect score",
            "Answer every question correctly on a quiz.",
            "bi-trophy",
            "amber",
            best,
            100,
        ),
        _entry(
            "planner",
            "Plan ahead",
            "Create your first day-by-day study plan.",
            "bi-calendar2-week",
            "indigo",
            summary.get("plans_count", 0),
            1,
        ),
        _entry(
            "plan_finisher",
            "Plan finisher",
            "Complete every day in at least one study plan.",
            "bi-calendar-check",
            "teal",
            summary.get("plans_completed", 0),
            1,
        ),
        _entry(
            "streak_3",
            "On a roll",
            "Study for three days in a row.",
            "bi-fire",
            "amber",
            summary.get("streak", 0),
            3,
        ),
        _entry(
            "streak_7",
            "Consistency champion",
            "Keep a seven-day study streak.",
            "bi-lightning-charge",
            "violet",
            summary.get("streak", 0),
            7,
        ),
        _entry(
            "flashcard_first",
            "Flashcard fan",
            "Create your first flashcard deck.",
            "bi-card-heading",
            "indigo",
            summary.get("flashcard_decks", 0),
            1,
        ),
        _entry(
            "flashcard_master",
            "Recall master",
            "Mark 20 flashcards as known.",
            "bi-lightbulb",
            "teal",
            summary.get("flashcard_cards_known", 0),
            20,
        ),
        _entry(
            "well_rounded",
            "Well rounded",
            "Reach 50% topic coverage and 70% quiz mastery.",
            "bi-compass",
            "violet",
            rounded_progress,
            100,
            earned=bool(coverage >= 50 and mastery >= 70),
        ),
    ]
    earned = sum(1 for item in achievements if item["earned"])
    return {
        "items": achievements,
        "earned_count": earned,
        "total": len(achievements),
        "completion": round(earned / len(achievements) * 100),
    }
