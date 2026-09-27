# 🧭 CareerPilot — AI Resume Analyzer & Job Match Platform

Upload a resume, get it scored like an ATS would score it, rewrite it for a
specific job description, and pull live job listings that match your
skills — all from one app.

This is a real client–server application: a **FastAPI backend** with
authentication, persistence, and an AI-backed analysis pipeline, and a
**React frontend** — the kind of architecture you'd actually deploy, not
just demo locally.

---

## ✨ Features

| Area | What it does |
|---|---|
| **Auth** | Email/password signup + JWT access/refresh tokens, email verification, and password reset that never leaks whether an email is registered. |
| **Resume upload** | PDF/DOCX, validated by extension, size cap, and magic-byte signature — a renamed executable can't slip through as a "resume". |
| **Resume parsing** | Single consolidated pipeline (spaCy + pdfplumber/python-docx) extracting contact info and structured sections. |
| **AI resume analysis** | Gemini scores the resume 0–100, with an overall assessment, strengths/improvements, section-by-section feedback, bullet-point rewrites, and course recommendations. |
| **Skill-claim verification** | Every skill Gemini credits is cross-checked locally against the actual resume text with sentence-transformer similarity before it's trusted. |
| **Deterministic fallback engine** | No `GEMINI_API_KEY`? Analysis still runs — spaCy PhraseMatcher against a ~45-skill taxonomy plus section-completeness/formatting heuristics. Every response reports which `engine` produced it (`"gemini"` or `"heuristic"`). |
| **Job-match & gap analysis** | Supply a job description alongside the resume and get a match percentage plus a skill-gap breakdown. |
| **Tailored resume rewrite** | Rewrites the resume for a target job description using only facts already present in the original (never invents employers, titles, or numbers), downloadable as a PDF. |
| **PDF reports** | Any past analysis can be downloaded as a formatted PDF summary. |
| **Job search** | Live listings via the Adzuna API. |
| **Hardening** | Redis-backed sliding-window rate limiting per IP (with automatic in-memory fallback if Redis is down), file-size/type/count limits, structured error handling. |
| **Tests + CI** | 27-test pytest suite (auth, verification/reset flows, upload validation, tenant isolation, both analysis engines) run automatically via GitHub Actions on every push. |
| **Containerized** | One `docker compose up` runs Postgres + Redis + API + frontend, all with health checks. |

---

## 🏗️ Architecture

```
┌──────────────────┐        HTTPS/JSON               ┌───────────────────────┐
│   React SPA       │ ───────────────────────────────▶│   FastAPI backend      │
│ (Vite, nginx-served)│◀─────────────────────────────  │                        │
└──────────────────┘        JWT bearer auth           │  ┌──────────────────┐  │
                                                        │  │ Auth (JWT +      │  │
                                                        │  │  email verify/   │  │
                                                        │  │  password reset) │  │
                                                        │  ├──────────────────┤  │
                                                        │  │ Resumes API      │  │
                                                        │  │  → parse         │  │
                                                        │  │  → AI analyze    │  │
                                                        │  │  → tailor        │  │
                                                        │  │  → PDF report    │  │
                                                        │  ├──────────────────┤  │
                                                        │  │ Jobs API         │  │
                                                        │  │  → Adzuna search │  │
                                                        │  └──────────────────┘  │
                                                        └──────────┬─────────────┘
                                                                   │
                                 ┌─────────────────┬───────────────┼───────────────┐
                                 ▼                 ▼               ▼               ▼
                          PostgreSQL         Redis (rate      Gemini API     Adzuna API
                       (users, resumes,       limiting)     (analysis +      (job listings)
                          analyses)                          tailoring)
```

**Why these choices, for anyone asking in an interview:**
- **FastAPI** — async-native, so file upload handling and calls out to
  Gemini/Adzuna don't block the server, plus free OpenAPI docs at
  `/api/docs`.
- **PostgreSQL + Alembic** — real migrations instead of `create_all()`, so
  schema changes are tracked and reversible like they'd need to be in
  production.
- **Redis-backed rate limiting with an in-memory fallback** — protects
  the API and the (metered) Gemini/Adzuna calls behind it, but a Redis
  outage degrades to in-process limiting instead of taking the app down.
- **Gemini for generation, sentence-transformers for verification** — the
  expensive/paid step (rich analysis + rewriting) is optional and
  swappable; the free local model's only job is to fact-check the paid
  model's skill claims against the resume text, so the app is never
  trusting an LLM's claims about the candidate unverified.
- **Deterministic fallback engine** — the app has to be honestly
  demonstrable without an API key: if `GEMINI_API_KEY` is unset (or the
  call fails), a keyword/skill-taxonomy engine takes over and the response
  says so via `engine: "heuristic"`, rather than failing silently.
- **JWT in `sessionStorage`, not `localStorage`** — closing the browser/tab
  ends the session and requires logging in again; refreshing the page
  within the same tab keeps you logged in. A deliberate trade-off of
  convenience for a tighter session lifetime.

---

## 🚀 Quick start (Docker — recommended)

```bash
git clone <your-repo-url>
cd careerpilot

cp backend/.env.example backend/.env
# edit backend/.env: set a real SECRET_KEY, and (optionally) GEMINI_API_KEY / ADZUNA_APP_ID / ADZUNA_APP_KEY

docker compose up --build
```

- Frontend: http://localhost
- Backend docs: http://localhost:8000/api/docs

## 🛠️ Local development (without Docker)

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

**Run the test suite**
```bash
cd backend
pytest -v
```

27 tests covering: signup/login/duplicate-email/password-hashing, full
email-verification and password-reset flows (including expired/invalid
token rejection), resume upload validation (extension, size, magic bytes),
per-owner resume access isolation, analysis on both the Gemini and
heuristic paths, tailor-without-API-key behavior, and rate-limiter
correctness.

---

## 📁 Project structure

```
careerpilot/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, middleware, startup
│   │   ├── api/
│   │   │   ├── deps.py               # get_db, get_current_user
│   │   │   └── routes/               # auth.py, resumes.py, jobs.py
│   │   ├── core/                     # config.py (env settings), security.py (JWT + bcrypt)
│   │   ├── db/                       # SQLAlchemy session
│   │   ├── models/                   # User, Resume(+Analysis)
│   │   ├── schemas/                  # Pydantic request/response models
│   │   └── services/
│   │       ├── resume_parser.py      # spaCy + pdfplumber/python-docx extraction
│   │       ├── analyzer.py           # Gemini scoring + deterministic fallback
│   │       ├── semantic_matcher.py   # sentence-transformers skill-claim verification
│   │       ├── skill_matcher.py      # ~45-skill taxonomy, PhraseMatcher
│   │       ├── resume_tailor.py      # job-specific resume rewriting
│   │       ├── pdf_report.py         # ReportLab PDF generation
│   │       ├── job_search.py         # Adzuna API integration
│   │       ├── file_validation.py    # extension/size/magic-byte checks
│   │       ├── email_service.py      # verification + reset emails (or console log)
│   │       └── rate_limiter.py       # Redis sliding window + in-memory fallback
│   ├── alembic/                       # DB migrations
│   ├── tests/                         # pytest suite (27 tests)
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                       # client.js (axios + JWT refresh interceptor), resources.js
│   │   ├── context/AuthContext.jsx    # auth state (session-only — see note below)
│   │   ├── components/                # Navbar, ProtectedRoute
│   │   └── pages/                     # Home, Login, Signup, VerifyEmail, ForgotPassword,
│   │                                  # ResetPassword, Dashboard, Upload, ResumeDetail, JobSearch
│   └── Dockerfile                     # nginx-served production build
├── .github/workflows/ci.yml           # backend tests (Postgres + Redis service containers) + frontend build
└── docker-compose.yml                 # Postgres + Redis + API + frontend, with health checks
```

**Stack:** FastAPI, PostgreSQL, SQLAlchemy + Alembic, Redis, JWT auth
(bcrypt-hashed passwords), Google Gemini (resume analysis + tailoring),
sentence-transformers (local semantic skill matching), spaCy (parsing +
keyword fallback), ReportLab (PDF generation), Adzuna API (job search),
React 18 + Vite, Docker Compose, pytest, GitHub Actions CI.

---

## 🔐 Security notes

- Passwords hashed with bcrypt, never stored or logged in plaintext.
- JWT access + refresh tokens; access tokens are short-lived and stored in
  `sessionStorage`, not `localStorage`, so closing the tab/browser ends the
  session.
- Email verification and password reset use expiring, single-use tokens;
  the forgot-password flow never reveals whether an email is registered.
- Every resume/analysis query is scoped to its owner at the ORM level —
  one user's uploads and results are structurally unreachable by another
  user.
- Upload validation: extension allowlist, per-file size cap, and
  magic-byte signature checking (not just trusting the file extension).
- Redis-backed rate limiting per IP on auth, upload, and analysis
  endpoints, with an automatic in-memory fallback if Redis is unreachable.
- `.env` files are gitignored; `.env.example` documents every variable.

## 🔑 Getting API keys (both free)

- **Gemini** (AI analysis + tailoring): https://aistudio.google.com/apikey
  — without it, the app automatically falls back to the deterministic
  keyword-matching engine; nothing breaks, you just get less-rich analysis.
- **Adzuna** (job search): https://developer.adzuna.com/ — without it, job
  search returns a clear `503` rather than failing silently.

## ⚙️ CI/CD

`.github/workflows/ci.yml` runs on every push/PR to `main`:
- **backend-tests**: spins up real Postgres + Redis service containers,
  installs dependencies, downloads the spaCy model, and runs the full
  pytest suite. No `GEMINI_API_KEY` is set in CI on purpose — the suite
  must (and does) pass entirely on the deterministic fallback engine,
  since a test suite should never depend on a live third-party API call.
- **frontend-build**: installs and builds the React app.

If you fork/push this to your own GitHub repo, the workflow runs
automatically — no extra setup needed beyond having the code in the repo.

## 📈 What I'd do next (honest roadmap)

Good projects name their own limitations — this is what I'd point to if
asked "what would you improve next":
- No admin dashboard for platform-wide usage stats.
- Resume skill-extraction (fallback engine) covers a curated ~45-skill
  taxonomy; the Gemini path is far more general but costs an API call.
- `datetime.utcnow()` is used in a few places (flagged as deprecated by
  Python, not yet removed) — a clean follow-up would be migrating to
  timezone-aware `datetime.now(UTC)` throughout.
- Celery + Redis for resume processing at higher upload volume, instead of
  FastAPI `BackgroundTasks`.
- Support additional resume formats (e.g. `.rtf`) and multi-language
  parsing.

---

## 📄 License

MIT — see `LICENSE`.
