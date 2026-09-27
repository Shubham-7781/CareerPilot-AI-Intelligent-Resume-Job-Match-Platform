# Running CareerPilot locally via terminal (no Docker)

Requires: Python 3.11+, Node 20+, PostgreSQL, and optionally Redis.

## 1. Install PostgreSQL

- **Windows:** download from postgresql.org and run the installer. During
  install you'll be asked for a password for the `postgres` superuser —
  pick anything memorable (this is separate from your app's DB password).
- **macOS:** `brew install postgresql@16 && brew services start postgresql@16`
- **Ubuntu/Debian:** `sudo apt install postgresql postgresql-contrib && sudo systemctl start postgresql`

If the installer offers **Stack Builder** at the end, you can cancel it —
it's optional add-ons, not needed here.

If `psql` isn't recognized in your terminal afterward, either use the full
path (e.g. `"C:\Program Files\PostgreSQL\18\bin\psql.exe"`) or add
`C:\Program Files\PostgreSQL\<version>\bin` to your PATH environment
variable and reopen the terminal.

Then create the app's database and user:
```bash
psql -U postgres
```
```sql
CREATE USER careerpilot WITH PASSWORD 'careerpilot';
CREATE DATABASE careerpilot OWNER careerpilot;
\q
```

## 2. (Optional) Install Redis

The rate limiter automatically falls back to in-memory limiting if Redis
isn't running, so this is skippable for local use.

- **macOS:** `brew install redis && brew services start redis`
- **Ubuntu:** `sudo apt install redis-server && sudo systemctl start redis-server`
- **Windows:** easiest via WSL, or just skip it

## 3. Backend setup

```bash
cd backend
python -m venv venv

source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows (cmd)
venv\Scripts\Activate.ps1       # Windows (PowerShell)

pip install -r requirements.txt
python -m spacy download en_core_web_sm

cp .env.example .env            # macOS/Linux
copy .env.example .env          # Windows
```

Edit `backend/.env`:
```
DATABASE_URL=postgresql://careerpilot:careerpilot@localhost:5432/careerpilot
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<see below>
ALLOWED_ORIGINS=["http://localhost:5173"]
```

**Getting a `SECRET_KEY`:** it's just a long random string used to sign
JWTs — you generate it yourself, not fetched from anywhere:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
Paste the output as `SECRET_KEY=...`. Never commit a real one to GitHub —
`.env` is already gitignored for this reason.

Leave `GEMINI_API_KEY` and `ADZUNA_APP_ID`/`ADZUNA_APP_KEY` blank if you
don't have them yet — the app degrades gracefully (basic analysis engine,
job search returns a clear error) rather than crashing. Leave `SMTP_HOST`
blank too — verification/reset emails will just print to your terminal.

## 4. Run database migrations

```bash
# still inside backend/, venv active
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## 5. Start the backend

```bash
uvicorn app.main:app --reload
```
Check it worked: open **http://localhost:8000/api/docs**.

## 6. Start the frontend (new terminal)

```bash
cd frontend
npm install
cp .env.example .env      # macOS/Linux
copy .env.example .env    # Windows
npm run dev
```
Open **http://localhost:5173**.

## 7. Run tests (optional)

```bash
cd backend
source venv/bin/activate   # if not already active
pytest -v
```

## Troubleshooting

- `password authentication failed` → the Postgres user/password you
  created doesn't match `DATABASE_URL`.
- `connection refused` on port 5432 → Postgres isn't running.
- CORS errors in the browser console → `ALLOWED_ORIGINS` in
  `backend/.env` must include `http://localhost:5173`.
- Job search returns 503 → `ADZUNA_APP_ID`/`ADZUNA_APP_KEY` not set — get
  a free key at developer.adzuna.com.
- Resume analysis feels basic (no strengths/improvements/course
  recommendations) → `GEMINI_API_KEY` not set — get a free key at
  aistudio.google.com/apikey.
- App logs you out every time you reopen the browser → this is intentional
  (see README "A note on login behavior"), not a bug.
