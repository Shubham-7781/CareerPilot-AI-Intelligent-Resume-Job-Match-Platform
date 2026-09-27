# CareerPilot — AI Resume Analyzer & Job Match Platform

A full-stack application that parses resumes (PDF/DOCX), scores them with an
AI-powered ATS analyzer, generates a tailored, role-specific rewrite of the
resume as a downloadable PDF, and surfaces live job listings.

## Architecture

```
careerpilot/
├── backend/                 FastAPI REST API
│   ├── app/
│   │   ├── api/routes/      auth, resumes, jobs
│   │   ├── core/            config, security (JWT + bcrypt)
│   │   ├── db/               SQLAlchemy session
│   │   ├── models/           User, Resume, Analysis
│   │   ├── schemas/          Pydantic request/response models
│   │   └── services/         resume parsing, AI analyzer (Gemini + deterministic
│   │                         fallback), resume tailoring, semantic skill matching,
│   │                         PDF report generation, job search, file validation,
│   │                         email sending, Redis-backed rate limiting
│   ├── alembic/               DB migrations
│   ├── tests/                 pytest suite (27 tests)
│   └── Dockerfile
├── frontend/                 React (Vite) SPA
│   ├── src/
│   │   ├── api/               axios client with JWT refresh interceptor
│   │   ├── context/           auth state (session-only — see note below)
│   │   ├── pages/             Home, Login, Signup, VerifyEmail, ForgotPassword,
│   │   │                      ResetPassword, Dashboard, Upload, ResumeDetail, JobSearch
│   │   └── components/
│   └── Dockerfile             nginx-served production build
├── .github/workflows/ci.yml  GitHub Actions: backend tests + frontend build
└── docker-compose.yml        Postgres + Redis + API + frontend
```

**Stack:** FastAPI, PostgreSQL, SQLAlchemy + Alembic, Redis, JWT auth
(bcrypt-hashed passwords), Google Gemini (resume analysis + tailoring),
sentence-transformers (local semantic skill matching), ReportLab (PDF
generation), React 18 + Vite, Docker Compose, pytest, GitHub Actions CI.

## Core features

- **Auth**: signup/login with hashed passwords + JWT access/refresh tokens,
  email verification, password reset (forgot-password never leaks whether
  an email is registered).
- **Resume upload**: PDF/DOCX, validated by extension, size, and magic-byte
  signature (a renamed executable can't slip through as a "resume").
- **Resume parsing**: consolidated single pipeline (spaCy + pdfplumber/
  python-docx) extracting contact info and structured sections.
- **AI resume analysis**: if `GEMINI_API_KEY` is set, Gemini scores the
  resume (0-100), gives an overall assessment, strengths/improvements,
  section-by-section feedback, bullet-point rewrites, course
  recommendations, and — if a job description is supplied — a job-match
  percentage and gap analysis. Every skill claim Gemini makes is
  cross-checked locally against the actual resume text using semantic
  similarity (sentence-transformers) before being trusted, so the analysis
  can't casually credit a skill the resume doesn't support.
- **Deterministic fallback engine**: if no API key is configured (or the
  Gemini call fails), analysis still works — keyword/skill-taxonomy
  matching (spaCy PhraseMatcher, ~45 skills with synonym mapping) plus
  section-completeness and formatting heuristics. Every response reports
  which `engine` produced it (`"gemini"` or `"heuristic"`).
- **Tailored resume generation**: rewrites the candidate's resume for a
  specific job description using only facts already present in the
  original (never invents employers, titles, or numbers), downloadable as
  a PDF. Requires `GEMINI_API_KEY`; returns a clear `503` if not
  configured, rather than failing silently.
- **PDF analysis report**: downloadable PDF summary of any past analysis.
- **Job search**: Adzuna API integration.
- **Rate limiting**: Redis-backed sliding window, per-IP, with automatic
  in-memory fallback if Redis is unreachable.

## A note on login behavior

Auth tokens are stored in `sessionStorage`, not `localStorage`. This is
intentional: it means closing the browser/tab ends the session, and the
person has to log in again next time they open the site — rather than the
app silently picking back up where they left off indefinitely. Refreshing
the page within the same tab keeps you logged in (normal SPA behavior);
closing the tab or browser does not.

## Running locally (Docker)

```bash
cp backend/.env.example backend/.env
# edit backend/.env: set a real SECRET_KEY, and (optionally) GEMINI_API_KEY / ADZUNA credentials

docker compose up --build
```

- API: http://localhost:8000/api/docs (interactive Swagger docs)
- Frontend: http://localhost

## Running locally (without Docker)

See the step-by-step terminal walkthrough further down, or the short
version:

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env   # set DATABASE_URL, SECRET_KEY, etc.
alembic revision --autogenerate -m "init"
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Running tests

```bash
cd backend
pytest -v
```

27 tests covering: signup/login/duplicate-email/password-hashing, full
email-verification and password-reset flows (including expired/invalid
token rejection), resume upload validation (extension, size, magic bytes),
per-owner resume access isolation, analysis on both the fallback and
keyword-matching paths, tailor-without-API-key behavior, and rate-limiter
correctness. Tests run with a generous in-test rate limit override and a
temp upload directory so they're independent of Docker/production paths.

## Getting API keys (both free)

- **Gemini** (AI analysis + tailoring): https://aistudio.google.com/apikey
  — without it, the app automatically falls back to the deterministic
  keyword-matching engine; nothing breaks, you just get less-rich analysis.
- **Adzuna** (job search): https://developer.adzuna.com/ — without it, job
  search returns a clear `503` rather than failing silently.

## CI/CD

`.github/workflows/ci.yml` runs on every push/PR to `main`:
- **backend-tests**: spins up real Postgres + Redis service containers,
  installs dependencies, downloads the spaCy model, and runs the full
  pytest suite. No `GEMINI_API_KEY` is set in CI on purpose — the suite
  must (and does) pass entirely on the deterministic fallback engine, since
  a test suite should never depend on a live third-party API call.
- **frontend-build**: installs and builds the React app.

If you fork/push this to your own GitHub repo, the workflow runs
automatically — no extra setup needed beyond having the code in the repo.

## Known limitations / good "next steps" to mention in an interview

- No admin dashboard for platform-wide usage stats.
- Resume skill-extraction (fallback engine) covers a curated ~45-skill
  taxonomy; the Gemini path is far more general but costs an API call.
- `datetime.utcnow()` is used in a few places (flagged as deprecated by
  Python, not yet removed) — a clean follow-up would be migrating to
  timezone-aware `datetime.now(UTC)` throughout.
