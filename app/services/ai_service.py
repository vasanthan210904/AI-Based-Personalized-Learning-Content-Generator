"""Secure backend-only AI provider integration.

The default live provider is NVIDIA NIM (OpenAI-compatible chat completions,
running a DeepSeek model). Google Gemini, OpenAI, OpenRouter, Groq and local
OpenAI-compatible servers are supported as alternates. API keys never leave the
server. Failures are converted into friendly, non-leaky errors.
"""
from __future__ import annotations

import logging
import threading
import time

import requests
from flask import current_app

from ..utils.json_parse import JsonParseError, extract_json

logger = logging.getLogger(__name__)

# A broken/unreachable provider should not make every student wait for the full
# request timeout. After a timeout or provider-side 5xx we pause live calls for
# AI_FAILURE_COOLDOWN seconds and let the callers use labelled demo content.
_cooldown_lock = threading.Lock()
_cooldowns: dict[str, tuple[float, str]] = {}


def reset_ai_cooldowns() -> None:
    """Clear provider cooldowns (used by tests and after a config change)."""
    with _cooldown_lock:
        _cooldowns.clear()


class AIServiceError(Exception):
    """A clean, user-presentable AI failure."""

    def __init__(self, message: str, *, code: str = "ai_error", status: int = 502):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


class AIService:
    def __init__(self, config=None, provider: str | None = None, model: str | None = None):
        self.config = config or current_app.config
        self._custom_provider = provider
        self._custom_model = model

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------
    @property
    def provider(self) -> str:
        if self._custom_provider:
            return self._custom_provider.lower()
        return (self.config.get("AI_PROVIDER") or "groq").lower()

    @property
    def model(self) -> str:
        if self._custom_model:
            return self._custom_model
        return self.config.get("AI_MODEL") or "qwen/qwen3.8-27b"

    @property
    def api_key(self) -> str:
        return {
            "nvidia": self.config.get("NVIDIA_API_KEY") or self.config.get("AI_API_KEY", ""),
            "gemini": self.config.get("GEMINI_API_KEY") or self.config.get("AI_API_KEY", ""),
            "openai": self.config.get("OPENAI_API_KEY") or self.config.get("AI_API_KEY", ""),
            "openrouter": self.config.get("OPENROUTER_API_KEY") or self.config.get("OPENAI_API_KEY") or self.config.get("AI_API_KEY", ""),
            "groq": self.config.get("GROQ_API_KEY") or self.config.get("AI_API_KEY", ""),
        }.get(self.provider, self.config.get("AI_API_KEY", ""))

    @property
    def key_env_name(self) -> str:
        return {
            "nvidia": "NVIDIA_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "openai": "OPENAI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "groq": "GROQ_API_KEY",
        }.get(self.provider, "AI_API_KEY")

    @property
    def demo_mode_setting(self) -> str:
        return (self.config.get("AI_DEMO_MODE") or "auto").lower()

    def is_live_available(self) -> bool:
        if self.demo_mode_setting == "on":
            return False
        return bool(self.api_key)

    def status(self) -> dict:
        live = self.is_live_available()
        remaining = self.cooldown_remaining()
        degraded = live and remaining > 0
        if not live:
            state = "demo"
            label = "Demo mode · offline sample content"
        elif degraded:
            state = "fallback"
            label = f"Live AI temporarily unavailable · demo fallback for {remaining}s"
        else:
            state = "live"
            label = f"Live AI · {self._provider_label()}"
        return {
            "live": live,
            "degraded": degraded,
            "state": state,
            "cooldown_remaining": remaining,
            "mode": "live" if state == "live" else "demo_fallback" if degraded else "demo",
            "provider": self.provider,
            "model": self.model,
            "label": label,
            "provider_label": self._provider_label(),
        }

    def _cooldown_key(self) -> str:
        return f"{self.provider}:{self.model}:{self._base_url()}"

    def cooldown_remaining(self) -> int:
        """Seconds left before live calls are attempted again (0 when healthy)."""
        key = self._cooldown_key()
        with _cooldown_lock:
            entry = _cooldowns.get(key)
            if not entry:
                return 0
            until, _reason = entry
            remaining = until - time.monotonic()
            if remaining <= 0:
                _cooldowns.pop(key, None)
                return 0
            return int(remaining) + 1

    def _mark_unavailable(self, reason: str) -> None:
        try:
            seconds = max(1, int(self.config.get("AI_FAILURE_COOLDOWN", 300)))
        except (TypeError, ValueError):
            seconds = 300
        with _cooldown_lock:
            _cooldowns[self._cooldown_key()] = (
                time.monotonic() + seconds,
                reason,
            )
        logger.warning(
            "Pausing live AI calls for %ss after provider failure: %s", seconds, reason
        )

    def _mark_available(self) -> None:
        with _cooldown_lock:
            _cooldowns.pop(self._cooldown_key(), None)

    def _provider_label(self) -> str:
        labels = {
            "nvidia": "NVIDIA NIM",
            "gemini": "Google Gemini",
            "openai": "OpenAI",
            "openrouter": "OpenRouter",
            "groq": "Groq",
        }
        return labels.get(self.provider, self.provider.title())

    # ------------------------------------------------------------------
    # Public generation API
    # ------------------------------------------------------------------
    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int = 4000,
        temperature: float | None = None,
    ) -> dict:
        if not self.is_live_available():
            raise AIServiceError(
                f"Live AI is not configured. Add {self.key_env_name} to your .env file, "
                "or use demo mode.",
                code="ai_not_configured",
                status=503,
            )
        remaining = self.cooldown_remaining()
        if remaining > 0:
            raise AIServiceError(
                "The AI provider is temporarily unavailable after a recent failure. "
                f"Labelled demo content will be used. Live AI retries automatically in about {remaining} seconds.",
                code="ai_cooldown",
                status=503,
            )

        temperature = (
            self.config.get("AI_TEMPERATURE", 0.55) if temperature is None else temperature
        )
        primary_error = None
        try:
            raw = self._call_provider(system_prompt, user_prompt, max_tokens, temperature)
            try:
                return extract_json(raw)
            except JsonParseError:
                logger.warning("AI returned invalid JSON; attempting one repair retry.")
                repair_prompt = (
                    f"{user_prompt}\n\n"
                    "IMPORTANT: Your previous response was not valid JSON. "
                    "Return ONLY the JSON object, with no markdown fences, comments or extra text. "
                    f"Previous response started with: {raw[:1200]}"
                )
                raw_retry = self._call_provider(
                    system_prompt, repair_prompt, max_tokens, temperature
                )
                return extract_json(raw_retry)
        except AIServiceError as exc:
            logger.warning("Primary provider %s failed: %s", self.provider, exc)
            primary_error = exc
        except Exception as exc:
            logger.warning("Primary provider %s unexpected error: %s", self.provider, exc)
            primary_error = AIServiceError(str(exc), code="ai_error", status=502)

        # Failover to alternate free providers if auto-failover is enabled
        alternates = self._get_alternate_providers()
        for alt in alternates:
            try:
                logger.info("Failing over to alternate AI: %s (%s)", alt["provider"], alt["model"])
                raw_alt = self._call_alternate(alt, system_prompt, user_prompt, max_tokens, temperature)
                return extract_json(raw_alt)
            except Exception as alt_exc:
                logger.warning("Alternate AI %s failed: %s", alt["provider"], alt_exc)

        if primary_error:
            raise primary_error
        raise AIServiceError("AI generation failed across all providers.", code="ai_invalid_response", status=502)

    def _get_alternate_providers(self) -> list[dict]:
        """Returns alternate configured free providers for seamless failover."""
        if not self.config.get("AI_AUTO_FAILOVER", False):
            return []
        alts = []
        if self.provider != "groq" and self.config.get("GROQ_API_KEY"):
            alts.append({
                "provider": "groq",
                "model": "qwen/qwen3.8-27b",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": self.config["GROQ_API_KEY"],
            })
        if self.provider != "openrouter" and self.config.get("OPENROUTER_API_KEY"):
            alts.append({
                "provider": "openrouter",
                "model": "nvidia/nemotron-3.5-lightning:free",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": self.config["OPENROUTER_API_KEY"],
            })
        if self.provider != "gemini" and self.config.get("GEMINI_API_KEY"):
            alts.append({
                "provider": "gemini",
                "model": "gemma-4-26b-a4b-it",
                "base_url": "",
                "api_key": self.config["GEMINI_API_KEY"],
            })
        return alts

    def _call_alternate(
        self, alt: dict, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        if alt["provider"] == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{alt['model']}:generateContent?key={alt['api_key']}"
            payload = {
                "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
            }
            res = requests.post(url, json=payload, timeout=self._timeout())
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            url = f"{alt['base_url'].rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {alt['api_key']}",
                "Content-Type": "application/json",
            }
            if alt["provider"] == "openrouter":
                headers["HTTP-Referer"] = "http://localhost:5000"
                headers["X-Title"] = "LearnForge AI"
            payload = {
                "model": alt["model"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            res = requests.post(url, headers=headers, json=payload, timeout=self._timeout())
            data = res.json()
            msg = data["choices"][0]["message"]
            return (msg.get("content") or msg.get("reasoning") or "").strip()

    # ------------------------------------------------------------------
    # Provider calls
    # ------------------------------------------------------------------
    def _call_provider(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        if self.provider == "gemini":
            return self._call_gemini(system_prompt, user_prompt, max_tokens, temperature)
        return self._call_openai_compatible(
            system_prompt, user_prompt, max_tokens, temperature
        )

    def _timeout(self) -> tuple[int, float]:
        return (10, float(self.config.get("AI_TIMEOUT", 90)))

    def _call_gemini(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json",
                # Gemini 3.x models otherwise spend the output budget on hidden
                # "thinking" tokens, which can leave no visible JSON behind.
                "thinkingConfig": {
                    "thinkingBudget": int(
                        self.config.get("AI_GEMINI_THINKING_BUDGET", 0)
                    )
                },
            },
        }
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        response = self._post(url, headers, payload)
        try:
            data = response.json()
        except ValueError:
            raise self._invalid_provider_response() from None

        if data.get("promptFeedback", {}).get("blockReason"):
            raise AIServiceError(
                "The AI declined to answer this request. Try rephrasing the topic.",
                code="ai_blocked",
                status=422,
            )

        candidates = data.get("candidates") or []
        if not candidates:
            raise self._invalid_provider_response()
        candidate = candidates[0]
        finish_reason = candidate.get("finishReason")
        if finish_reason in {"SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT"}:
            raise AIServiceError(
                "The AI declined to generate this content. Try a different topic.",
                code="ai_blocked",
                status=422,
            )
        parts = (candidate.get("content") or {}).get("parts") or []
        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            raise self._invalid_provider_response(
                "The AI returned an empty response. Please try again."
            )
        return text

    def _call_openai_compatible(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        base_url = self._base_url()
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "http://localhost:5000"
            headers["X-Title"] = "LearnForge AI"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "top_p": float(self.config.get("AI_TOP_P", 0.95)),
            "max_tokens": max_tokens,
            "stream": False,
            "response_format": {"type": "json_object"},
        }

        response = self._post(url, headers, payload, allow_format_retry=True, retry_headers=headers, retry_payload=payload)
        try:
            data = response.json()
        except ValueError:
            raise self._invalid_provider_response() from None

        try:
            msg = data["choices"][0]["message"]
            text = (msg.get("content") or "").strip()
            if not text and msg.get("reasoning"):
                text = msg.get("reasoning").strip()
        except (KeyError, IndexError, TypeError):
            raise self._invalid_provider_response() from None
        if not text:
            raise self._invalid_provider_response(
                "The AI returned an empty response. Please try again."
            )
        return text

    def _base_url(self) -> str:
        configured = (self.config.get("AI_BASE_URL") or "").rstrip("/")
        if configured:
            return configured
        defaults = {
            "nvidia": "https://integrate.api.nvidia.com/v1",
            "openai": "https://api.openai.com/v1",
            "openrouter": "https://openrouter.ai/api/v1",
            "groq": "https://api.groq.com/openai/v1",
        }
        return defaults.get(self.provider, "https://api.openai.com/v1")

    def _post(
        self,
        url: str,
        headers: dict,
        payload: dict,
        *,
        allow_format_retry: bool = False,
        retry_headers: dict | None = None,
        retry_payload: dict | None = None,
    ) -> requests.Response:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self._timeout())
        except requests.Timeout:
            logger.warning("AI request timed out after %.0fs", self.config.get("AI_TIMEOUT", 90))
            self._mark_unavailable("The AI provider timed out.")
            raise AIServiceError(
                "The AI took too long to respond. Please try again in a moment.",
                code="ai_timeout",
            ) from None
        except requests.RequestException as exc:
            logger.warning("AI network error: %s", exc)
            self._mark_unavailable("The AI provider could not be reached.")
            raise AIServiceError(
                "Could not reach the AI service. Check your internet connection and try again.",
                code="ai_network",
            ) from None

        if response.status_code == 401 or response.status_code == 403:
            logger.warning("AI auth failure (%s)", response.status_code)
            raise AIServiceError(
                f"The AI provider rejected the API key. Check {self.key_env_name} in your .env file.",
                code="ai_auth",
            )
        if response.status_code == 429:
            logger.warning("AI rate limit hit")
            self._mark_unavailable("The AI provider rate limit was reached.")
            raise AIServiceError(
                "The AI provider's rate limit was reached. Please wait a minute and try again.",
                code="ai_rate_limit",
            )
        if response.status_code == 400 and allow_format_retry and retry_payload is not None:
            # Some OpenAI-compatible servers do not support response_format.
            retry_payload = dict(retry_payload)
            retry_payload.pop("response_format", None)
            logger.info("Retrying AI request without response_format.")
            return self._post(url, retry_headers or headers, retry_payload)
        if 400 <= response.status_code < 500:
            logger.warning("AI provider rejected request: HTTP %s", response.status_code)
            raise AIServiceError(
                "The AI provider rejected the request. Check AI_MODEL and AI_BASE_URL settings.",
                code="ai_bad_request",
            )
        if response.status_code >= 500:
            logger.warning("AI provider server error: HTTP %s", response.status_code)
            self._mark_unavailable(f"The AI provider returned HTTP {response.status_code}.")
            raise AIServiceError(
                "The AI provider is temporarily unavailable. Please try again shortly.",
                code="ai_unavailable",
            )
        if not response.ok:
            raise AIServiceError(
                "The AI service returned an unexpected response.",
                code="ai_bad_response",
            )
        self._mark_available()
        return response

    def _invalid_provider_response(
        self, message: str = "The AI returned an unexpected response. Please try again."
    ) -> AIServiceError:
        return AIServiceError(message, code="ai_bad_response")


def get_ai_service() -> AIService:
    return AIService()
