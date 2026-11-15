"""Authentication pages and JSON auth API."""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..forms import LoginForm, RegistrationForm
from ..models import StudentProfile, User, utcnow
from ..utils.rate_limit import rate_limit
from ..utils.responses import api_error, api_success, form_errors
from ..utils.security import is_safe_redirect
from ..utils.serializers import user_dict
from ..utils.validation import ValidationError

auth_bp = Blueprint("auth", __name__)


def _post_login_url(user) -> str:
    if user.role == "admin":
        return url_for("admin.dashboard")
    return url_for("student.dashboard")


def _create_student(form: RegistrationForm) -> User:
    email = form.email.data.strip().lower()
    user = User(name=form.name.data.strip(), email=email, role="student")
    user.set_password(form.password.data)
    profile = StudentProfile(
        user=user,
        course=form.course.data.strip(),
        department=form.department.data.strip(),
        year=form.year.data,
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValidationError(
            "An account with this email already exists.", "email"
        ) from None
    return user


@auth_bp.route("/register", methods=["GET", "POST"])
@rate_limit(
    "register",
    limit_key="RATE_LIMIT_LOGIN",
    window_key="RATE_LIMIT_LOGIN_WINDOW",
    message="Too many sign-up attempts. Please wait a few minutes.",
)
def register():
    if current_user.is_authenticated:
        return redirect(_post_login_url(current_user))
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = _create_student(form)
        except ValidationError as exc:
            form.email.errors.append(exc.message)
        else:
            login_user(user)
            user.last_login_at = utcnow()
            db.session.commit()
            flash(f"Welcome, {user.first_name}! Your account is ready.", "success")
            flash(
                "Add your learning preferences next so every generation is tailored to you.",
                "info",
            )
            return redirect(url_for("student.dashboard"))
    elif request.method == "POST":
        flash("Please correct the highlighted fields and try again.", "danger")
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@rate_limit(
    "login",
    limit_key="RATE_LIMIT_LOGIN",
    window_key="RATE_LIMIT_LOGIN_WINDOW",
    message="Too many sign-in attempts. Please wait a few minutes and try again.",
)
def login():
    if current_user.is_authenticated:
        return redirect(_post_login_url(current_user))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(form.password.data):
            user.last_login_at = utcnow()
            db.session.commit()
            login_user(user, remember=bool(form.remember.data))
            flash(f"Welcome back, {user.first_name}!", "success")
            next_url = request.args.get("next")
            if is_safe_redirect(next_url):
                return redirect(next_url)
            return redirect(_post_login_url(user))
        flash("Invalid email or password. Please try again.", "danger")
    elif request.method == "POST":
        flash("Please correct the highlighted fields and try again.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out securely.", "info")
    return redirect(url_for("auth.login"))


# ----------------------------------------------------------------------
# JSON API
# ----------------------------------------------------------------------
@auth_bp.post("/api/register")
@rate_limit(
    "api-register",
    limit_key="RATE_LIMIT_LOGIN",
    window_key="RATE_LIMIT_LOGIN_WINDOW",
    message="Too many sign-up attempts. Please wait a few minutes.",
)
def api_register():
    if current_user.is_authenticated:
        return api_error(
            "You are already signed in.", status=409, code="already_authenticated"
        )
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Send a JSON object with the registration details.")
    form = RegistrationForm(data=payload, meta={"csrf": False})
    if not form.validate():
        return api_error(
            "Please correct the highlighted fields.",
            status=422,
            code="validation_error",
            fields=form_errors(form),
        )
    try:
        user = _create_student(form)
    except ValidationError as exc:
        return api_error(exc.message, status=409, code="duplicate_email", fields={exc.field: exc.message})
    login_user(user)
    user.last_login_at = utcnow()
    db.session.commit()
    return api_success(user_dict(user), message="Account created successfully.", status=201)


@auth_bp.post("/api/login")
@rate_limit(
    "api-login",
    limit_key="RATE_LIMIT_LOGIN",
    window_key="RATE_LIMIT_LOGIN_WINDOW",
    message="Too many sign-in attempts. Please wait a few minutes.",
)
def api_login():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Send a JSON object with email and password.")
    form = LoginForm(data=payload, meta={"csrf": False})
    if not form.validate():
        return api_error(
            "Please correct the login details.",
            status=422,
            code="validation_error",
            fields=form_errors(form),
        )
    email = form.email.data.strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(form.password.data):
        return api_error(
            "Invalid email or password.", status=401, code="invalid_credentials"
        )
    user.last_login_at = utcnow()
    db.session.commit()
    login_user(user, remember=bool(form.remember.data))
    return api_success(user_dict(user), message="Signed in successfully.")


@auth_bp.post("/api/logout")
@login_required
def api_logout():
    logout_user()
    return api_success(None, message="Signed out successfully.")
