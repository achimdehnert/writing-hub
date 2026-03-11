# Lokales Setup (Entwickler)

## Voraussetzungen

- Python 3.11+
- pip / venv
- SQLite (lokal) oder PostgreSQL (Staging/Prod)
- Zugang zu WeltenHub (`WELTENHUB_URL`, `WELTENHUB_TOKEN`)
- OpenAI API Key (`OPENAI_API_KEY`) oder kompatibles LLM-Backend

## Setup-Schritte

```bash
git clone https://github.com/achimdehnert/writing-hub.git
cd writing-hub
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Umgebungsvariablen

Erstelle eine `.env`-Datei im Projektroot:

```env
# Django
DJANGO_SECRET_KEY=dein-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Datenbank (lokal: SQLite automatisch)
DATABASE_URL=sqlite:///db.sqlite3

# WeltenHub
WELTENHUB_URL=https://weltenhub.iil.pet
WELTENHUB_TOKEN=dein-weltenhub-token

# LLM (OpenAI oder compatible)
OPENAI_API_KEY=sk-...
# Optional: iil-aifw Router
AIFW_BASE_URL=https://aifw.iil.pet
AIFW_API_KEY=dein-aifw-token

# Redis (optional, fuer Celery)
REDIS_URL=redis://localhost:6379/0
```

## Datenbank migrieren

```bash
python manage.py migrate
python manage.py createsuperuser
```

## Seed-Daten

```bash
# Fixtures laden (Genre, Aktionen, etc.)
python manage.py loaddata apps/*/fixtures/*.json

# Management Commands
python manage.py seed_authors    # Demo-Autoren
python manage.py seed_projects   # Demo-Projekte
```

## Entwicklungsserver starten

```bash
python manage.py runserver
```

App erreichbar unter: http://localhost:8000

## Settings-Module

| Modul | Verwendung |
|-------|------------|
| `config/settings/base.py` | Gemeinsame Einstellungen |
| `config/settings/local.py` | Lokal (DEBUG=True, SQLite) |
| `config/settings/staging.py` | Staging (PostgreSQL, Sentry) |
| `config/settings/production.py` | Production (PostgreSQL, strict) |

Aktivierung via `DJANGO_SETTINGS_MODULE`:
```bash
export DJANGO_SETTINGS_MODULE=config.settings.local
```
