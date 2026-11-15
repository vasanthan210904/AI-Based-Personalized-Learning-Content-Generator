# LearnForge — AI-Based Personalized Learning Content Generator

LearnForge is a Flask + SQLite college mini-project that turns a subject and topic into
personalized study material, quizzes and a day-by-day study plan. Students get a private
workspace; administrators manage the subject/topic catalog and user accounts.

The default live provider is **NVIDIA NIM** (`deepseek-ai/deepseek-v4.1-flash`). If live AI is
unavailable, the app keeps working with **clearly labelled demo content** instead of failing or
inventing facts silently.

## Features

### Student workspace
- Email/password accounts with Flask-Login and role-based access.
- Learning preferences: course, year, level, language, style and goals.
- Content studio with 8 formats: Detailed Notes, Short Notes, Summary, Bullet Points,
  Step-by-Step Guide, Real-World Examples, Exam Preparation and FAQ.
- 15-section generated material with objectives, definitions, examples, pros/cons, revision tips
  and FAQs.
- Quiz studio with hidden answers, server-side evaluation, explanations and history.
- Study planner with daily tasks, progress tracking and `.ics` calendar export.
- Progress page with Chart.js coverage and quiz-mastery charts.
- History, saved library with private notes, flashcards with review states, and revocable
  read-only share links.
- PDF and Markdown export, achievements panel and dark mode.

### Administrator console
- Database-backed dashboard statistics (no hardcoded numbers).
- User listing, role badges and account activity.
- Subject/topic CRUD with safeguards against deleting content in use.
- REST endpoints for every admin action.

## Tech stack

| Layer | Choice |
| --- | --- |
| Backend | Python 3.11+, Flask 3.1, Flask-SQLAlchemy, Flask-Login, Flask-WTF |
| Database | SQLite (`instance/app.db`) |
| AI | NVIDIA NIM chat completions; Gemini/OpenAI/OpenRouter/Groq supported |
| Reports | ReportLab (PDF), Markdown exporter, ICS calendar |
| Frontend | Jinja2, Bootstrap 5, Bootstrap Icons, Chart.js, vanilla JavaScript |

## Quick start (Windows PowerShell)

```powershell
cd AI-Personalized-Learning
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and add NVIDIA_API_KEY (or leave it empty for demo mode)
.\venv\Scripts\python.exe run.py
```

Open <http://127.0.0.1:5000>. The database, admin account, subjects and topics are created and
seeded automatically on the first start. To add a populated demo student later:

```powershell
.\venv\Scripts\python.exe -m flask --app run.py seed-demo
```

## Configuration

All secrets stay in `.env`; keys are only read on the server and are never exposed to templates
or JavaScript.

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Flask session signing key |
| `AI_PROVIDER` | `nvidia` (default), `gemini`, `openai`, `openrouter`, `groq` |
| `NVIDIA_API_KEY` | NVIDIA NIM key; leave empty for demo mode |
| `NVIDIA_MODEL` | Default `deepseek-ai/deepseek-v4.1-flash` |
| `NVIDIA_BASE_URL` | Default `https://integrate.api.nvidia.com/v1` |
| `AI_TIMEOUT` | Provider read timeout in seconds (default 120) |
| `AI_FAILURE_COOLDOWN` | Seconds to skip live calls after a timeout/5xx (default 300) |
| `AI_DEMO_MODE` | `auto` (fallback), `on` (always demo), `off` (require live AI) |
| `AI_TEMPERATURE`, `AI_TOP_P` | Generation sampling settings |
| `RATE_LIMIT_*` | In-process rate limiting for AI and login actions |
| `SESSION_COOKIE_SECURE` | Set `true` only behind HTTPS |

### AI modes in the UI

- **Live AI** — the provider key is configured and no failure is active.
- **Demo fallback** — a live call timed out or the provider returned a 5xx. The request still
  completes with clearly labelled offline content, and the UI shows how long until retry.
- **Demo mode** — no key is configured, or `AI_DEMO_MODE=on`. The app only serves the offline
  demo library.

The circuit breaker (`AI_FAILURE_COOLDOWN`) prevents every student from waiting for the full
timeout while a provider is down. It is stored in process memory, so it applies to a single
Flask worker; the development server is single-worker by design.

## Generator form behaviour

- Choosing a subject automatically selects its first topic, so the form can never get stuck on a
  disabled topic dropdown.
- Missing fields are reported inline next to the field and in a precise toast message
  (for example “Please choose a content type to continue.”) instead of one generic warning.
- The first invalid control is focused, and errors clear as soon as the field changes.
- The submit button and full-screen overlay show progress while content is generated.

## Tests

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

The suite uses an in-memory SQLite database and never calls a real AI provider. It covers:

- generator page rendering and the absence of the old generic validation message,
- missing subject/topic/content-type API errors with field names,
- demo generation, database persistence and viewer rendering,
- login protection for the generation API,
- provider timeout handling, labelled demo fallback, and the circuit breaker skipping repeated
  provider calls,
- provider 5xx handling and cooldown state.

JavaScript is dependency-free and has no Node.js build step. Validate browser-side changes with
the DevTools console and the app's live flows. The latest bug-fix evidence is recorded in
`docs/verification.md`.

## REST API

All JSON endpoints use a `{success, data}` envelope; errors return
`{success: false, error: {code, message, fields?}}`. Session authentication is required, and
state-changing calls from JavaScript send the CSRF token in `X-CSRFToken`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/generate-content` | Generate learning material |
| `POST` | `/api/generate-quiz` | Generate a quiz |
| `POST` | `/api/submit-quiz` | Evaluate quiz answers |
| `POST` | `/api/generate-study-plan` | Build a study plan |
| `GET` | `/api/progress` | Progress summary |
| `GET/PUT` | `/api/profile` | Read/update preferences |
| `GET/POST/DELETE` | `/api/bookmarks/...` | Saved library |
| `GET/POST/DELETE` | `/api/learning-content/<id>/share` | Share links |
| `GET/POST` | `/api/flashcards/...` | Flashcard decks and reviews |
| `GET/POST/PUT/DELETE` | `/api/admin/...` | Admin catalog and stats |

## Project structure

```text
AI-Personalized-Learning/
├── app/
│   ├── routes/          Flask blueprints (auth, student, learning, quiz, study, admin, ...)
│   ├── services/        AI provider, prompts, generators, PDF/Markdown export
│   ├── static/          CSS, JavaScript and images
│   ├── templates/       Jinja2 pages and shared macros
│   ├── utils/           validation, pagination, rate limiting, serializers
│   ├── models.py        SQLAlchemy models
│   ├── seed.py          First-run catalog and optional demo activity
│   └── __init__.py      App factory, error handlers and security headers
├── tests/               Pytest suite
├── config.py            Environment-driven configuration
├── run.py               Development entry point
├── requirements.txt
└── .env.example
```

## Limitations

- SQLite and the in-process rate limiter/circuit breaker target a single-worker development
  deployment. Use Redis or a shared store before running multiple workers.
- Demo mode is English-only. Curated demo quizzes exist for the built-in demo topics; other quiz
  topics require live AI.
- Generated material is a study aid, not a substitute for the course textbook. The UI says so.
- This project uses Flask's development server; use a production WSGI server and HTTPS for any
  real deployment.
