"""LearnForge AI - Flask application factory."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import click
from flask import Flask, jsonify, render_template, request, url_for
from flask_login import current_user
from flask_wtf.csrf import CSRFError

from config import Config

from .constants import (
    AI_MODES,
    CONTENT_TYPES,
    CONTENT_TYPE_INFO,
    LANGUAGES,
    LEARNING_LEVEL_INFO,
    LEARNING_LEVELS,
    LEARNING_STYLE_INFO,
    LEARNING_STYLES,
    QUIZ_DIFFICULTIES,
    QUIZ_DIFFICULTY_INFO,
)
from .extensions import csrf, db, login_manager
from .models import User, utcnow
from .utils.rate_limit import RateLimitExceeded
from .utils.responses import api_error
from .utils.validation import ValidationError


def _is_api_request() -> bool:
    return request.path.startswith("/api/")


def create_app(config_object=None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object or Config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .routes.admin import admin_api_bp, admin_bp
    from .routes.auth import auth_bp
    from .routes.flashcards import flashcards_bp
    from .routes.learning import learning_bp
    from .routes.library import library_bp
    from .routes.progress import progress_bp
    from .routes.public import public_bp
    from .routes.quiz import quiz_bp
    from .routes.student import student_bp
    from .routes.study_plan import study_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(study_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(flashcards_bp)
    app.register_blueprint(library_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_api_bp)

    # ------------------------------------------------------------------
    # Auth plumbing
    # ------------------------------------------------------------------
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        if _is_api_request():
            return api_error(
                "Please sign in to continue.", status=401, code="unauthorized"
            )
        return url_for_login()

    def url_for_login():
        from flask import redirect

        return redirect(url_for("auth.login", next=request.path))

    # ------------------------------------------------------------------
    # Template helpers
    # ------------------------------------------------------------------
    @app.context_processor
    def inject_globals():
        from .services.ai_service import AIService

        ai_status = AIService(app.config).status()
        return {
            "app_name": app.config["APP_NAME"],
            "app_tagline": app.config["APP_TAGLINE"],
            "project_title": app.config["PROJECT_TITLE"],
            "current_year": date.today().year,
            "ai_status": ai_status,
            "mode_info": AI_MODES,
            "learning_levels": LEARNING_LEVELS,
            "learning_level_info": LEARNING_LEVEL_INFO,
            "learning_styles": LEARNING_STYLES,
            "learning_style_info": LEARNING_STYLE_INFO,
            "languages": LANGUAGES,
            "content_types": CONTENT_TYPES,
            "content_type_info": CONTENT_TYPE_INFO,
            "quiz_difficulties": QUIZ_DIFFICULTIES,
            "quiz_difficulty_info": QUIZ_DIFFICULTY_INFO,
        }

    @app.template_filter("nice_date")
    def nice_date(value, fmt: str = "%d %b %Y"):
        if not value:
            return "-"
        try:
            return value.strftime(fmt)
        except (AttributeError, ValueError):
            return str(value)

    @app.template_filter("time_ago")
    def time_ago(value):
        if not value:
            return ""
        seconds = max(0, (utcnow() - value).total_seconds())
        if seconds < 60:
            return "just now"
        if seconds < 3600:
            return f"{int(seconds // 60)} min ago"
        if seconds < 86400:
            return f"{int(seconds // 3600)} hr ago"
        days = int(seconds // 86400)
        if days == 1:
            return "yesterday"
        if days < 30:
            return f"{days} days ago"
        return value.strftime("%d %b %Y")

    @app.template_filter("initial")
    def initial(value):
        text = (value or "S").strip()
        return text[:1].upper() if text else "S"

    # ------------------------------------------------------------------
    # Error handlers (JSON for API, friendly pages otherwise)
    # ------------------------------------------------------------------
    @app.errorhandler(404)
    def handle_404(error):
        if _is_api_request():
            return api_error("The requested resource was not found.", status=404, code="not_found")
        return (
            render_template(
                "errors/error.html",
                code=404,
                title="Page not found",
                message="The page you are looking for may have moved or no longer exists.",
            ),
            404,
        )

    @app.errorhandler(403)
    def handle_403(error):
        if _is_api_request():
            return api_error(
                "You do not have permission to perform this action.",
                status=403,
                code="forbidden",
            )
        return (
            render_template(
                "errors/error.html",
                code=403,
                title="Access denied",
                message="You do not have permission to view this page.",
            ),
            403,
        )

    @app.errorhandler(400)
    def handle_400(error):
        if _is_api_request():
            return api_error("The request was invalid.", status=400, code="bad_request")
        return (
            render_template(
                "errors/error.html",
                code=400,
                title="Bad request",
                message="Something about that request was not valid. Please go back and try again.",
            ),
            400,
        )

    @app.errorhandler(413)
    def handle_413(error):
        if _is_api_request():
            return api_error(
                "The uploaded request is too large.", status=413, code="payload_too_large"
            )
        return (
            render_template(
                "errors/error.html",
                code=413,
                title="Request too large",
                message="The data sent was too large. Please try a smaller request.",
            ),
            413,
        )

    @app.errorhandler(CSRFError)
    def handle_csrf(error):
        if _is_api_request():
            return api_error(
                "Your session token was missing or expired. Refresh the page and try again.",
                status=400,
                code="csrf_failed",
            )
        return (
            render_template(
                "errors/error.html",
                code=400,
                title="Session expired",
                message="Your form session expired. Go back, refresh the page and try again.",
            ),
            400,
        )

    @app.errorhandler(ValidationError)
    def handle_validation(error):
        if _is_api_request():
            fields = {error.field: error.message} if error.field else None
            return api_error(
                error.message, status=422, code="validation_error", fields=fields
            )
        return (
            render_template(
                "errors/error.html",
                code=422,
                title="Check your input",
                message=error.message,
            ),
            422,
        )

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(error):
        response = (
            api_error(error.message, status=429, code="rate_limited")
            if _is_api_request()
            else (
                render_template(
                    "errors/error.html",
                    code=429,
                    title="Slow down for a moment",
                    message=error.message,
                ),
                429,
            )
        )
        if isinstance(response, tuple):
            payload, status = response[0], response[1]
            if hasattr(payload, "headers"):
                payload.headers["Retry-After"] = str(error.retry_after)
        return response

    @app.errorhandler(429)
    def handle_429(error):
        if _is_api_request():
            return api_error(
                "Too many requests. Please wait and try again.",
                status=429,
                code="rate_limited",
            )
        return (
            render_template(
                "errors/error.html",
                code=429,
                title="Slow down for a moment",
                message="Too many requests were sent. Please wait a moment and try again.",
            ),
            429,
        )

    @app.errorhandler(500)
    def handle_500(error):
        db.session.rollback()
        app.logger.exception("Unhandled application error")
        if _is_api_request():
            return api_error(
                "Something went wrong on our side. Please try again.",
                status=500,
                code="internal_error",
            )
        return (
            render_template(
                "errors/error.html",
                code=500,
                title="Something went wrong",
                message="The application hit an unexpected error. Please try again.",
            ),
            500,
        )

    from .services.ai_service import AIServiceError

    @app.errorhandler(AIServiceError)
    def handle_ai_error(error):
        if _is_api_request():
            return api_error(error.message, status=error.status, code=error.code)
        return (
            render_template(
                "errors/error.html",
                code=error.status,
                title="AI service unavailable",
                message=error.message,
            ),
            error.status,
        )

    # ------------------------------------------------------------------
    # Security headers
    # ------------------------------------------------------------------
    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        if _is_api_request():
            response.headers.setdefault("Cache-Control", "no-store")
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response

    # ------------------------------------------------------------------
    # CLI commands
    # ------------------------------------------------------------------
    @app.cli.command("init-db")
    def init_db_command():
        """Create tables and seed admin, subjects and topics."""
        db.create_all()
        result = seed_data()
        click.echo(
            f"Database ready. Admin created: {result['admin']}, "
            f"subjects added: {result['subjects']}, topics added: {result['topics']}."
        )

    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Create a demo student with sample activity."""
        db.create_all()
        seed_data()
        from .seed import seed_demo_activity

        click.echo(seed_demo_activity())

    def seed_data():
        from .seed import seed_initial_data

        return seed_initial_data()

    # ------------------------------------------------------------------
    # First-run bootstrap
    # ------------------------------------------------------------------
    if app.config.get("AUTO_INIT_DB"):
        with app.app_context():
            db.create_all()
            try:
                result = seed_data()
                if any(result.values()):
                    app.logger.info("Database seeded: %s", result)
            except Exception:
                db.session.rollback()
                app.logger.exception("Database seeding failed")

    return app
