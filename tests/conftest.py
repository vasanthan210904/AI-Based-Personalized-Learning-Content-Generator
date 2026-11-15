"""Shared pytest fixtures for the LearnForge test-suite."""
from __future__ import annotations

import pytest

from app import create_app
from app.extensions import db
from app.models import StudentProfile, Subject, Topic, User
from app.seed import seed_initial_data
from app.services.ai_service import reset_ai_cooldowns
from config import TestConfig

STUDENT_EMAIL = "test.student@learnforge.com"
STUDENT_PASSWORD = "Student@12345"


@pytest.fixture()
def app():
    """A fresh application with an in-memory database and seeded catalog."""
    application = create_app(TestConfig)
    # Tests must never reach a real AI provider by accident.
    application.config.update(
        AI_API_KEY="",
        AI_DEMO_MODE="auto",
        AI_FAILURE_COOLDOWN=120,
    )

    with application.app_context():
        db.create_all()
        seed_initial_data()

        student = User(name="Test Student", email=STUDENT_EMAIL, role="student")
        student.set_password(STUDENT_PASSWORD)
        student.profile = StudentProfile(
            course="B.Tech Computer Science",
            department="Computer Science & Engineering",
            year="2nd Year",
            learning_level="Intermediate",
            preferred_language="English",
            learning_style="Detailed Explanation",
            learning_goals="Prepare for semester exams.",
            interested_subjects="Artificial Intelligence",
        )
        db.session.add(student)
        db.session.commit()

    reset_ai_cooldowns()
    yield application

    reset_ai_cooldowns()
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def student_client(client):
    response = client.post(
        "/login",
        data={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 302, response.get_data(as_text=True)
    return client


@pytest.fixture()
def admin_client(client):
    response = client.post(
        "/login",
        data={
            "email": TestConfig.ADMIN_EMAIL,
            "password": TestConfig.ADMIN_PASSWORD,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302, response.get_data(as_text=True)
    return client


@pytest.fixture()
def catalog(app):
    """Return ids for a seeded topic that has curated demo content."""
    with app.app_context():
        subject = Subject.query.filter_by(subject_name="Artificial Intelligence").first()
        assert subject is not None
        topic = Topic.query.filter_by(
            subject_id=subject.id, topic_name="Machine Learning Basics"
        ).first()
        assert topic is not None
        return {"subject_id": subject.id, "topic_id": topic.id}
