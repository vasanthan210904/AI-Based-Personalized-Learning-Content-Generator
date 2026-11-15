import pytest
from app.extensions import db
from app.models import (
    FlashcardDeck,
    LearningContent,
    Quiz,
    StudyPlan,
    Subject,
    Topic,
    User,
)
from app.services.demo_bank import get_demo_quiz


def test_generic_quiz_fallback_for_uncurated_topic(app):
    """Verifies that demo quiz generation works for any topic name, never raising DemoUnavailable."""
    with app.app_context():
        # Any arbitrary topic name
        questions, note = get_demo_quiz("Quantum Computing", difficulty="Medium", count=5)
        assert questions is not None
        assert len(questions) == 5
        for q in questions:
            assert "question" in q
            assert len(q["options"]) == 4
            assert q["correct_index"] in [0, 1, 2, 3]
            assert q["explanation"]


def test_custom_topic_content_generation_with_flashcards(student_client, app):
    """Verifies custom topic input and auto flashcard deck generation via API."""
    with app.app_context():
        sub = Subject.query.first()
        assert sub is not None

        response = student_client.post(
            "/api/generate-content",
            json={
                "subject_id": sub.id,
                "custom_topic": "Quantum Teleportation",
                "content_type": "Detailed Notes",
                "learning_level": "Beginner",
                "explanation_style": "Practical Examples",
                "language": "English",
                "create_flashcards": True,
            },
        )
        assert response.status_code == 201, response.get_json()
        data = response.get_json()
        assert data["success"] is True
        content_id = data["data"]["id"]

        # Check content in DB
        content = db.session.get(LearningContent, content_id)
        assert content is not None
        assert "Quantum Teleportation" in content.title or "Quantum Teleportation" in content.body_markdown

        # Check Topic was dynamically created
        topic = Topic.query.filter_by(subject_id=sub.id, topic_name="Quantum Teleportation").first()
        assert topic is not None
        assert content.topic_id == topic.id

        # Check Flashcard Deck was created
        deck = FlashcardDeck.query.filter_by(content_id=content_id).first()
        assert deck is not None
        assert deck.total_cards > 0


def test_custom_topic_quiz_generation(student_client, app):
    """Verifies custom topic generates quiz without failure."""
    with app.app_context():
        sub = Subject.query.first()

        response = student_client.post(
            "/api/generate-quiz",
            json={
                "subject_id": sub.id,
                "custom_topic": "Autonomous Drone Navigation",
                "difficulty": "Medium",
                "num_questions": 5,
            },
        )
        assert response.status_code == 201, response.get_json()
        data = response.get_json()
        assert data["success"] is True
        quiz_id = data["data"]["id"]

        quiz = db.session.get(Quiz, quiz_id)
        assert quiz is not None
        assert len(quiz.questions) == 5

        # Check Topic was dynamically created
        topic = Topic.query.filter_by(subject_id=sub.id, topic_name="Autonomous Drone Navigation").first()
        assert topic is not None
        assert quiz.topic_id == topic.id


def test_custom_topic_study_plan_generation(student_client, app):
    """Verifies study plan can include custom typed topics."""
    with app.app_context():
        sub = Subject.query.first()
        from datetime import date, timedelta
        target = (date.today() + timedelta(days=14)).isoformat()

        response = student_client.post(
            "/api/generate-study-plan",
            json={
                "subject_id": sub.id,
                "custom_topics": ["Reinforcement Learning", "Transformer Attention"],
                "hours_per_day": 2.0,
                "target_date": target,
                "learning_level": "Intermediate",
            },
        )
        assert response.status_code == 201, response.get_json()
        data = response.get_json()
        assert data["success"] is True
        plan_id = data["data"]["id"]

        plan = db.session.get(StudyPlan, plan_id)
        assert plan is not None
        assert len(plan.days) > 0

        # Verify topics exist
        rl = Topic.query.filter_by(subject_id=sub.id, topic_name="Reinforcement Learning").first()
        ta = Topic.query.filter_by(subject_id=sub.id, topic_name="Transformer Attention").first()
        assert rl is not None
        assert ta is not None


def test_cheat_sheet_and_ask_tutor_api(student_client, app):
    """Verifies the new AI Revision Cheat Sheet and Ask Tutor endpoints."""
    with app.app_context():
        sub = Subject.query.first()
        topic = Topic.query.filter_by(subject_id=sub.id).first()
        student = User.query.filter_by(role="student").first()

        content = LearningContent(
            user_id=student.id,
            subject_id=sub.id,
            topic_id=topic.id,
            title="Introduction to Machine Learning",
            learning_level="Beginner",
            content_type="Detailed Explanation",
            language="English",
            explanation_style="Visual & Examples",
            generated_content={
                "introduction": "Machine learning enables systems to learn from data patterns.",
                "summary": "Core algorithms generalize from historical observations.",
                "important_definitions": [
                    {"term": "Supervised Learning", "definition": "Learning from input-output pairs."},
                    {"term": "Overfitting", "definition": "Fitting training noise instead of the general trend."}
                ],
                "basic_concepts": [
                    {"heading": "Loss Function", "explanation": "Quantifies the discrepancy between predictions and targets."}
                ],
                "practical_applications": [
                    "Email spam detection",
                    "Autonomous vehicles navigation"
                ]
            },
            ai_mode="demo"
        )
        db.session.add(content)
        db.session.commit()
        content_id = content.id

    # 1. Test Cheat Sheet endpoint
    cs_resp = student_client.get(f"/api/learning-content/{content_id}/cheat-sheet")
    assert cs_resp.status_code == 200
    cs_data = cs_resp.get_json()
    assert cs_data["success"] is True
    data = cs_data["data"]
    assert len(data["definitions"]) >= 2
    assert any("Supervised Learning" in d["term"] for d in data["definitions"])
    assert len(data["takeaways"]) >= 1
    assert len(data["common_pitfalls"]) >= 1
    assert len(data["mnemonics"]) >= 1

    # 2. Test Ask Tutor endpoint
    tutor_resp = student_client.post(
        f"/api/learning-content/{content_id}/ask-tutor",
        json={"question": "What is the key difference between classification and regression?"}
    )
    assert tutor_resp.status_code == 200
    tutor_data = tutor_resp.get_json()
    assert tutor_data["success"] is True
    assert tutor_data["data"]["answer"]
    assert len(tutor_data["data"]["suggested_followups"]) >= 1

