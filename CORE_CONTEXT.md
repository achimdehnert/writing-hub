# Writing Hub — Core Context

> **Zweck:** KI-gestützte Autorenplattform der iil-Plattform
> **Domain:** https://writing.iil.pet
> **Port:** 8097

## Quick Facts

| Key | Value |
|-----|-------|
| **Repo** | achimdehnert/writing-hub |
| **Stack** | Django 5.2 LTS, PostgreSQL 15, Celery+Redis |
| **Server** | 88.198.191.108, `/opt/writing-hub` |
| **Container** | `writing_hub_web`, `writing_hub_db` |
| **Settings** | `config.settings.production` / `config.settings.test` |

## Apps

| App | Beschreibung |
|-----|--------------|
| `projects` | Buchprojekte, Outline, Kapitel, Versionen, Export, Review, Lektorat |
| `authors` | Autoren-Profile, WritingStyle, Style Lab (DO/DONT/Taboo/Signature Moves) |
| `series` | Buchserien, SharedCharacter, SharedWorld |
| `worlds` | WeltenHub-Integration — Welten, Charaktere, Orte, Szenen via `iil-weltenfw` |
| `idea_import` | Ideen-Import (Datei-Upload) + Ideen-Studio Kreativagent |
| `authoring` | ChapterWriter, StyleChecker, QualityScoring, LLMRouter |
| `illustration` | IllustrationSession, SceneAnalysis |
| `outlines` | Outline-Management, Beat-Struktur |
| `core` | Shared utilities, base templates |
| `api` | REST API (DRF) |

## iil Platform Packages

| Package | Zweck |
|---------|-------|
| `iil-aifw` | LLM-Routing — `LLMRouter.completion()` via DB-konfigurierte AIActionTypes |
| `iil-promptfw` | Prompt-Templates — `PromptStack.render_to_messages()` (Jinja2, 5-Layer) |
| `iil-authoringfw` | Domain-Schemas — `StyleProfile`, `CharacterProfile`, `WorldContext` |
| `iil-weltenfw` | WeltenHub REST Client — `get_client().worlds/characters/locations/scenes` |
| `iil-outlinefw` | Story Outline Framework — Beat-Schemas, LLM-Generator |

## SSoT-Prinzip (Single Source of Truth)

- **Welten, Charaktere, Orte, Szenen** → SSoT ist **WeltenHub** (`weltenhub.iil.pet`)
- Writing-Hub speichert nur UUID-Referenzen lokal (`ProjectWorldLink`, `ProjectCharacterLink`, etc.)
- Daten werden live via `iil-weltenfw` aus WeltenHub geladen
- **Kein lokales ORM-Modell** für Welt-Entitäten

## URL-Struktur

| Pfad | App | Beschreibung |
|------|-----|--------------|
| `/` | core | Dashboard |
| `/projects/` | projects | Buchprojekte CRUD |
| `/outlines/` | outlines | Outline-Editor |
| `/serien/` | series | Buchserien |
| `/ideen/` | idea_import | Ideen-Import + Studio |
| `/welten/` | worlds | WeltenHub-Integration |
| `/autoren/` | authors | Autoren-Profile |
| `/api/v1/` | api | REST API |

## ADRs

Siehe `docs/adr/ADR-INDEX.md` für vollständige Liste.

Wichtigste ADRs:
- **ADR-150** — Romanstruktur 4-Ebenen-Datenmodell
- **ADR-151** — Dramaturgische Felder OutlineNode Lookups
- **ADR-152** — Charakter-Arc Dramaturgie
- **ADR-153** — Frontend CSS Design Tokens HTMX
- **ADR-083** — Writing Hub Extraktion (Ursprung)

## Deployment

| Branch | Umgebung | Trigger |
|--------|----------|---------|
| `develop` | Staging (staging.writing.iil.pet) | push auf develop |
| `main` | — | kein automatischer Deploy |
| `main` + workflow_dispatch | Production (writing.iil.pet) | NUR explizit |

**Regel:** Änderungen immer über `develop` auf Staging testen — Production NUR auf explizite Anweisung.

## Prompt Templates (promptfw)

Alle LLM-Prompts sind als Jinja2-Templates in `/templates/prompts/` ausgelagert:

```
templates/prompts/
├── idea_import/          # Brainstorm, Refine, Premise, Exposé
├── outlines/             # Structure-Pass, Detail-Pass, Enrich
├── authors/              # Analyze Style, Extract Rules, Generate Sample
└── projects/             # Review Agents, Lektorat, Keywords
```

**Nutzung:**
```python
from apps.core.prompt_utils import render_prompt

messages = render_prompt("idea_import/brainstorm_ideas", genre="Thriller", count=5)
result = router.completion(action_code="outline_generate", messages=messages)
```

**18 Templates** für zentrale Prompt-Verwaltung, A/B-Testing und Versionierung.

## Testing

```bash
# Lokal
pytest tests/ -v

# Mit Coverage
pytest tests/ --cov=apps --cov-report=term-missing
```

Settings: `config.settings.test` (SQLite in-memory, WHITENOISE_MANIFEST_STRICT=False)
