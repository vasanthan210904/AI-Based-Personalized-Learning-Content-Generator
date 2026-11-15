"""Generator validation and end-to-end content generation tests."""
from __future__ import annotations

from pathlib import Path

from app.extensions import db
from app.models import LearningContent


def _payload(catalog, **overrides):
    payload = {
        "subject_id": catalog["subject_id"],
        "topic_id": catalog["topic_id"],
        "content_type": "Short Notes",
        "learning_level": "Intermediate",
        "explanation_style": "Detailed Explanation",
        "language": "English",
    }
    payload.update(overrides)
    return payload


def test_generator_page_renders_form_and_catalog(student_client):
    response = student_client.get("/generate")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert 'id="generatorForm"' in body
    assert 'id="subjectsData"' in body
    for field in ("subject_id", "topic_id", "content_type"):
        assert f'data-client-error="{field}"' in body
    # Eight selectable content-type cards are rendered server-side.
    assert body.count('name="content_type"') == 8


def test_generator_script_has_no_generic_dead_end_message(app):
    script = Path(app.root_path, "static", "js", "generator.js").read_text(encoding="utf-8")

    assert "Choose a subject, topic and content type." not in script
    # The first topic is selected automatically so a valid subject is never a dead end.
    assert "autoSelectFirst" in script
    assert "data-client-error" in script


def test_missing_subject_returns_field_error(student_client):
    response = student_client.post("/api/generate-content", json={})
    assert response.status_code == 422
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "validation_error"
    assert "subject_id" in payload["error"]["fields"]


def test_missing_topic_returns_topic_field_error(student_client, catalog):
    response = student_client.post(
        "/api/generate-content",
        json={"subject_id": catalog["subject_id"]},
    )
    assert response.status_code == 422
    payload = response.get_json()
    assert "topic_id" in payload["error"]["fields"]


def test_invalid_content_type_returns_field_error(student_client, catalog):
    response = student_client.post(
        "/api/generate-content",
        json=_payload(catalog, content_type="Not a real format"),
    )
    assert response.status_code == 422
    payload = response.get_json()
    assert "content_type" in payload["error"]["fields"]


def test_demo_generation_saves_content_and_opens_viewer(student_client, app, catalog):
    response = student_client.post("/api/generate-content", json=_payload(catalog))
    assert response.status_code == 201, response.get_data(as_text=True)

    payload = response.get_json()
    assert payload["success"] is True
    record = payload["data"]
    assert record["ai_mode"] == "demo"
    assert record["subject_id"] == catalog["subject_id"]
    assert record["topic_id"] == catalog["topic_id"]
    assert record["generated_content"]["introduction"]
    assert record["generated_content"]["summary"]

    with app.app_context():
        saved = db.session.get(LearningContent, record["id"])
        assert saved is not None
        assert saved.generated_content["introduction"]

    viewer = student_client.get(record["view_url"])
    assert viewer.status_code == 200
    assert "Demo mode" in viewer.get_data(as_text=True)

    pdf = student_client.get(record["pdf_url"])
    assert pdf.status_code == 200
    assert pdf.mimetype == "application/pdf"

    markdown = student_client.get(record["markdown_url"])
    assert markdown.status_code == 200
    assert "Machine Learning Basics" in markdown.get_data(as_text=True)


def test_generation_requires_a_student_login(client, catalog):
    response = client.post("/api/generate-content", json=_payload(catalog))
    assert response.status_code in {302, 401}
