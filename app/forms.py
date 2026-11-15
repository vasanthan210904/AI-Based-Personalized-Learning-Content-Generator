"""WTForms used by server-rendered pages and reused by the JSON API."""
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    EmailField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError

from .constants import LANGUAGES, LEARNING_LEVELS, LEARNING_STYLES, YEARS
from .models import User
from .utils.validation import password_problem


class RegistrationForm(FlaskForm):
    name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=3, max=120, message="Enter your full name.")],
        render_kw={"placeholder": "e.g. Asha Verma", "autocomplete": "name"},
    )
    email = EmailField(
        "Email address",
        validators=[DataRequired(), Email(message="Enter a valid email address."), Length(max=255)],
        render_kw={"placeholder": "you@example.com", "autocomplete": "email"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)],
        render_kw={"placeholder": "At least 8 characters", "autocomplete": "new-password"},
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords do not match."),
        ],
        render_kw={"placeholder": "Repeat your password", "autocomplete": "new-password"},
    )
    course = StringField(
        "Course",
        validators=[DataRequired(), Length(min=2, max=120)],
        render_kw={"placeholder": "e.g. B.Tech Computer Science"},
    )
    department = StringField(
        "Department",
        validators=[DataRequired(), Length(min=2, max=120)],
        render_kw={"placeholder": "e.g. Computer Science & Engineering"},
    )
    year = SelectField(
        "Year of study",
        choices=[(year, year) for year in YEARS],
        validators=[DataRequired()],
    )
    submit = SubmitField("Create my account")

    def validate_email(self, field):
        email = (field.data or "").strip().lower()
        if User.query.filter_by(email=email).first():
            raise ValidationError("An account with this email already exists.")

    def validate_password(self, field):
        problem = password_problem(field.data or "")
        if problem:
            raise ValidationError(problem)


class LoginForm(FlaskForm):
    email = EmailField(
        "Email address",
        validators=[DataRequired(), Email(message="Enter a valid email address.")],
        render_kw={"placeholder": "you@example.com", "autocomplete": "email"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()],
        render_kw={"placeholder": "Your password", "autocomplete": "current-password"},
    )
    remember = BooleanField("Keep me signed in")
    submit = SubmitField("Sign in")


class ProfileForm(FlaskForm):
    name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=3, max=120)],
        render_kw={"autocomplete": "name"},
    )
    course = StringField(
        "Course",
        validators=[DataRequired(), Length(min=2, max=120)],
    )
    department = StringField(
        "Department",
        validators=[DataRequired(), Length(min=2, max=120)],
    )
    year = SelectField(
        "Year of study",
        choices=[(year, year) for year in YEARS],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save profile")


class PreferencesForm(FlaskForm):
    learning_level = SelectField(
        "Current learning level",
        choices=[(level, level) for level in LEARNING_LEVELS],
        validators=[DataRequired()],
    )
    learning_style = SelectField(
        "Preferred learning style",
        choices=[(style, style) for style in LEARNING_STYLES],
        validators=[DataRequired()],
    )
    preferred_language = SelectField(
        "Preferred language",
        choices=[(language, language) for language in LANGUAGES],
        validators=[DataRequired()],
    )
    learning_goals = TextAreaField(
        "Learning goals",
        validators=[Optional(), Length(max=1000)],
        render_kw={
            "rows": 4,
            "placeholder": "e.g. Build a strong foundation in Python and score 85%+ in my DBMS exam.",
        },
    )
    interested_subjects = SelectMultipleField(
        "Interested subjects",
        choices=[],
        validators=[DataRequired(message="Choose at least one subject.")],
    )
    submit = SubmitField("Save preferences")
