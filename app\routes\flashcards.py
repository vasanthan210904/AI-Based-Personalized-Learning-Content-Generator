"""Flashcard pages and API."""
from __future__ import annotations

from flask import Blueprint, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import desc

from ..decorators import student_required
from ..extensions import db
from ..models import FlashcardDeck, LearningContent
from ..services.flashcard_service import generate_deck, reset_deck, review_card
from ..utils.catalog import subjects_with_topics
from ..utils.rate_limit import rate_limit
from ..utils.responses import api_success
from ..utils.security import get_owned_or_404
from ..utils.serializers import (
    flashcard_deck_detail,
    flashcard_deck_summary,
)
from ..utils.validation import ValidationError

flashcards_bp = Blueprint("flashcards", __name__)


@flashcards_bp.get("/flashcards")
@student_required
def index():
    decks = (
        FlashcardDeck.query.filter_by(user_id=current_user.id)
        .order_by(desc(FlashcardDeck.created_at))
        .all()
    )
    materials = (
        LearningContent.query.filter_by(user_id=current_user.id)
        .order_by(desc(LearningContent.created_at))
        .limit(12)
        .all()
    )
    return render_template(
        "flashcards/index.html",
        decks=decks,
        materials=materials,
        subjects_data=subjects_with_topics(),
        totals={
            "decks": len(decks),
            "cards": sum(deck.total_cards for deck in decks),
            "known": sum(deck.known_cards for deck in decks),
        },
    )


@flashcards_bp.get("/flashcards/<int:deck_id>")
@student_required
def study(deck_id: int):
    deck = get_owned_or_404(FlashcardDeck, deck_id)
    return render_template(
        "flashcards/study.html",
        deck=deck,
        deck_data=flashcard_deck_detail(deck),
    )


# ----------------------------------------------------------------------
# JSON API
# ----------------------------------------------------------------------
@flashcards_bp.post("/api/flashcards/generate")
@student_required
@rate_limit(
    "generate-flashcards",
    message="Several flashcard decks were requested recently. Please wait a minute and try again.",
)
def api_generate_deck():
    payload = request.get_json(silent=True) or {}
    deck, created = generate_deck(current_user, payload)
    return api_success(
        {
            **flashcard_deck_summary(deck),
            "redirect_url": url_for("flashcards.study", deck_id=deck.id),
        },
        message="Flashcard deck created." if created else "Using the existing deck for this material.",
        status=201 if created else 200,
    )


@flashcards_bp.get("/api/flashcards")
@student_required
def api_list_decks():
    decks = (
        FlashcardDeck.query.filter_by(user_id=current_user.id)
        .order_by(desc(FlashcardDeck.created_at))
        .all()
    )
    return api_success({"items": [flashcard_deck_summary(deck) for deck in decks]})


@flashcards_bp.get("/api/flashcards/<int:deck_id>")
@student_required
def api_get_deck(deck_id: int):
    deck = get_owned_or_404(FlashcardDeck, deck_id)
    return api_success(flashcard_deck_detail(deck))


@flashcards_bp.post("/api/flashcards/cards/<int:card_id>/review")
@student_required
def api_review_card(card_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Send a JSON object with the review status.")
    deck = review_card(current_user, card_id, payload.get("status"))
    return api_success(
        {
            "deck": flashcard_deck_summary(deck),
            "card": {
                "id": card_id,
                "status": payload.get("status"),
            },
        },
        message="Card progress saved.",
    )


@flashcards_bp.post("/api/flashcards/<int:deck_id>/reset")
@student_required
def api_reset_deck(deck_id: int):
    deck = get_owned_or_404(FlashcardDeck, deck_id)
    reset_deck(deck)
    return api_success(flashcard_deck_summary(deck), message="Deck reset to new.")


@flashcards_bp.delete("/api/flashcards/<int:deck_id>")
@student_required
def api_delete_deck(deck_id: int):
    deck = get_owned_or_404(FlashcardDeck, deck_id)
    db.session.delete(deck)
    db.session.commit()
    return api_success({"id": deck_id}, message="Flashcard deck deleted.")
