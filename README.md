# kartup

A single-page Flask site with exactly two fields (**Name**, **Surname**) and a **Submit** button. Submissions are validated on the server and stored in a `submissions` table. A separate, password-protected admin page at `/admin` lists them; nothing is ever shown on the public page.

- **Frontend:** HTML, CSS, vanilla JavaScript (premium dark theme, responsive, accessible, reduced-motion aware)
- **Backend:** Python 3.11+ / Flask, Flask-SQLAlchemy (parameterised ORM queries)
- **Database:** SQLite locally, PostgreSQL in production (via `DATABASE_URL`)
- **Server:** Gunicorn

## Project structure

```
kartup/
├── app/
│   ├── __init__.py        # app factory, security headers, table creation
│   ├── config.py          # all settings come from environment variables
│   ├── extensions.py      # SQLAlchemy instance
│   ├── models.py          # Submission model -> "submissions" table
│   ├── validation.py      # server-side field validation
│   ├── public.py          # GET /  and  POST /api/submissions
│   ├── admin.py           # /admin login, dashboard, logout
│   ├── cli.py             # flask init-db, flask hash-password
│   ├── templates/         # index.html, admin/login.html, admin/dashboard.html
│   └── static/            # css/style.css, js/app.js, favicon.svg
├── tests/                 # pytest suite
├── wsgi.py                # production entry point (gunicorn wsgi:app)
├── gunicorn.conf.py       # binds to $PORT, preload, logging
├── render.yaml            # Render Blueprint (web service + PostgreSQL)
├── Procfile               # for Heroku-style hosts
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── .gitignore
```

## Database table

| column       | type                          | notes                         |
|--------------|-------------------------------|-------------------------------|
| `id`         | integer, primary key          | auto-generated                |
| `name`       | varchar(100), not null        |                               |
| `surname`    | varchar(100), not null        |                               |
| `created_at` | timestamp with time zone      | set automatically (UTC), indexed |

Tables are created automatically when the app starts (idempotent). You can also run `flask --app wsgi init-db`.

## API

`POST /api/submissions` with JSON `{"name": "...", "surname": "..."}`

- `201` `{"ok": true, "message": "Thank you! ..."}`
- `422` `{"ok": false, "message": "...", "errors": {"name": "..."}}` on validation failure
- `415` if the body is not JSON, `500` with a friendly message if the database write fails

Rules: both fields required, trimmed, max 100 characters. Any characters are allowed (letters, numbers, symbols such as @). The response never contains stored records. There is no public endpoint that lists submissions.

## Run locally

```bash
cd kartup
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

cp .env.example .env               # optional; or export the variables below
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD_HASH="$(flask --app wsgi hash-password)"   # prompts for a password

flask --app wsgi run --debug       # http://127.0.0.1:5000
```

Without `DATABASE_URL`, data is stored in `instance/kartup.db` (SQLite, git-ignored).

To run with the production server locally: `gunicorn wsgi:app` (listens on `$PORT`, default 8000).

To try PostgreSQL locally, set e.g. `DATABASE_URL=postgresql://user:pass@localhost:5432/kartup`. `postgres://` and `postgresql://` URLs are both accepted and mapped to the psycopg 3 driver automatically.

> On Windows, `export` becomes `set VAR=value` (cmd) or `$env:VAR="value"` (PowerShell). Flask doesn't read `.env` on its own unless `python-dotenv` is installed (`pip install python-dotenv`).

## Admin access

Visit `/admin`. Sign in with `ADMIN_USERNAME` and the password whose hash is in `ADMIN_PASSWORD_HASH`.

- Generate the hash with `flask --app wsgi hash-password` (at least 10 characters).
- `ADMIN_PASSWORD` (plain text) is accepted as a fallback for quick local testing only; prefer the hash.
- If neither is set, admin login is disabled.
- Protections: signed, HttpOnly, SameSite cookies (Secure in production), CSRF tokens on login/logout, 5 failed attempts per IP per 15 minutes, 2-hour session lifetime, `noindex` and `no-store` on admin pages.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

Covers: page shows only the two fields and Submit, successful save, validation errors, non-JSON rejection, no public listing, admin redirect when signed out, wrong password, CSRF required, login rate limit, admin listing and logout.

## Environment variables

| variable | required | purpose |
|---|---|---|
| `SECRET_KEY` | yes (production) | signs session cookies; app refuses to start in production without it |
| `DATABASE_URL` | production | PostgreSQL connection string; unset = SQLite |
| `ADMIN_USERNAME` | no | defaults to `admin` |
| `ADMIN_PASSWORD_HASH` | to enable admin | output of `flask --app wsgi hash-password` |
| `SESSION_COOKIE_SECURE` | no | defaults to `1` when `DATABASE_URL` is set |
| `PORT`, `WEB_CONCURRENCY` | no | Gunicorn bind port and worker count |

## Deploy to Render

### Option A: Blueprint (one click, recommended)

1. Push this folder to a GitHub repository (it must be the repo root, or set the root directory in Render).
2. In Render, choose **New > Blueprint** and select the repository. Render reads `render.yaml` and creates:
   - a free PostgreSQL database `kartup-db`
   - a Python web service `kartup` with `DATABASE_URL` wired to the database and a generated `SECRET_KEY`
3. When prompted for `ADMIN_PASSWORD_HASH`, paste the output of `flask --app wsgi hash-password` (run locally).
   Tip: in Render's env var editor, paste the hash as-is; it contains `$` and `:` characters, which is fine.
4. Click **Apply**. Once deployed, open the service URL. The table is created on first start. Admin is at `/admin`.

### Option B: Manual

1. **New > PostgreSQL**: create a database and copy its **Internal Database URL**.
2. **New > Web Service** from your repo:
   - Runtime: Python
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn wsgi:app`
   - Health check path: `/healthz`
3. Environment variables: `DATABASE_URL` (the internal URL), `SECRET_KEY` (a long random string), `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, and optionally `PYTHON_VERSION=3.12.7`.
4. Deploy.

### Other hosts

Any platform that runs Python and offers PostgreSQL works (Railway, Fly.io, Heroku, a VPS). Use `gunicorn wsgi:app` as the start command (a `Procfile` is included) and set the same environment variables.

## Security notes

- No secrets in code; everything comes from environment variables. `.env` and local database files are git-ignored.
- All database access goes through SQLAlchemy's ORM (parameterised queries).
- Strict Content-Security-Policy (no inline scripts), `X-Frame-Options: DENY`, `nosniff`, 16 KB request body limit.
- The public page and API never return stored submissions.
