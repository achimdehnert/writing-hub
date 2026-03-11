# CI/CD-Pipeline

## Workflow-Datei

`.github/workflows/ci-cd.yml`

## Pipeline-Stages

```
Push zu main/develop
    |
    v
[1] Lint (Ruff)
    |
    v
[2] Tests (pytest)
    |
    v
[3] Docker Build
    |
    v
[4] Deploy Staging    <-- automatisch (develop-Branch)
    |
    v
[5] Deploy Production <-- NUR auf explizite Anweisung
```

## Branch-Strategie

| Branch | Deployment |
|--------|------------|
| `develop` | -> Staging automatisch |
| `main` | -> Production NUR manuell / explizit |

## Deployment-Regeln

> **KRITISCH:** Production (`writing.iil.pet`) wird NIEMALS automatisch deployed.
> Workflow: Code pushen -> CI grueen -> Staging testen -> explizit "deploy production" sagen.

## Docker-Compose (Staging/Prod)

```yaml
services:
  web:
    image: writing-hub:latest
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.staging
  celery:
    image: writing-hub:latest
    command: celery -A config worker
  beat:
    image: writing-hub:latest
    command: celery -A config beat
```

## Environment-Variablen in CI

GitHub Secrets (unter Repository Settings > Secrets):

```
DJANGO_SECRET_KEY
DATABASE_URL
WELTENHUB_URL
WELTENHUB_TOKEN
OPENAI_API_KEY
DOCKER_REGISTRY_TOKEN
```

## Manuelles Deployment

```bash
# Staging
git push origin develop

# Oder via GitHub Actions Workflow Dispatch:
# Actions -> ci-cd.yml -> Run workflow -> environment: staging
```
