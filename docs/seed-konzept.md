# Seed-Konzept: Stammdaten & Konfiguration

## Warum?

Staging und Production müssen identisch konfiguriert sein.
Manueller Admin-Eingriff nach jedem Deploy ist fehleranfällig.

## Kategorien

### Kategorie A — Fixtures (JSON im Repo)
Stammdaten die überall gleich sind und versioniert werden müssen:

| Fixture | Inhalt |
|---------|--------|
| `fixtures/initial_lookups.json` | ContentTypeLookup, GenreLookup, AudienceLookup |
| `fixtures/initial_quality.json` | QualityDimension, GateDecisionType |

Fixtures werden bei **jedem Deploy automatisch** via `seed_all` geladen (`loaddata` ist idempotent).

### Kategorie B — Management Commands (Code-gesteuert)

| Command | Zweck |
|---------|-------|
| `setup_aifw_actions` | LLMProvider + LLMModel + AIActionType anlegen |
| `seed_all` | Orchestriert alle Seeds in richtiger Reihenfolge |

Konfigurierte `action_codes` für aifw:

| action_code | Zweck |
|-------------|-------|
| `world_generate` | Vollständige Weltgenerierung |
| `world_expand` | Einzelnen Welt-Aspekt vertiefen |
| `world_locations` | Orte für eine Welt generieren |
| `character_generate` | Charaktere / Besetzung generieren |
| `scene_generate` | Szenen generieren |
| `chapter_analyze` | Kapitel-Review / Lektorat |
| `idea_brainstorm` | Buchideen brainstormen (Ideen-Studio) |
| `idea_refine` | Idee verfeinern |
| `idea_premise` | Premise aus Idee generieren |
| `style_extract` | DO/DONT/Taboo aus Quelltext extrahieren |

### Kategorie C — Umgebungsvariablen (.env)

| Variable | Zweck |
|----------|-------|
| `OPENAI_API_KEY` | OpenAI API-Key |
| `DJANGO_SECRET_KEY` | Django Secret |
| `DATABASE_URL` | DB-Verbindung |
| `WELTENHUB_URL` | WeltenHub REST URL |
| `WELTENHUB_TOKEN` | WeltenHub Service-Token |
| `REDIS_URL` | Celery Broker |

## Deploy-Ablauf (automatisch)

```
Deploy startet
  └ migrate --noinput
  └ collectstatic
  └ seed_all
      └ loaddata fixtures/initial_lookups.json    (idempotent)
      └ loaddata fixtures/initial_quality.json     (idempotent)
      └ setup_aifw_actions                         (idempotent)
  └ gunicorn start
```

## Neue Stammdaten hinzufügen

1. Fixture-Datei updaten (oder neue anlegen)
2. Commit + Push → nächster Deploy überträgt automatisch
3. Kein manueller Admin-Eingriff nötig

## Was NICHT in Fixtures kommt

- `auth.User` — immer umgebungsspezifisch
- `BookProject`, `BookSeries` — Nutzerdaten
- `IdeaImportDraft`, `CreativeSession`, `BookIdea` — Transaktionsdaten
- `WritingStyle`, `AuthorStyleDNA` — Nutzerdaten
- `ProjectWorldLink`, `ProjectCharacterLink`, `ProjectLocationLink`, `ProjectSceneLink` — Nutzerdaten
