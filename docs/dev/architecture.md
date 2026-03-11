# Architektur (Entwickler-Sicht)

## Projektstruktur

```
writing-hub/
├── apps/
│   ├── authors/        # Autoren-Profile, WritingStyle (Style Lab)
│   ├── idea_import/    # Ideen-Import + Ideen-Studio (Kreativagent)
│   ├── projects/       # Buchprojekte, Outline, Kapitel, Lektorat
│   └── worlds/         # WeltenHub-Integration (Welten, Chars, Orte)
├── config/
│   ├── settings/
│   └── urls.py
├── templates/          # Django-Templates (Jinja2-kompatibel)
├── docs/               # Diese Dokumentation
├── mkdocs.yml
├── requirements.txt
└── manage.py
```

## App-Verantwortlichkeiten

### `authors`
- `Author` — Autor-Profil mit Biografie
- `WritingStyle` — Style DNA (DO/DONT/Taboo/Signature Moves)
- Service: `extract_style_rules()` via LLM
- Service: `get_style_prompt_for_writing()` — Style als Prompt-Kontext

### `idea_import`
- `IdeaImportDraft` — Staging-Modell fuer Dokument-Import
- `CreativeSession` — Ideen-Studio Session
- `BookIdea` — Einzelne generierte Buchidee
- Views: `views_html.py` (Import), `views_creative.py` (Studio)

### `projects`
- `BookProject` — Hauptmodell
- `OutlineVersion`, `OutlineNode` — Outline-Baum
- `ChapterVersion`, `ChapterContent` — Kapitelinhalte
- `ReviewSession`, `ReviewFeedback` — Review-System
- `LektoratSession`, `LektoratIssue` — Lektorat
- `PublishingProfile` — Veroeffentlichungs-Metadaten

### `worlds`
- `ProjectWorldLink` — Projekt <-> WeltenHub-Welt
- `ProjectCharacterLink` — Projekt <-> WeltenHub-Charakter
- `ProjectLocationLink` — Projekt <-> WeltenHub-Ort
- `ProjectSceneLink` — Projekt <-> WeltenHub-Szene
- Services: `WorldBuilderService`, `WorldCharacterService`, `WorldLocationService`, `WorldSceneService`

## URL-Struktur

```
/                    # Dashboard
/projekte/           # Buchprojekte
/ideen/              # Ideen-Import
/ideen/studio/       # Ideen-Studio
/autoren/            # Autoren & Style Lab
/welten/             # WeltenHub-Integration
/api/                # REST API (DRF)
```

## View-Schichten

Jede App hat typischerweise:

| Datei | Zweck |
|-------|-------|
| `views_html.py` | Django Class-Based Views fuer HTML-Frontend |
| `views.py` | DRF API Views (REST) |
| `urls.py` / `urls_html.py` | URL-Routing |
| `services/` | Business-Logik, LLM-Integration |
| `models.py` | Django ORM Modelle |

## Service-Pattern

Services kapseln die Geschäftslogik:

```python
# Typischer Service-Aufruf
from apps.worlds.services import WorldBuilderService

service = WorldBuilderService()
result = service.generate_and_save(
    project=project,
    weltenhub_world_id=world_id,
    author_style=style,
)
```

Services nutzen intern:
1. `iil-aifw` fuer LLM-Calls
2. `iil-promptfw` fuer Prompt-Templates
3. `iil-authoringfw` fuer typisierte Schemas
4. `iil-weltenfw` fuer WeltenHub-Persistenz
