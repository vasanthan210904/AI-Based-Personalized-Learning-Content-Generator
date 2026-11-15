"""AI quiz generation, server-side evaluation and result review."""
from __future__ import annotations

from flask import current_app

from ..constants import QUIZ_DIFFICULTIES, QUIZ_MAX_QUESTIONS, QUIZ_MIN_QUESTIONS
from ..extensions import db
from ..models import Quiz, QuizAttempt, Subject, Topic
from ..utils.validation import ValidationError, choice, parse_int
from .ai_service import AIService, AIServiceError
from .demo_bank import DemoUnavailable, get_demo_quiz
from .prompts import build_quiz_prompt


def _normalize_questions(raw_questions, limit: int) -> list[dict]:
    if isinstance(raw_questions, dict):
        raw_questions = raw_questions.get("questions", [])
    if not isinstance(raw_questions, (list, tuple)):
        return []

    questions: list[dict] = []
    for item in raw_questions:
        if not isinstance(item, dict):
            continue
        question = str(item.get("question") or "").strip()
        options_raw = item.get("options")
        if not question or not isinstance(options_raw, (list, tuple)):
            continue
        options = [str(option).strip() for option in options_raw if str(option).strip()]
        if len(options) < 4:
            continue
        options = options[:4]
        if len(set(options)) != 4:
            continue

        correct = item.get("correct_index", item.get("correct_answer_index"))
        if correct is None and isinstance(item.get("correct_answer"), str):
            try:
                correct = options.index(item["correct_answer"].strip())
            except ValueError:
                correct = None
        try:
            correct = int(correct)
        except (TypeError, ValueError):
            continue
        if correct < 0 or correct >= 4:
            continue

        explanation = str(item.get("explanation") or "").strip()
        questions.append(
            {
                "question": question[:1000],
                "options": options,
                "correct_index": correct,
                "explanation": explanation[:2000]
                or "Review the related concept in your notes and try the question again.",
            }
        )
        if len(questions) >= limit:
            break
    return questions


def _validate_payload(payload: dict) -> tuple[Subject, Topic, str, int]:
    if not isinstance(payload, dict):
        raise ValidationError("Send a JSON object with the quiz options.")

    # Subject resolution
    custom_subject = str(payload.get("custom_subject") or "").strip()
    subject_id_raw = payload.get("subject_id")
    subject = None
    if subject_id_raw:
        try:
            subject = db.session.get(Subject, int(subject_id_raw))
        except (TypeError, ValueError):
            pass
    if subject is None:
        if custom_subject:
            subject = Subject.query.filter(db.func.lower(Subject.subject_name) == custom_subject.lower()).first()
            if not subject:
                subject = Subject(subject_name=custom_subject, description=f"Custom curriculum: {custom_subject}")
                db.session.add(subject)
                db.session.flush()
        else:
            raise ValidationError("The selected subject does not exist.", "subject_id")

    # Topic resolution (supports custom_topic or topic_id)
    custom_topic = str(payload.get("custom_topic") or payload.get("custom_topic_name") or "").strip()
    topic_id_raw = payload.get("topic_id")
    topic = None

    if custom_topic:
        topic = Topic.query.filter(
            Topic.subject_id == subject.id,
            db.func.lower(Topic.topic_name) == custom_topic.lower()
        ).first()
        if not topic:
            topic = Topic(subject_id=subject.id, topic_name=custom_topic, description=f"Custom topic: {custom_topic}")
            db.session.add(topic)
            db.session.flush()
    else:
        topic_id = parse_int(topic_id_raw, "topic_id", label="Topic")
        topic = db.session.get(Topic, topic_id)
        if topic is None or topic.subject_id != subject.id:
            raise ValidationError("Choose a topic that belongs to the selected subject.", "topic_id")

    difficulty = choice(payload.get("difficulty"), QUIZ_DIFFICULTIES, "difficulty", "difficulty")
    raw_count = payload.get("num_questions", payload.get("question_count", 5))
    count = parse_int(
        raw_count,
        "num_questions",
        minimum=QUIZ_MIN_QUESTIONS,
        maximum=QUIZ_MAX_QUESTIONS,
        label="Number of questions",
    )
    return subject, topic, difficulty, count


def generate_quiz(user, payload: dict) -> Quiz:
    subject, topic, difficulty, count = _validate_payload(payload)
    config = current_app.config

    ai_engine = str(payload.get("ai_engine") or payload.get("ai_model") or "").strip()
    custom_prov, custom_mod = None, None
    if ":" in ai_engine:
        custom_prov, custom_mod = ai_engine.split(":", 1)
    elif ai_engine:
        custom_prov = ai_engine

    if custom_prov == "offline":
        ai = None
    else:
        ai = AIService(config, provider=custom_prov, model=custom_mod)

    profile = user.profile
    level = profile.learning_level if profile else "Intermediate"
    language = profile.preferred_language if profile else "English"

    questions: list[dict] = []
    mode = "demo"
    note = ""

    if ai and ai.is_live_available():
        system_prompt, user_prompt = build_quiz_prompt(
            subject_name=subject.subject_name,
            topic_name=topic.topic_name,
            difficulty=difficulty,
            num_questions=count,
            level=level,
            language=language,
        )
        try:
            raw = ai.generate_json(
                system_prompt,
                user_prompt,
                max_tokens=config.get("AI_MAX_TOKENS_QUIZ", 4000),
                temperature=0.45,
            )
            questions = _normalize_questions(raw.get("questions", raw), count)
            if not questions:
                raise AIServiceError(
                    "The AI did not return usable quiz questions. Please try again.",
                    code="ai_invalid_response",
                )
            mode = "live"
            if len(questions) < count:
                note = (
                    f"The AI returned {len(questions)} valid questions instead of {count}. "
                    "All valid questions were kept."
                )
        except AIServiceError as exc:
            current_app.logger.warning("Quiz generation failed: %s", exc.message)
            if config.get("AI_DEMO_MODE") == "off":
                raise
            try:
                questions, note = get_demo_quiz(topic.topic_name, difficulty, count)
            except DemoUnavailable as demo_exc:
                raise AIServiceError(
                    f"Live AI was unavailable ({exc.message}) and {demo_exc}",
                    code="demo_unavailable",
                    status=422,
                ) from None
            mode = "demo_fallback"
            note = f"Live AI was unavailable: {exc.message} {note}"
    else:
        if config.get("AI_DEMO_MODE") == "off":
            raise AIServiceError(
                "Live AI is required (AI_DEMO_MODE=off) but AI_API_KEY is not configured.",
                code="ai_not_configured",
                status=503,
            )
        try:
            questions, note = get_demo_quiz(topic.topic_name, difficulty, count)
        except DemoUnavailable as exc:
            raise AIServiceError(str(exc), code="demo_unavailable", status=422) from None
        mode = "demo"

    quiz = Quiz(
        user_id=user.id,
        subject_id=subject.id,
        topic_id=topic.id,
        difficulty=difficulty,
        num_questions=len(questions),
        questions=questions,
        ai_mode=mode,
        ai_note=note or None,
    )
    db.session.add(quiz)
    db.session.commit()
    return quiz


def _normalise_answers(raw_answers, total: int) -> dict[str, int | None]:
    if isinstance(raw_answers, (list, tuple)):
        mapping = {str(i): value for i, value in enumerate(raw_answers)}
    elif isinstance(raw_answers, dict):
        mapping = raw_answers
    else:
        raise ValidationError("Answers must be sent as an object of question indexes.", "answers")

    normalised: dict[str, int | None] = {}
    for index in range(total):
        value = mapping.get(str(index), mapping.get(index))
        if value is None or value == "" or value == -1 or value == "-1":
            normalised[str(index)] = None
            continue
        try:
            selected = int(value)
        except (TypeError, ValueError):
            normalised[str(index)] = None
            continue
        normalised[str(index)] = selected if 0 <= selected < 4 else None
    return normalised


def evaluate_quiz(quiz: Quiz, user, raw_answers) -> QuizAttempt:
    questions = quiz.questions or []
    if not questions:
        raise ValidationError("This quiz has no questions to evaluate.", "quiz")
    answers = _normalise_answers(raw_answers, len(questions))

    correct = wrong = unanswered = 0
    for index, question in enumerate(questions):
        selected = answers.get(str(index))
        if selected is None:
            unanswered += 1
        elif selected == int(question.get("correct_index", -1)):
            correct += 1
        else:
            wrong += 1

    total = len(questions)
    percentage = round(correct / total * 100, 1) if total else 0.0
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=user.id,
        answers=answers,
        score=correct,
        total_questions=total,
        correct_count=correct,
        wrong_count=wrong,
        unanswered_count=unanswered,
        percentage=percentage,
    )
    db.session.add(attempt)
    db.session.commit()
    return attempt


def build_review(attempt: QuizAttempt) -> list[dict]:
    review = []
    for index, question in enumerate(attempt.quiz.questions or []):
        selected = (attempt.answers or {}).get(str(index))
        correct_index = int(question.get("correct_index", 0))
        review.append(
            {
                "index": index + 1,
                "question": question.get("question", ""),
                "options": question.get("options", []),
                "selected_index": selected,
                "correct_index": correct_index,
                "is_correct": selected == correct_index,
                "is_unanswered": selected is None,
                "explanation": question.get("explanation", ""),
            }
        )
    return review
