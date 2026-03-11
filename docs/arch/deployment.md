# Deployment-Architektur

## Umgebungen

| Umgebung | URL | Branch | Auto-Deploy |
|----------|-----|--------|-------------|
| Production | writing.iil.pet | main | Nein (manuell) |
| Staging | staging.writing.iil.pet | develop | Ja (auto) |
| Lokal | localhost:8000 | beliebig | n/a |

## Docker-Compose-Struktur

```yaml
services:
  db:        # PostgreSQL
  redis:     # Redis (Cache + Queue)
  web:       # Django (Gunicorn)
  celery:    # Celery Worker (async Tasks)
  beat:      # Celery Beat (Scheduler)
```

## Deployment-Prozess

```
[1] git push origin develop
         |
         v
[2] GitHub Actions: Lint + Tests
         |
         v
[3] Docker Image Build + Push to Registry
         |
         v
[4] SSH -> Server: docker compose pull + up -d
         |
         v
[5] python manage.py migrate (automatisch beim Start)
         |
         v
[6] Staging verfuegbar: staging.writing.iil.pet
```

## Infra-Repo

Die Docker-Compose- und Traefik-Konfigurationen liegen in:
`/home/dehnert/github/infra-deploy/`

## Umgebungsvariablen (Prod/Staging)

```env
# Django Core
DJANGO_SECRET_KEY=<secret>
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_ALLOWED_HOSTS=writing.iil.pet

# Datenbank
DATABASE_URL=postgresql://user:pass@db:5432/writinghub

# Redis
REDIS_URL=redis://redis:6379/0

# WeltenHub
WELTENHUB_URL=https://weltenhub.iil.pet
WELTENHUB_TOKEN=<service-token>

# LLM
OPENAI_API_KEY=<key>
# Optional:
AIFW_BASE_URL=https://aifw.iil.pet
AIFW_API_KEY=<key>
```

## Health Check

```bash
curl https://writing.iil.pet/health/
# -> {"status": "ok"}
```

## Migrations bei Deployment

Migrationen laufen automatisch via Docker Entrypoint:
```bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn config.wsgi:application
```

## Rollback

```bash
# Vorheriges Image
docker compose pull writing-hub:previous-tag
docker compose up -d

# DB-Migration rueckgaengig
python manage.py migrate <app> <previous_migration>
```

## Monitoring

- Sentry fuer Error-Tracking (`SENTRY_DSN` in Settings)
- Django Debug Toolbar lokal
- Logs: `docker compose logs -f web`
