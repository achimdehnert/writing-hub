# Writing Hub

Eigenständige Autorenplattform — extrahiert aus `bfagent` gemäß ADR-083.

## Überblick

`writing-hub` ist das eigenständige Django-Projekt für alle Authoring-Funktionen:

- **worlds** — Weltenbau (World, WorldLocation, WorldRule, WorldCharacter)
- **projects** — Buchprojekte, Outline, Kapitel
- **series** — Buchserien, SharedCharacter, SharedWorld
- **authoring** — ChapterWriter, StyleChecker, QualityScoring
- **illustration** — IllustrationSession, SceneAnalysis
- **idea_import** — IdeaImportDraft (ADR-081)
- **api** — REST API für bfagent-Integration

## Stack

- Django 5.2 LTS
- PostgreSQL 15
- Gunicorn + WhiteNoise
- DRF für REST API
- iil-aifw für LLM-Integration

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Deployment

Siehe `docker-compose.prod.yml`. Port: `8095`.
Domain: `writing.bfagent.iil.pet`

## ADRs

- [ADR-081](https://github.com/achimdehnert/bfagent/blob/main/docs/adr/ADR-081-idea-import-document-extraction.md) — IdeaImport
- [ADR-082](https://github.com/achimdehnert/bfagent/blob/main/docs/adr/ADR-082-world-character-sst.md) — WorldCharacter SSoT
- [ADR-083](https://github.com/achimdehnert/bfagent/blob/main/docs/adr/ADR-083-writing-hub-extraction.md) — Writing Hub Extraktion
