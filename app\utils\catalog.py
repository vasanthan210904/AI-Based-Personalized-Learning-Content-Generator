"""Catalog helpers shared by generator pages."""
from __future__ import annotations

from ..models import Subject


def subjects_with_topics() -> list[dict]:
    subjects = Subject.query.order_by(Subject.subject_name).all()
    return [
        {
            "id": subject.id,
            "name": subject.subject_name,
            "description": subject.description or "",
            "topics": [
                {"id": topic.id, "name": topic.topic_name}
                for topic in sorted(subject.topics, key=lambda t: t.topic_name)
            ],
        }
        for subject in subjects
    ]
