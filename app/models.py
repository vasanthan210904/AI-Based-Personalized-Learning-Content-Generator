"""SQLAlchemy models for LearnForge AI."""
from __future__ import annotations

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .constants import PERFORMANCE_LEVELS
from .extensions import db


def utcnow() -> datetime:
    """Naive UTC timestamp (SQLite-friendly, consistent across the app)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.CheckConstraint("role IN ('student', 'admin')", name="ck_user_role"),
    )

    profile = db.relationship(
        "StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    contents = db.relationship(
        "LearningContent", back_populates="user", cascade="all, delete-orphan"
    )
    quizzes = db.relationship("Quiz", back_populates="user", cascade="all, delete-orphan")
    attempts = db.relationship(
        "QuizAttempt", back_populates="user", cascade="all, delete-orphan"
    )
    study_plans = db.relationship(
        "StudyPlan", back_populates="user", cascade="all, delete-orphan"
    )
    bookmarks = db.relationship(
        "ContentBookmark", back_populates="user", cascade="all, delete-orphan"
    )
    flashcard_decks = db.relationship(
        "FlashcardDeck", back_populates="user", cascade="all, delete-orphan"
    )
    shares = db.relationship(
        "ContentShare", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def initials(self) -> str:
        parts = [p for p in (self.name or "").split() if p]
        if not parts:
            return "S"
        if len(parts) == 1:
            return parts[0][:1].upper()
        return (parts[0][:1] + parts[-1][:1]).upper()

    @property
    def first_name(self) -> str:
        return (self.name or "Student").split()[0]

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<User {self.email} ({self.role})>"


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    course = db.Column(db.String(120), nullable=True)
    department = db.Column(db.String(120), nullable=True)
    year = db.Column(db.String(20), nullable=True)
    learning_level = db.Column(db.String(20), nullable=False, default="Beginner")
    preferred_language = db.Column(db.String(30), nullable=False, default="English")
    learning_style = db.Column(db.String(40), nullable=False, default="Simple Explanation")
    learning_goals = db.Column(db.Text, nullable=True)
    interested_subjects = db.Column(db.Text, nullable=True)  # comma-separated subject names
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    user = db.relationship("User", back_populates="profile")

    @property
    def subject_list(self) -> list[str]:
        if not self.interested_subjects:
            return []
        return [s.strip() for s in self.interested_subjects.split(",") if s.strip()]

    def set_subjects(self, subjects) -> None:
        seen: list[str] = []
        for subject in subjects or []:
            cleaned = str(subject).strip()
            if cleaned and cleaned not in seen:
                seen.append(cleaned)
        self.interested_subjects = ", ".join(seen)

    @property
    def is_configured(self) -> bool:
        return bool(self.learning_goals and self.subject_list and self.course)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<StudentProfile user_id={self.user_id}>"


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    topics = db.relationship(
        "Topic", back_populates="subject", cascade="all, delete-orphan", order_by="Topic.topic_name"
    )
    contents = db.relationship("LearningContent", back_populates="subject")
    quizzes = db.relationship("Quiz", back_populates="subject")
    study_plans = db.relationship("StudyPlan", back_populates="subject")
    flashcard_decks = db.relationship("FlashcardDeck", back_populates="subject")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Subject {self.subject_name}>"


class Topic(db.Model):
    __tablename__ = "topics"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True
    )
    topic_name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    subject = db.relationship("Subject", back_populates="topics")
    contents = db.relationship("LearningContent", back_populates="topic")
    quizzes = db.relationship("Quiz", back_populates="topic")
    flashcard_decks = db.relationship("FlashcardDeck", back_populates="topic")

    __table_args__ = (
        db.UniqueConstraint("subject_id", "topic_name", name="uq_topic_subject_name"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Topic {self.topic_name}>"


class LearningContent(db.Model):
    __tablename__ = "learning_contents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True
    )
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), nullable=False, index=True)
    title = db.Column(db.String(220), nullable=False)
    learning_level = db.Column(db.String(20), nullable=False)
    content_type = db.Column(db.String(60), nullable=False)
    language = db.Column(db.String(30), nullable=False, default="English")
    explanation_style = db.Column(db.String(60), nullable=False)
    generated_content = db.Column(db.JSON, nullable=False)
    ai_mode = db.Column(db.String(20), nullable=False, default="demo")
    ai_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    user = db.relationship("User", back_populates="contents")
    subject = db.relationship("Subject", back_populates="contents")
    topic = db.relationship("Topic", back_populates="contents")
    bookmarks = db.relationship(
        "ContentBookmark", back_populates="content", cascade="all, delete-orphan"
    )
    shares = db.relationship(
        "ContentShare", back_populates="content", cascade="all, delete-orphan"
    )
    flashcard_decks = db.relationship("FlashcardDeck", back_populates="content")

    @property
    def mode_info(self) -> dict:
        from .constants import AI_MODES

        return AI_MODES.get(self.ai_mode, AI_MODES["demo"])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LearningContent {self.title}>"


class Quiz(db.Model):
    __tablename__ = "quizzes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True
    )
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), nullable=False, index=True)
    difficulty = db.Column(db.String(20), nullable=False)
    num_questions = db.Column(db.Integer, nullable=False)
    questions = db.Column(db.JSON, nullable=False)
    ai_mode = db.Column(db.String(20), nullable=False, default="demo")
    ai_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    user = db.relationship("User", back_populates="quizzes")
    subject = db.relationship("Subject", back_populates="quizzes")
    topic = db.relationship("Topic", back_populates="quizzes")
    attempts = db.relationship(
        "QuizAttempt", back_populates="quiz", cascade="all, delete-orphan"
    )

    def public_questions(self) -> list[dict]:
        """Return questions without answers or explanations (safe for the browser)."""
        result = []
        for index, q in enumerate(self.questions or []):
            result.append(
                {
                    "index": index,
                    "question": q.get("question", ""),
                    "options": list(q.get("options", [])),
                }
            )
        return result

    @property
    def mode_info(self) -> dict:
        from .constants import AI_MODES

        return AI_MODES.get(self.ai_mode, AI_MODES["demo"])

    @property
    def best_attempt(self):
        return max(self.attempts, key=lambda a: a.percentage, default=None)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Quiz {self.id} {self.topic.topic_name if self.topic else ''}>"


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    answers = db.Column(db.JSON, nullable=False, default=dict)
    score = db.Column(db.Integer, nullable=False, default=0)
    total_questions = db.Column(db.Integer, nullable=False, default=0)
    correct_count = db.Column(db.Integer, nullable=False, default=0)
    wrong_count = db.Column(db.Integer, nullable=False, default=0)
    unanswered_count = db.Column(db.Integer, nullable=False, default=0)
    percentage = db.Column(db.Float, nullable=False, default=0.0)
    attempted_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    quiz = db.relationship("Quiz", back_populates="attempts")
    user = db.relationship("User", back_populates="attempts")

    @property
    def performance(self) -> dict:
        points = self.percentage or 0
        for key in ("excellent", "good", "average", "needs_improvement"):
            info = PERFORMANCE_LEVELS[key]
            if points >= info["min"]:
                return {"key": key, **info}
        return {"key": "needs_improvement", **PERFORMANCE_LEVELS["needs_improvement"]}

    @property
    def score_label(self) -> str:
        return f"{self.score}/{self.total_questions}"

    def __repr__(self) -> str:  # pragma: no cover
        return f"<QuizAttempt {self.id} {self.percentage}%>"


class StudyPlan(db.Model):
    __tablename__ = "study_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True
    )
    learning_level = db.Column(db.String(20), nullable=False, default="Beginner")
    hours_per_day = db.Column(db.Float, nullable=False, default=2.0)
    target_date = db.Column(db.Date, nullable=False)
    plan_data = db.Column(db.JSON, nullable=False)
    completion_status = db.Column(db.JSON, nullable=False, default=lambda: {"completed_days": []})
    ai_mode = db.Column(db.String(20), nullable=False, default="demo")
    ai_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    user = db.relationship("User", back_populates="study_plans")
    subject = db.relationship("Subject", back_populates="study_plans")

    @property
    def days(self) -> list[dict]:
        return (self.plan_data or {}).get("days", [])

    @property
    def total_days(self) -> int:
        return len(self.days)

    @property
    def completed_day_indices(self) -> list[int]:
        return list((self.completion_status or {}).get("completed_days", []))

    @property
    def completed_days(self) -> int:
        return len(self.completed_day_indices)

    @property
    def completion_percentage(self) -> int:
        if not self.total_days:
            return 0
        return round(self.completed_days / self.total_days * 100)

    @property
    def is_complete(self) -> bool:
        return self.total_days > 0 and self.completed_days >= self.total_days

    @property
    def mode_info(self) -> dict:
        from .constants import AI_MODES

        return AI_MODES.get(self.ai_mode, AI_MODES["demo"])

    def is_day_completed(self, index: int) -> bool:
        return index in self.completed_day_indices

    def __repr__(self) -> str:  # pragma: no cover
        return f"<StudyPlan {self.id} {self.subject.subject_name if self.subject else ''}>"


class ContentBookmark(db.Model):
    """A saved material with an optional private study note."""

    __tablename__ = "content_bookmarks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    content_id = db.Column(
        db.Integer, db.ForeignKey("learning_contents.id"), nullable=False, index=True
    )
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    user = db.relationship("User", back_populates="bookmarks")
    content = db.relationship("LearningContent", back_populates="bookmarks")

    __table_args__ = (
        db.UniqueConstraint("user_id", "content_id", name="uq_bookmark_user_content"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ContentBookmark user_id={self.user_id} content_id={self.content_id}>"


class FlashcardDeck(db.Model):
    """A personalised flashcard deck generated from material or a topic."""

    __tablename__ = "flashcard_decks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True
    )
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), nullable=False, index=True)
    content_id = db.Column(
        db.Integer, db.ForeignKey("learning_contents.id"), nullable=True, index=True
    )
    title = db.Column(db.String(220), nullable=False)
    source = db.Column(db.String(30), nullable=False, default="topic")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    last_studied_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", back_populates="flashcard_decks")
    subject = db.relationship("Subject", back_populates="flashcard_decks")
    topic = db.relationship("Topic", back_populates="flashcard_decks")
    content = db.relationship("LearningContent", back_populates="flashcard_decks")
    cards = db.relationship(
        "Flashcard",
        back_populates="deck",
        cascade="all, delete-orphan",
        order_by="Flashcard.position",
    )

    @property
    def total_cards(self) -> int:
        return len(self.cards)

    @property
    def known_cards(self) -> int:
        return sum(1 for card in self.cards if card.status == "known")

    @property
    def review_cards(self) -> int:
        return sum(1 for card in self.cards if card.status == "review")

    @property
    def new_cards(self) -> int:
        return sum(1 for card in self.cards if card.status == "new")

    @property
    def mastery_percentage(self) -> int:
        if not self.total_cards:
            return 0
        return round(self.known_cards / self.total_cards * 100)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<FlashcardDeck {self.id} {self.title}>"


class Flashcard(db.Model):
    __tablename__ = "flashcards"

    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(
        db.Integer, db.ForeignKey("flashcard_decks.id"), nullable=False, index=True
    )
    front = db.Column(db.Text, nullable=False)
    back = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="new")
    review_count = db.Column(db.Integer, nullable=False, default=0)
    last_reviewed_at = db.Column(db.DateTime, nullable=True)

    deck = db.relationship("FlashcardDeck", back_populates="cards")

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('new', 'review', 'known')", name="ck_flashcard_status"
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Flashcard {self.id} {self.status}>"


class ContentShare(db.Model):
    """A revocable, read-only public link for a generated material."""

    __tablename__ = "content_shares"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    content_id = db.Column(
        db.Integer, db.ForeignKey("learning_contents.id"), nullable=False, unique=True, index=True
    )
    token = db.Column(db.String(80), nullable=False, unique=True, index=True)
    views = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    last_viewed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", back_populates="shares")
    content = db.relationship("LearningContent", back_populates="shares")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ContentShare {self.token}>"
