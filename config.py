"""Application configuration loaded from environment variables."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"

load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


_PROVIDER = os.environ.get("AI_PROVIDER", "groq").strip().lower()
_DEFAULT_MODEL = {
    "groq": "qwen/qwen3.8-27b",
    "gemini": "gemma-4-26b-a4b-it",
    "nvidia": "deepseek-ai/deepseek-v4.1-flash",
    "openrouter": "nvidia/nemotron-3.5-lightning:free",
    "openai": "gpt-4o-mini",
}.get(_PROVIDER, "qwen/qwen3.8-27b")
_DEFAULT_BASE_URL = {
    "nvidia": "https://integrate.api.nvidia.com/v1",
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "groq": "https://api.groq.com/openai/v1",
}.get(_PROVIDER, "")

# Provider-specific keys
_NVIDIA_API_KEY = (
    os.environ.get("NVIDIA_API_KEY", "").strip()
    or os.environ.get("AI_API_KEY", "").strip()
)
_GEMINI_API_KEY = (
    os.environ.get("GEMINI_API_KEY", "").strip()
    or os.environ.get("AI_API_KEY", "").strip()
)
_OPENAI_API_KEY = (
    os.environ.get("OPENAI_API_KEY", "").strip()
    or os.environ.get("AI_API_KEY", "").strip()
)
_GROQ_API_KEY = (
    os.environ.get("GROQ_API_KEY", "").strip()
    or os.environ.get("OPENAI_API_KEY", "").strip()
    or os.environ.get("AI_API_KEY", "").strip()
)
_OPENROUTER_API_KEY = (
    os.environ.get("OPENROUTER_API_KEY", "").strip()
    or os.environ.get("OPENAI_API_KEY", "").strip()
    or os.environ.get("AI_API_KEY", "").strip()
)
_HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", "").strip()

_PROVIDER_KEY = {
    "nvidia": _NVIDIA_API_KEY,
    "gemini": _GEMINI_API_KEY,
    "openai": _OPENAI_API_KEY,
    "openrouter": _OPENROUTER_API_KEY,
    "groq": _GROQ_API_KEY,
}.get(_PROVIDER, os.environ.get("AI_API_KEY", "").strip())

_AI_MODEL = os.environ.get("AI_MODEL", "").strip()
if _PROVIDER == "nvidia":
    _AI_MODEL = os.environ.get("NVIDIA_MODEL", "").strip() or _AI_MODEL
_AI_MODEL = _AI_MODEL or _DEFAULT_MODEL

_AI_BASE_URL = os.environ.get("AI_BASE_URL", "").strip().rstrip("/")
if _PROVIDER == "nvidia":
    _AI_BASE_URL = (
        os.environ.get("NVIDIA_BASE_URL", "").strip().rstrip("/") or _AI_BASE_URL
    )
_AI_BASE_URL = _AI_BASE_URL or _DEFAULT_BASE_URL


class Config:
    """Default development configuration."""

    # --- Core -------------------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "learnforge-dev-secret-change-me")
    APP_NAME = "LearnForge"
    APP_TAGLINE = "AI-Powered Personalized Learning"
    PROJECT_TITLE = "AI-Based Personalized Learning Content Generator"
    _is_vercel = os.environ.get("VERCEL") in ("1", "true", "True") or bool(os.environ.get("VERCEL_ENV"))
    _DEFAULT_DB = "/tmp/app.db" if _is_vercel else (INSTANCE_DIR / "app.db").as_posix()
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{_DEFAULT_DB}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUTO_INIT_DB = True
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024

    # --- Sessions / forms -------------------------------------------------
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", False)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # --- Seed accounts ----------------------------------------------------
    ADMIN_NAME = os.environ.get("ADMIN_NAME", "Platform Administrator")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@learnforge.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@12345")

    # --- AI service -------------------------------------------------------
    AI_PROVIDER = _PROVIDER
    AI_API_KEY = _PROVIDER_KEY
    AI_MODEL = _AI_MODEL
    AI_BASE_URL = _AI_BASE_URL
    NVIDIA_API_KEY = _NVIDIA_API_KEY
    NVIDIA_BASE_URL = os.environ.get(
        "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
    ).strip().rstrip("/")
    NVIDIA_MODEL = os.environ.get(
        "NVIDIA_MODEL", "deepseek-ai/deepseek-v4.1-flash"
    ).strip()
    GROQ_API_KEY = _GROQ_API_KEY
    GEMINI_API_KEY = _GEMINI_API_KEY
    OPENROUTER_API_KEY = _OPENROUTER_API_KEY
    HUGGINGFACE_API_KEY = _HUGGINGFACE_API_KEY
    AI_TIMEOUT = _env_float("AI_TIMEOUT", 120.0)
    # After a timeout/server error, skip live calls for this many seconds and
    # serve clearly labelled demo content immediately instead of hanging again.
    AI_FAILURE_COOLDOWN = _env_int("AI_FAILURE_COOLDOWN", 300)
    AI_DEMO_MODE = os.environ.get("AI_DEMO_MODE", "auto").strip().lower()  # auto | on | off
    AI_MAX_TOKENS_CONTENT = _env_int("AI_MAX_TOKENS_CONTENT", 6000)
    AI_MAX_TOKENS_QUIZ = _env_int("AI_MAX_TOKENS_QUIZ", 4000)
    AI_MAX_TOKENS_PLAN = _env_int("AI_MAX_TOKENS_PLAN", 4000)
    AI_TEMPERATURE = _env_float("AI_TEMPERATURE", 0.55)
    AI_TOP_P = _env_float("AI_TOP_P", 0.95)
    AI_GEMINI_THINKING_BUDGET = _env_int("AI_GEMINI_THINKING_BUDGET", 0)

    # --- Rate limiting ----------------------------------------------------
    RATE_LIMIT_ENABLED = _env_bool("RATE_LIMIT_ENABLED", True)
    RATE_LIMIT_AI = _env_int("RATE_LIMIT_AI", 8)
    RATE_LIMIT_AI_WINDOW = _env_int("RATE_LIMIT_AI_WINDOW", 600)
    RATE_LIMIT_LOGIN = _env_int("RATE_LIMIT_LOGIN", 12)
    RATE_LIMIT_LOGIN_WINDOW = _env_int("RATE_LIMIT_LOGIN_WINDOW", 900)


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    AUTO_INIT_DB = False
    RATE_LIMIT_ENABLED = False
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    ADMIN_EMAIL = "admin@learnforge.com"
    ADMIN_PASSWORD = "Admin@12345"
