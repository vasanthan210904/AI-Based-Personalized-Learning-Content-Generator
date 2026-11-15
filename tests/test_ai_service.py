"""AI provider availability, timeout and circuit-breaker tests."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
import requests

from app.services import ai_service as ai_module
from app.services.ai_service import AIService, AIServiceError, reset_ai_cooldowns


def _configure_live(app):
    app.config.update(
        AI_PROVIDER="nvidia",
        AI_MODEL="deepseek-ai/deepseek-v4.1-flash",
        AI_API_KEY="test-key",
        AI_DEMO_MODE="auto",
        AI_FAILURE_COOLDOWN=120,
        AI_TIMEOUT=1,
    )


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


def test_status_reports_live_provider(app):
    _configure_live(app)
    status = AIService(app.config).status()

    assert status["live"] is True
    assert status["state"] == "live"
    assert status["degraded"] is False
    assert status["cooldown_remaining"] == 0
    assert status["provider_label"] == "NVIDIA NIM"
    assert status["model"] == "deepseek-ai/deepseek-v4.1-flash"


def test_timeout_opens_circuit_and_skips_second_call(app, monkeypatch):
    _configure_live(app)
    reset_ai_cooldowns()
    calls = []

    def fake_post(*args, **kwargs):
        calls.append(kwargs)
        raise requests.Timeout("simulated provider timeout")

    monkeypatch.setattr(ai_module.requests, "post", fake_post)
    service = AIService(app.config)

    with pytest.raises(AIServiceError) as first:
        service.generate_json("system", "user", max_tokens=32)
    assert first.value.code == "ai_timeout"
    assert len(calls) == 1

    status = service.status()
    assert status["state"] == "fallback"
    assert status["degraded"] is True
    assert status["cooldown_remaining"] > 0
    assert "demo fallback" in status["label"].lower()

    # The breaker must fail fast: no second HTTP request during the cooldown.
    with pytest.raises(AIServiceError) as second:
        service.generate_json("system", "user", max_tokens=32)
    assert second.value.code == "ai_cooldown"
    assert len(calls) == 1


def test_provider_server_error_opens_circuit(app, monkeypatch):
    _configure_live(app)
    reset_ai_cooldowns()

    monkeypatch.setattr(
        ai_module.requests,
        "post",
        lambda *args, **kwargs: SimpleNamespace(status_code=503, ok=False, text="upstream"),
    )

    service = AIService(app.config)
    with pytest.raises(AIServiceError) as excinfo:
        service.generate_json("system", "user", max_tokens=32)

    assert excinfo.value.code == "ai_unavailable"
    assert service.cooldown_remaining() > 0


def test_failed_live_call_falls_back_to_labelled_demo(
    student_client, app, catalog, monkeypatch
):
    _configure_live(app)
    reset_ai_cooldowns()
    calls = []

    def fake_post(*args, **kwargs):
        calls.append(kwargs)
        raise requests.Timeout("simulated provider timeout")

    monkeypatch.setattr(ai_module.requests, "post", fake_post)

    first = student_client.post("/api/generate-content", json=_payload(catalog))
    assert first.status_code == 201, first.get_data(as_text=True)
    first_data = first.get_json()["data"]
    assert first_data["ai_mode"] == "demo_fallback"
    assert "Live AI was unavailable" in (first_data["ai_note"] or "")
    assert calls and len(calls) == 1

    # A second generation during the cooldown still succeeds with demo content
    # and never waits on the provider again.
    second = student_client.post("/api/generate-content", json=_payload(catalog))
    assert second.status_code == 201, second.get_data(as_text=True)
    assert second.get_json()["data"]["ai_mode"] == "demo_fallback"
    assert len(calls) == 1

    page = student_client.get("/generate")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert "Live AI temporarily unavailable" in body
    assert "Demo fallback" in body
