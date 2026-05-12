# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**vocabmorizer** — a web app for learning and practising vocabulary and phrases for second language acquisition. Built with Flask + SQLite. See [SPECIFICATION.md](SPECIFICATION.md) for the full feature spec and [README.md](README.md) for usage.

## Setup

```bash
# Install dependencies (Python 3.11+)
pip install -e ".[dev]"

# Copy and fill in secrets
cp .env.example .env
# Set SECRET_KEY and ADMIN_PASSWORD in .env

# Create / migrate the database
flask db upgrade

# Run the development server
flask run
# or
python wsgi.py
```

The app starts at `http://localhost:5000`. Log in with username `admin` and the `ADMIN_PASSWORD` from `.env`.

## Common Commands

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_auth.py -v

# Run a single test
pytest tests/test_auth.py::TestLogin::test_login_page_loads -v

# Lint and format
ruff check .
ruff format .

# Generate a new DB migration after changing models
flask db migrate -m "describe the change"
flask db upgrade

# i18n (Phase 4 onwards)
pybabel extract -F babel.cfg -o locales/messages.pot .
pybabel update -i locales/messages.pot -d locales
pybabel compile -d locales
```

## Architecture

Flask application using the **application factory** pattern (`create_app()` in `app/__init__.py`). All extensions are instantiated in `app/extensions.py` and initialised in the factory to avoid circular imports.

### Key files

| Path | Purpose |
|------|---------|
| `app/__init__.py` | `create_app()` factory; registers all blueprints |
| `app/extensions.py` | `db`, `login_manager`, `migrate`, `csrf` — import from here everywhere |
| `app/config.py` | `DevelopmentConfig`, `ProductionConfig`, `TestingConfig` |
| `app/models/user.py` | `User` SQLAlchemy model + `load_user` hook |
| `app/auth/` | Blueprint at `/auth` — login, logout, register |
| `app/utils/decorators.py` | `@admin_required` |
| `app/templates/base.html` | Shared layout (Tailwind CDN, navbar, flash messages) |
| `wsgi.py` | WSGI entry point |
| `migrations/` | Alembic migration files — commit these |

### Blueprints (planned by phase)

| Blueprint | Prefix | Phase |
|-----------|--------|-------|
| `auth` | `/auth` | 1 ✅ |
| `vocab` | `/vocab` | 2 |
| `practice` | `/practice` | 3 |
| `admin` | `/admin` | 5 |
| `stats` | `/stats` | 7 |
| `io` | `/io` | 6 |
| `backup` | `/backup` | 8 |

### Auth

Three login paths:
1. **Admin bootstrap** — username `admin` + `ADMIN_PASSWORD` env var; bypasses the DB entirely via `_AdminProxy`; used before any users exist
2. **Email/password** — standard local accounts; passwords hashed with bcrypt
3. **Google OAuth** — Phase 9 (deferred until Google Cloud credentials are available)

### Database

SQLAlchemy ORM with Flask-Migrate (Alembic). SQLite in dev/prod. For tests, use `StaticPool` + `sqlite:///:memory:` (see `tests/conftest.py`) so all app contexts share the same in-memory DB and `g._login_user` doesn't leak between requests.

### Testing

Function-scoped `client` and `db` fixtures; session-scoped `app` fixture that does NOT hold an app context open during tests (avoids Flask-Login's `g._login_user` leaking across test requests via the shared session-scoped app context).
