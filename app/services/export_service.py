"""Plain-text exports: Markdown study notes and an iCalendar study plan."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from ..constants import AI_MODES


def _bullets(items) -> list[str]:
    return [f"- {item}" for item in items or [] if str(item).strip()]


def _numbered(items) -> list[str]:
    return [f"{index}. {item}" for index, item in enumerate(items or [], start=1) if str(item).strip()]


def build_content_markdown(content) -> str:
    """Render a generated material as portable Markdown."""
    data = content.generated_content or {}
    lines: list[str] = [
        f"# {data.get('title') or content.title}",
        "",
        f"> **Subject:** {content.subject.subject_name if content.subject else '-'}  ",
        f"> **Topic:** {content.topic.topic_name if content.topic else '-'}  ",
        f"> **Level:** {content.learning_level}  ",
        f"> **Format:** {content.content_type}  ",
        f"> **Language:** {content.language}  ",
        f"> **Generated:** {content.created_at.strftime('%d %B %Y, %H:%M')}  ",
        f"> **Mode:** {AI_MODES.get(content.ai_mode, AI_MODES['demo'])['label']}",
        "",
    ]

    if content.ai_mode != "live":
        lines += [
            f"> [!NOTE]",
            f"> {content.ai_note or AI_MODES.get(content.ai_mode, AI_MODES['demo'])['description']}",
            "",
        ]

    if data.get("introduction"):
        lines += ["## Introduction", "", str(data["introduction"]).strip(), ""]

    if data.get("learning_objectives"):
        lines += ["## Learning Objectives", ""] + _bullets(data["learning_objectives"]) + [""]

    if data.get("basic_concepts"):
        lines += ["## Basic Concepts", ""]
        for concept in data["basic_concepts"]:
            lines += [f"### {concept.get('heading', 'Concept')}", "", str(concept.get("explanation", "")).strip(), ""]

    if data.get("detailed_explanation"):
        lines += ["## Detailed Explanation", ""]
        for paragraph in str(data["detailed_explanation"]).split("\n\n"):
            if paragraph.strip():
                lines += [paragraph.strip(), ""]

    if data.get("important_definitions"):
        lines += ["## Important Definitions", ""]
        for item in data["important_definitions"]:
            lines += [f"**{item.get('term', 'Term')}** - {item.get('definition', '')}", ""]

    if data.get("key_terms"):
        lines += ["## Key Terms", "", ", ".join(data["key_terms"]), ""]

    if data.get("step_by_step"):
        lines += ["## Step-by-Step", ""] + _numbered(data["step_by_step"]) + [""]

    if data.get("real_world_examples"):
        lines += ["## Real-World Examples", ""]
        for example in data["real_world_examples"]:
            lines += ["```text", str(example).strip(), "```", ""]

    if data.get("practical_applications"):
        lines += ["## Practical Applications", ""] + _bullets(data["practical_applications"]) + [""]

    if data.get("advantages") or data.get("disadvantages"):
        lines += ["## Advantages & Disadvantages", ""]
        if data.get("advantages"):
            lines += ["### Advantages", ""] + _bullets(data["advantages"]) + [""]
        if data.get("disadvantages"):
            lines += ["### Disadvantages", ""] + _bullets(data["disadvantages"]) + [""]

    if data.get("important_points"):
        lines += ["## Important Points", ""] + _bullets(data["important_points"]) + [""]

    if data.get("summary"):
        lines += ["## Summary", "", str(data["summary"]).strip(), ""]

    if data.get("revision_tips"):
        lines += ["## Revision Tips", ""] + _bullets(data["revision_tips"]) + [""]

    if data.get("faqs"):
        lines += ["## Frequently Asked Questions", ""]
        for faq in data["faqs"]:
            lines += [
                f"### Q: {faq.get('question', '')}",
                "",
                str(faq.get("answer", "")).strip(),
                "",
            ]

    lines += [
        "---",
        "",
        f"Exported from LearnForge on {datetime.now(timezone.utc).strftime('%d %B %Y, %H:%M UTC')}.",
        "",
    ]
    return "\n".join(lines)


def _ics_escape(value) -> str:
    text = str(value or "").replace("\\", "\\\\")
    text = text.replace(";", "\\;").replace(",", "\\,")
    text = text.replace("\r\n", "\n").replace("\n", "\\n")
    return text


def _ics_date(value: date) -> str:
    return value.strftime("%Y%m%d")


def build_plan_ics(plan) -> bytes:
    """Render a study plan as an RFC 5545 all-day event calendar."""
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    subject = plan.subject.subject_name if plan.subject else "Study"
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//LearnForge AI//Study Planner//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_ics_escape(f'{subject} study plan')}",
        f"X-WR-CALDESC:{_ics_escape('Day-by-day study schedule from LearnForge AI.')}",
    ]

    for index, day in enumerate(plan.days):
        try:
            day_date = date.fromisoformat(str(day.get("date")))
        except (TypeError, ValueError):
            continue
        summary = f"LearnForge · Day {day.get('day', index + 1)}: {day.get('topic', subject)}"
        objectives = day.get("objectives") or []
        description = "\n".join(
            [
                f"Study: {day.get('duration_minutes', 0)} min",
                f"Revision: {day.get('revision_minutes', 0)} min",
                "Objectives:",
                *[f"- {item}" for item in objectives],
                "",
                f"Open plan: /study-plans/{plan.id}",
            ]
        )
        lines += [
            "BEGIN:VEVENT",
            f"UID:learnforge-plan-{plan.id}-day-{index + 1}@learnforge.local",
            f"DTSTAMP:{now}",
            f"DTSTART;VALUE=DATE:{_ics_date(day_date)}",
            f"DTEND;VALUE=DATE:{_ics_date(day_date + timedelta(days=1))}",
            f"SUMMARY:{_ics_escape(summary)}",
            f"DESCRIPTION:{_ics_escape(description)}",
            "CATEGORIES:Education,Study",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]

    lines += ["END:VCALENDAR", ""]
    return "\r\n".join(lines).encode("utf-8")
