"""First-run seed data and an optional demo-activity seeder."""
from __future__ import annotations

from datetime import date, timedelta

from flask import current_app
from sqlalchemy import func

from .constants import AI_MODES
from .extensions import db
from .models import (
    LearningContent,
    Quiz,
    QuizAttempt,
    StudentProfile,
    StudyPlan,
    Subject,
    Topic,
    User,
    utcnow,
)

SUBJECT_SEED = [
    (
        "Computer Science",
        "Programming, algorithms, data structures and software engineering fundamentals.",
        [
            ("Python Basics", "Syntax, variables, data types and writing your first Python programs."),
            ("Object-Oriented Programming", "Classes, objects, inheritance, polymorphism and encapsulation."),
            ("Functions in Python", "Defining reusable functions, arguments, return values and scope."),
            ("Data Structures", "Lists, stacks, queues, trees and choosing the right structure."),
            ("Algorithms", "Searching, sorting, complexity and problem-solving strategies."),
            ("File Handling", "Reading and writing text, CSV and JSON files safely."),
        ],
    ),
    (
        "Database Management Systems",
        "Relational modelling, SQL, normalization, transactions and indexing.",
        [
            ("SQL Basics", "SELECT, filtering, joins and modifying data in relational databases."),
            ("Normalization", "Functional dependencies, 1NF to 3NF and removing data anomalies."),
            ("ER Model", "Entities, relationships, cardinality and converting ER diagrams to tables."),
            ("Transactions and ACID", "Atomicity, consistency, isolation, durability and concurrency."),
            ("Indexing", "B-tree indexes, query plans and trade-offs between reads and writes."),
        ],
    ),
    (
        "Operating Systems",
        "Processes, scheduling, memory, file systems and concurrency.",
        [
            ("Process Management", "Process states, PCBs, context switching and inter-process communication."),
            ("CPU Scheduling", "FCFS, SJF, round-robin, priority scheduling and performance metrics."),
            ("Deadlocks", "Necessary conditions, prevention, avoidance and detection strategies."),
            ("Memory Management", "Paging, segmentation, virtual memory and page replacement."),
            ("File Systems", "Files, directories, allocation methods and disk scheduling."),
        ],
    ),
    (
        "Artificial Intelligence",
        "Machine learning, neural networks, NLP and intelligent systems.",
        [
            ("Machine Learning Basics", "Features, labels, training, evaluation and overfitting."),
            ("Neural Networks", "Perceptrons, layers, activation functions and backpropagation."),
            ("Natural Language Processing", "Tokenization, embeddings, language models and applications."),
            ("Introduction to AI", "Search, knowledge representation and the scope of artificial intelligence."),
        ],
    ),
    (
        "Mathematics",
        "Discrete mathematics, matrices, probability and graph theory.",
        [
            ("Set Theory", "Sets, operations, Venn diagrams and cardinality."),
            ("Matrices", "Matrix operations, determinants, inverses and applications."),
            ("Probability Basics", "Events, conditional probability, independence and Bayes' theorem."),
            ("Graph Theory", "Vertices, edges, paths, trees and graph traversal."),
        ],
    ),
    (
        "Physics",
        "Mechanics, energy, optics and electromagnetic phenomena.",
        [
            ("Newton's Laws of Motion", "Force, mass, acceleration, inertia and action-reaction pairs."),
            ("Work, Energy and Power", "Work-energy theorem, conservative forces and power calculations."),
            ("Optics", "Reflection, refraction, lenses and image formation."),
            ("Electromagnetic Induction", "Magnetic flux, Faraday's law and Lenz's law."),
        ],
    ),
]


def seed_initial_data() -> dict:
    """Idempotently create the admin account, subjects and topics."""
    created = {"admin": False, "subjects": 0, "topics": 0}

    admin_email = (current_app.config.get("ADMIN_EMAIL") or "").strip().lower()
    admin_password = current_app.config.get("ADMIN_PASSWORD") or ""
    if admin_email and admin_password:
        existing = User.query.filter(func.lower(User.email) == admin_email).first()
        if existing is None:
            admin = User(
                name=current_app.config.get("ADMIN_NAME") or "Administrator",
                email=admin_email,
                role="admin",
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            created["admin"] = True
        elif existing.role != "admin":
            current_app.logger.warning(
                "ADMIN_EMAIL belongs to a student account; admin not created."
            )

    for subject_name, description, topics in SUBJECT_SEED:
        subject = Subject.query.filter(
            func.lower(Subject.subject_name) == subject_name.lower()
        ).first()
        if subject is None:
            subject = Subject(subject_name=subject_name, description=description)
            db.session.add(subject)
            db.session.flush()
            created["subjects"] += 1
        for topic_name, topic_description in topics:
            exists = Topic.query.filter(
                Topic.subject_id == subject.id,
                func.lower(Topic.topic_name) == topic_name.lower(),
            ).first()
            if exists is None:
                db.session.add(
                    Topic(
                        subject_id=subject.id,
                        topic_name=topic_name,
                        description=topic_description,
                    )
                )
                created["topics"] += 1

    db.session.commit()
    return created


def _find_topic(subject_name: str, topic_name: str) -> Topic | None:
    return (
        Topic.query.join(Subject)
        .filter(Subject.subject_name == subject_name, Topic.topic_name == topic_name)
        .first()
    )


def seed_demo_activity() -> str:
    """Create a demo student with realistic activity for presentations.

    This is optional and only runs through `flask seed-demo`. All statistics in
    the UI remain database-derived; this merely creates real rows to look at.
    """
    from .services.demo_bank import build_demo_content, get_demo_quiz
    from .services.quiz_generator import evaluate_quiz
    from .services.study_plan_generator import generate_study_plan, toggle_day

    email = "student@learnforge.com"
    if User.query.filter_by(email=email).first():
        return "Demo student already exists. Sign in with student@learnforge.com / Student@12345."

    user = User(name="Demo Student", email=email, role="student")
    user.set_password("Student@12345")
    profile = StudentProfile(
        user=user,
        course="B.Tech Computer Science",
        department="Computer Science & Engineering",
        year="2nd Year",
        learning_level="Beginner",
        preferred_language="English",
        learning_style="Practical Examples",
        learning_goals=(
            "Build strong programming fundamentals, revise DBMS regularly and score above "
            "85% in my semester exams."
        ),
    )
    profile.set_subjects(
        ["Computer Science", "Database Management Systems", "Artificial Intelligence"]
    )
    db.session.add_all([user, profile])
    db.session.commit()

    sample_contents = [
        ("Computer Science", "Python Basics", "Detailed Notes", 9, "Built the first steps of my Python foundation."),
        ("Database Management Systems", "SQL Basics", "Short Notes", 5, "Quick SQL revision before the lab test."),
        ("Artificial Intelligence", "Machine Learning Basics", "Exam Preparation Notes", 2, "Focused on features, labels and overfitting."),
    ]
    for subject_name, topic_name, content_type, days_ago, _ in sample_contents:
        topic = _find_topic(subject_name, topic_name)
        if not topic:
            continue
        content, note = build_demo_content(
            subject_name=subject_name,
            topic_name=topic_name,
            level="Beginner",
            content_type=content_type,
            language="English",
            style="Practical Examples",
        )
        record = LearningContent(
            user_id=user.id,
            subject_id=topic.subject_id,
            topic_id=topic.id,
            title=content["title"],
            learning_level="Beginner",
            content_type=content_type,
            language="English",
            explanation_style="Practical Examples",
            generated_content=content,
            ai_mode="demo",
            ai_note=note,
            created_at=utcnow() - timedelta(days=days_ago),
        )
        db.session.add(record)

    quiz_specs = [
        ("Computer Science", "Python Basics", "Easy", 4, 3),
        ("Database Management Systems", "SQL Basics", "Medium", 3, 1),
    ]
    for subject_name, topic_name, difficulty, correct_count, days_ago in quiz_specs:
        topic = _find_topic(subject_name, topic_name)
        if not topic:
            continue
        questions, note = get_demo_quiz(topic_name, difficulty, 5)
        quiz = Quiz(
            user_id=user.id,
            subject_id=topic.subject_id,
            topic_id=topic.id,
            difficulty=difficulty,
            num_questions=len(questions),
            questions=questions,
            ai_mode="demo",
            ai_note=note,
            created_at=utcnow() - timedelta(days=days_ago),
        )
        db.session.add(quiz)
        db.session.commit()

        answers = {}
        for index, question in enumerate(questions):
            correct = int(question["correct_index"])
            answers[str(index)] = correct if index < correct_count else (correct + 1) % 4
        attempt = evaluate_quiz(quiz, user, answers)
        attempt.attempted_at = utcnow() - timedelta(days=days_ago)
        db.session.commit()

    cs = Subject.query.filter_by(subject_name="Computer Science").first()
    if cs:
        topic_ids = [
            topic.id
            for topic in Topic.query.filter(
                Topic.subject_id == cs.id,
                Topic.topic_name.in_(["Python Basics", "Functions in Python", "Data Structures"]),
            ).all()
        ]
        if topic_ids:
            plan = generate_study_plan(
                user,
                {
                    "subject_id": cs.id,
                    "topic_ids": topic_ids,
                    "hours_per_day": 2,
                    "target_date": (date.today() + timedelta(days=9)).isoformat(),
                    "learning_level": "Beginner",
                },
            )
            plan.created_at = utcnow() - timedelta(days=8)
            for index in range(min(3, plan.total_days)):
                toggle_day(plan, index)
            db.session.commit()

    return (
        "Demo student created: student@learnforge.com / Student@12345 "
        "(3 materials, 2 quiz attempts, 1 study plan)."
    )
