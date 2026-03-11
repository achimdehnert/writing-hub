# Writing Hub

Eigenständige Autorenplattform — Django 5.2 LTS, PostgreSQL 15.

## Überblick

`writing-hub` ist das zentrale Django-Projekt für alle Authoring-Funktionen der iil-Plattform.

### Apps

| App | Beschreibung |
|-----|--------------|
| `projects` | Buchprojekte, Outline, Kapitel, Versionen, Export, Review, Lektorat |
| `authors` | Autoren-Profile, WritingStyle, Style Lab (DO/DONT/Taboo/Signature Moves) |
| `series` | Buchserien, SharedCharacter, SharedWorld |
| `worlds` | WeltenHub-Integration — Welten, Charaktere, Orte, Szenen via `iil-weltenfw` |
| `idea_import` | Ideen-Import (Datei-Upload) + Ideen-Studio Kreativagent |
| `authoring` | ChapterWriter, StyleChecker, QualityScoring, LLMRouter |
| `illustration` | IllustrationSession, SceneAnalysis |

### iil Platform Packages

| Package | Zweck |
|---------|-------|
| `iil-aifw` | LLM-Routing — `LLMRouter.completion()` via DB-konfigurierte AIActionTypes |
| `iil-promptfw` | Prompt-Templates — `PromptStack.render_to_messages()` (Jinja2, 5-Layer) |
| `iil-authoringfw` | Domain-Schemas — `StyleProfile`, `CharacterProfile`, `WorldContext` |
| `iil-weltenfw` | WeltenHub REST Client — `get_client().worlds/characters/locations/scenes` |
| `iil-outlinefw` | Story Outline Framework — Beat-Schemas, LLM-Generator |

## Stack

- Django 5.2 LTS
- PostgreSQL 15
- Gunicorn + WhiteNoise
- DRF für REST API
- Celery + Redis für Async Tasks

## URLs

| Umgebung | URL |
|----------|-----|
| Production | https://writing.iil.pet |
| Staging | https://staging.writing.iil.pet |
| WeltenHub | https://weltenhub.iil.pet |

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_all
python manage.py createsuperuser
python manage.py runserver
```

## Deployment

Siehe `docker-compose.prod.yml`. Port: `8095`.

```bash
# Staging-Deploy: push auf develop-Branch
git push origin develop

# Production-Deploy: NUR auf explizite Anweisung
# workflow_dispatch mit environment=production
```

## Architektur

Siehe [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## ADRs

- [ADR-081](https://github.com/achimdehnert/bfagent/blob/main/docs/adr/ADR-081-idea-import-document-extraction.md) — IdeaImport
- [ADR-082](https://github.com/achimdehnert/bfagent/blob/main/docs/adr/ADR-082-world-character-sst.md) — WorldCharacter SSoT
- [ADR-083](https://github.com/achimdehnert/bfagent/blob/main/docs/adr/ADR-083-writing-hub-extraction.md) — Writing Hub Extraktion
