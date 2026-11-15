"""Smoke tests for the main student and admin pages."""
from __future__ import annotations

import pytest

STUDENT_PAGES = [
    "/dashboard",
    "/generate",
    "/learning/history",
    "/library/saved",
    "/flashcards",
    "/progress",
    "/study-planner",
    "/quiz/generate",
    "/quiz/history",
    "/profile",
    "/preferences",
]

ADMIN_PAGES = [
    "/admin/",
    "/admin/users",
    "/admin/subjects",
    "/admin/topics",
]


@pytest.mark.parametrize("path", STUDENT_PAGES)
def test_student_pages_render(student_client, path):
    response = student_client.get(path)
    assert response.status_code == 200, response.get_data(as_text=True)
    body = response.get_data(as_text=True)
    assert "Traceback" not in body
    assert "Internal Server Error" not in body


@pytest.mark.parametrize("path", ADMIN_PAGES)
def test_admin_pages_render(admin_client, path):
    response = admin_client.get(path)
    assert response.status_code == 200, response.get_data(as_text=True)
    body = response.get_data(as_text=True)
    assert "Traceback" not in body
    assert "Internal Server Error" not in body


def test_student_cannot_open_admin_console(student_client):
    response = student_client.get("/admin/")
    assert response.status_code == 403


def test_admin_cannot_open_student_studio(admin_client):
    response = admin_client.get("/generate")
    assert response.status_code == 403
