# Verification log — generator validation and AI fallback

Date: 15 November 2026

## Reported problem

Submitting the Content Studio form showed the generic message:

> Choose a subject, topic and content type.

The topic dropdown stays disabled until a subject is selected, so a student who picked only a
subject could not tell which field was actually missing. The message also appeared after a valid
selection if the browser did not send the expected value.

## Root causes

1. The topic `<select>` remains disabled while no subject is selected, so the form could not be
   completed in the expected order without a visible hint.
2. Validation used a single generic toast instead of field-specific messages.
3. The old JavaScript still contained the generic message, so any missing value produced the same
   wording regardless of the actual problem.
4. A live provider timeout could make every generation wait for the full 90-second read timeout.
5. The progress page used `summary.achievements.items`; Jinja resolved `.items` to the built-in
   `dict.items` method, producing a 500 error.

## Changes made

### Generator form
- Selecting a subject automatically selects its first topic.
- Inline errors are rendered next to Subject, Topic and Content type.
- Toast text names the exact missing field(s), e.g. “Please choose a content type to continue.”
- The first invalid control is focused.
- Errors clear when the field changes.
- The disabled topic is not reported as a separate error while the subject is still empty.

### AI reliability
- Added `AI_FAILURE_COOLDOWN` (default 300 seconds).
- A provider timeout, network error, 429 or 5xx opens a per-provider circuit breaker.
- During the cooldown, generation skips the provider and immediately uses clearly labelled
  `demo_fallback` content.
- The status panel shows Live AI, Demo fallback (with retry countdown) or Demo mode.
- Provider authentication failures and configuration errors are not masked as demo content.

### Progress page
- Changed to `summary.achievements["items"]` so Jinja returns the achievement list instead of the
  dict method.

## Test evidence

```text
28 passed, 2 warnings in 12.10s
```

Automated coverage added in `tests/`:

- `test_generator.py` — page rendering, no generic dead-end message, missing subject/topic/type
  field errors, demo generation, database persistence, viewer, PDF and Markdown export, login
  protection.
- `test_ai_service.py` — live status, timeout circuit breaker, fast `ai_cooldown` rejection,
  5xx handling, labelled demo fallback and provider call suppression.
- `test_pages.py` — smoke tests for all student pages, admin pages, and role-based access.

Browser verification performed with the in-app browser:

1. Submitting with no subject showed only “Choose a subject.” inline and
   “Please choose a subject to continue.” as the toast; focus moved to the subject field.
2. Selecting a subject auto-selected the first topic.
3. Generating with no content type showed “Choose a content type.” inline and the precise toast.
4. A valid request sent `POST /api/generate-content` with subject, topic, type, level, style and
   language.
5. Live NVIDIA generation timed out at 90 seconds and the API returned HTTP 201 with
   `ai_mode=demo_fallback`; the viewer showed a clear Demo Fallback notice and saved material.
6. The next request returned immediately with `ai_cooldown` and 201 demo-fallback content; the
   provider was not called again.
7. The generator page then displayed “Demo fallback” and a retry countdown.
8. Dashboard, history, saved library, flashcards, progress, study planner, quiz history and all
   admin pages rendered HTTP 200 with no browser console errors.

## Live AI limitation

The configured NVIDIA model (`deepseek-ai/deepseek-v4.1-flash`) did not return a chat completion
during verification; the request timed out after 90 seconds. The key and `/v1/models` endpoint
were valid. Live content quality therefore could not be verified in this session. The app
correctly labels and saves demo fallback content while the provider is unavailable. Changing the
production model requires the project owner's approval.

## Related files

- `app/services/ai_service.py`
- `config.py`
- `app/services/content_generator.py`
- `app/static/js/generator.js`
- `app/templates/learning/generator.html`
- `app/templates/layouts/_topbar.html`
- `app/templates/layouts/auth.html`
- `app/templates/quiz/generator.html`
- `app/templates/study_plan/planner.html`
- `app/templates/student/preferences.html`
- `app/templates/progress/index.html`
- `tests/conftest.py`, `tests/test_generator.py`, `tests/test_ai_service.py`, `tests/test_pages.py`
- `README.md`, `.env.example`
