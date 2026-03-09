# Seed-Konzept: Stammdaten & Konfiguration

## Warum?

Staging und Production m\u00fcssen identisch konfiguriert sein.
Manueller Admin-Eingriff nach jedem Deploy ist fehleranf\u00e4llig.

## Kategorien

### Kategorie A \u2014 Fixtures (JSON im Repo)
Stammdaten die \u00fcberall gleich sind und versioniert werden m\u00fcssen:

| Fixture | Inhalt |
|---|---|
| `fixtures/initial_lookups.json` | ContentTypeLookup, GenreLookup, AudienceLookup |
| `fixtures/initial_quality.json` | QualityDimension, GateDecisionType |

Fixtures werden bei **jedem Deploy automatisch** via `seed_all` geladen (`loaddata` ist idempotent bei PK-Konflikten).

### Kategorie B \u2014 Management Commands (Code-gesteuert)
Konfiguration mit Umgebungsabh\u00e4ngigkeiten (Provider, Modell):

| Command | Zweck |
|---|---|
| `setup_aifw_actions` | LLMProvider + LLMModel + AIActionType anlegen |
| `seed_all` | Orchestriert alle Seeds in richtiger Reihenfolge |

### Kategorie C \u2014 Umgebungsvariablen (.env)
Sensible Konfiguration **niemals** in Fixtures oder Code:

| Variable | Zweck |
|---|---|
| `OPENAI_API_KEY` | OpenAI API-Key |
| `DJANGO_SECRET_KEY` | Django Secret |
| `DATABASE_URL` | DB-Verbindung |

Diese werden **nicht** geseedet \u2014 m\u00fcssen in `.env.staging` und `.env.production` gesetzt sein.

## Deploy-Ablauf (automatisch)

```
Deploy startet
  \u2514 migrate --noinput
  \u2514 collectstatic
  \u2514 seed_all
      \u2514 loaddata fixtures/initial_lookups.json    (idempotent)
      \u2514 loaddata fixtures/initial_quality.json     (idempotent)
      \u2514 setup_aifw_actions                         (idempotent)
  \u2514 gunicorn start
```

## Neue Stammdaten hinzuf\u00fcgen

1. Fixture-Datei updaten (oder neue anlegen)
2. Commit + Push \u2192 n\u00e4chster Deploy \u00fcbertr\u00e4gt automatisch auf Staging + Production
3. Kein manueller Admin-Eingriff n\u00f6tig

## aifw-Konfiguration \u00e4ndern (Modell wechseln)

```bash
# Auf Staging oder Production:
python manage.py setup_aifw_actions --model gpt-4o --force

# Oder: Standard-Modell im Command \u00e4ndern + deployen
# apps/projects/management/commands/setup_aifw_actions.py \u2192 ACTION_CODES Default
```

## Was NICHT in Fixtures kommt

- `auth.User` \u2014 immer umgebungsspezifisch
- `BookProject`, `BookSeries` \u2014 Nutzerdaten
- `IdeaImportDraft`, `OutlineVersion` \u2014 Transaktionsdaten
- `AuthorStyleDNA`, `ChapterQualityScore` \u2014 Nutzerdaten
