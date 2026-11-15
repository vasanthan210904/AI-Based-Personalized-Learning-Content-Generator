"""Flashcard generation and review logic.

Decks are derived from the student's own generated material, or from the
curated offline demo packs when no material exists yet. No AI call is made
here: flashcards always come from content the student can already see.
"""
from __future__ import annotations

from flask import abort, current_app

from ..constants import FLASHCARD_MAX_CARDS
from ..extensions import db
from ..models import Flashcard, FlashcardDeck, LearningContent, Subject, Topic, utcnow
from ..utils.validation import ValidationError, clean_multiline, clean_text, choice, parse_int
from .demo_bank import get_demo_pack


def _add_pair(cards: list[dict], seen: set[str], front, back) -> None:
    front_text = clean_text(front, 400)
    back_text = clean_multiline(back, 3000)
    if not front_text or not back_text:
        return
    key = front_text.casefold()
    if key in seen:
        return
    seen.add(key)
    cards.append({"front": front_text, "back": back_text})


def _extract_cards(data: dict, topic_name: str, subject_name: str) -> list[dict]:
    cards: list[dict] = []
    seen: set[str] = set()

    definitions = data.get("important_definitions") or data.get("definitions") or []
    for item in definitions:
        if isinstance(item, dict):
            _add_pair(cards, seen, item.get("term"), item.get("definition"))

    concepts = data.get("basic_concepts") or data.get("concepts") or []
    for item in concepts:
        if isinstance(item, dict):
            _add_pair(cards, seen, item.get("heading"), item.get("explanation"))

    faqs = data.get("faqs") or []
    for item in faqs:
        if isinstance(item, dict):
            _add_pair(cards, seen, item.get("question"), item.get("answer"))

    summary = clean_multiline(data.get("summary"), 1200)
    introduction = clean_multiline(data.get("introduction") or data.get("intro"), 1200)
    if len(cards) < 3:
        _add_pair(cards, seen, f"What is {topic_name}?", introduction or summary)
    if len(cards) < 3 and summary:
        _add_pair(cards, seen, f"Summarise {topic_name} in your own words.", summary)
    if len(cards) < 3:
        _add_pair(
            cards,
            seen,
            f"Which subject does {topic_name} belong to?",
            f"{topic_name} is part of {subject_name}.",
        )

    return cards[:FLASHCARD_MAX_CARDS]


def _topic_cards(user, topic: Topic, subject: Subject) -> tuple[list[dict], str]:
    """Build cards from a curated demo pack, or from existing material."""
    latest = (
        LearningContent.query.filter_by(user_id=user.id, topic_id=topic.id)
        .order_by(LearningContent.created_at.desc())
        .first()
    )
    if latest:
        cards = _extract_cards(
            latest.generated_content or {}, topic.topic_name, subject.subject_name
        )
        if len(cards) >= 3:
            return cards, "content"

    pack = get_demo_pack(topic.topic_name)
    if pack:
        cards = _extract_cards(pack, topic.topic_name, subject.subject_name)
        if len(cards) >= 3:
            return cards, "demo"

    raise ValidationError(
        "No usable material is available for this topic yet. Generate learning content "
        "for it first, then create flashcards.",
        "topic_id",
    )


def generate_deck(user, payload: dict) -> tuple[FlashcardDeck, bool]:
    """Create (or reuse) a flashcard deck. Returns (deck, created)."""
    if not isinstance(payload, dict):
        raise ValidationError("Send a JSON object with the flashcard options.")

    content = None
    topic = None
    subject = None
    source = "topic"
    cards: list[dict] = []

    if payload.get("content_id") not in (None, ""):
        content_id = parse_int(payload.get("content_id"), "content_id", label="Material")
        content = db.session.get(LearningContent, content_id)
        if content is None or content.user_id != user.id:
            abort(404)
        existing = FlashcardDeck.query.filter_by(
            user_id=user.id, content_id=content.id
        ).first()
        if existing:
            return existing, False
        subject = content.subject
        topic = content.topic
        source = "content"
        cards = _extract_cards(
            content.generated_content or {},
            topic.topic_name if topic else content.title,
            subject.subject_name if subject else "your course",
        )
        if len(cards) < 3:
            raise ValidationError(
                "This material does not contain enough structured facts to build a deck. "
                "Try generating detailed notes first.",
                "content_id",
            )
    else:
        subject_id = parse_int(payload.get("subject_id"), "subject_id", label="Subject")
        topic_id = parse_int(payload.get("topic_id"), "topic_id", label="Topic")
        subject = db.session.get(Subject, subject_id)
        if subject is None:
            raise ValidationError("The selected subject does not exist.", "subject_id")
        topic = db.session.get(Topic, topic_id)
        if topic is None or topic.subject_id != subject.id:
            raise ValidationError(
                "Choose a topic that belongs to the selected subject.", "topic_id"
            )
        cards, source = _topic_cards(user, topic, subject)

    if len(cards) < 3:
        raise ValidationError(
            "At least three flashcards are needed. Generate more detailed material first.",
            "content_id",
        )

    deck = FlashcardDeck(
        user_id=user.id,
        subject_id=subject.id,
        topic_id=topic.id,
        content_id=content.id if content else None,
        title=f"{topic.topic_name} · Flashcards",
        source=source,
    )
    db.session.add(deck)
    db.session.flush()
    for position, item in enumerate(cards):
        deck.cards.append(
            Flashcard(
                front=item["front"],
                back=item["back"],
                position=position,
                status="new",
            )
        )
    db.session.commit()
    current_app.logger.info(
        "Generated flashcard deck %s for user %s from %s", deck.id, user.id, source
    )
    return deck, True


def review_card(user, card_id: int, status: str) -> FlashcardDeck:
    card = db.session.get(Flashcard, card_id)
    if card is None or card.deck is None or card.deck.user_id != user.id:
        abort(404)
    card.status = choice(status, ["new", "review", "known"], "status", "review result")
    card.review_count = (card.review_count or 0) + 1
    card.last_reviewed_at = utcnow()
    card.deck.last_studied_at = utcnow()
    db.session.commit()
    return card.deck


def reset_deck(deck: FlashcardDeck) -> FlashcardDeck:
    for card in deck.cards:
        card.status = "new"
        card.review_count = 0
        card.last_reviewed_at = None
    deck.last_studied_at = None
    db.session.commit()
    return deck
