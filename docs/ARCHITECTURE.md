# Writing Hub — Architektur

## Prinzipien

### SSoT (Single Source of Truth)
- **Welten, Charaktere, Orte, Szenen** → SSoT ist **WeltenHub** (`weltenhub.iil.pet`)
- Writing-Hub speichert nur UUID-Referenzen lokal (`ProjectWorldLink`, `ProjectCharacterLink`, `ProjectLocationLink`, `ProjectSceneLink`)
- Daten werden live via `iil-weltenfw` aus WeltenHub geladen
- **Kein lokales ORM-Modell** für Welt-Entitäten

### iil Package-Nutzung

```
LLM-Call:       LLMRouter.completion(action_code, messages)
                └─ iil-aifw → DB-Lookup AIActionType → LiteLLM → Provider

Prompt-Bau:     PromptStack.render_to_messages(template, **ctx)
                └─ iil-promptfw → Jinja2-Template aus PROMPT_TEMPLATES_DIR

Domain-Schema:  CharacterProfile / WorldContext / StyleProfile
                └─ iil-authoringfw → typisierte Zwischen-Daten für Prompts

WeltenHub API:  get_client().worlds.create(WorldCreateInput(...))
                └─ iil-weltenfw[django] → REST gegen WeltenHub
```

## App-Übersicht

### `apps/worlds/`

```
models.py
  ProjectWorldLink         — Referenz auf WeltenHub-Welt (UUID)
  ProjectCharacterLink     — Referenz auf WeltenHub-Charakter (UUID) + project_arc
  ProjectLocationLink      — Referenz auf WeltenHub-Ort (UUID)
  ProjectSceneLink         — Referenz auf WeltenHub-Szene (UUID) + outline_node FK

services/
  world_builder_service.py
    WorldBuilderService
      generate_world()         — LLM via aifw (action: world_generate)
      save_to_weltenhub()      — weltenfw WorldCreateInput
      link_to_project()        — ProjectWorldLink.get_or_create()
      expand_world_aspect()    — LLM + weltenfw WorldUpdateInput
      get_project_worlds()     — weltenfw.worlds.get() pro Link

  character_service.py
    WorldCharacterService
      generate_cast()          — LLM via aifw (action: character_generate)
                                  + promptfw.render_to_messages() wenn Template
                                  + authoringfw.CharacterProfile für Kontext
      save_to_weltenhub()      — weltenfw CharacterCreateInput
      link_to_project()        — ProjectCharacterLink.get_or_create()
      get_world_characters()   — weltenfw.characters.list(world=uuid) [kein iter_all]
      enrich_character()       — LLM + weltenfw CharacterUpdateInput

  location_service.py
    WorldLocationService
      generate_locations()     — LLM via aifw (action: world_locations)
                                  + promptfw.render_to_messages() wenn Template
      save_to_weltenhub()      — weltenfw LocationCreateInput
      link_to_project()        — ProjectLocationLink.get_or_create()
      get_world_locations()    — weltenfw.locations.list(world=uuid)

    WorldSceneService
      generate_scenes()        — LLM via aifw (action: scene_generate)
      save_to_weltenhub()      — weltenfw SceneCreateInput
      link_to_project()        — ProjectSceneLink.get_or_create()
      get_project_scenes()     — weltenfw.scenes.get() pro Link

views_html.py
  WorldListView               — Liste + Live-Daten aus WeltenHub
  ProjectWorldDetailView      — Welt + Charaktere + Orte (Live)
  WorldGenerateView           — POST: LLM → WeltenHub → Link
  WorldCharacterGenerateView  — POST: LLM → WeltenHub → Link
  WorldLocationGenerateView   — POST: LLM → WeltenHub → Link
```

### `apps/idea_import/`

```
models.py              — IdeaImportDraft (Datei-Import Workflow)
models_creative.py     — CreativeSession, BookIdea (Ideen-Studio Kreativagent)

views_html.py          — IdeaListView, IdeaUploadView, IdeaReviewView
views_creative.py      — CreativeDashboardView, CreativeSessionView,
                          CreativeBrainstormView, CreativeRefineView,
                          CreativePremiseView, CreativeCreateProjectView

urls_html.py
  /ideen/              — Ideen-Import (Datei-Upload)
  /ideen/studio/       — Ideen-Studio Kreativagent
```

### `apps/authors/`

```
models.py
  Author                — Autoren-Profil
  WritingStyle          — Schreibstil-DNA inkl. Style Lab:
    do_list             — JSONField (was tun)
    dont_list           — JSONField (was nicht tun)
    taboo_list          — JSONField (Tabu-Wörter/-Phrasen)
    signature_moves     — JSONField (charakteristische Stilmittel)

services.py
  extract_style_rules() — LLM extrahiert DO/DONT/Taboo aus Quelltext
  get_style_prompt_for_writing() — Style-DNA als Prompt-Kontext
```

### `apps/projects/`

```
models.py
  BookProject, OutlineVersion, OutlineNode
  ChapterReview, ChapterEditing
  LektoratSession, LektoratIssue
  PublishingProfile

views_html.py           — Projekt CRUD, Outline, ChapterWriter
views_review.py         — Review + Redaktion (manuell + KI)
views_lektorat.py       — Lektorat-Sessions (KI-Analyse pro Kapitel)
views_export.py         — Export (DOCX, PDF, Markdown)
views_import.py         — Markdown-Import → BookProject
views_publishing.py     — Klappentext, Keywords, Publishing-Profil
views_versions.py       — Snapshot-Verwaltung
```

## Datenfluss: Welt generieren

```
User → POST /welten/generate/
  └ WorldGenerateView.post()
    └ WorldBuilderService.generate_world(project_id, genre, ...)
        └ authoringfw.WorldContext → Kontext-String
        └ LLMRouter.completion("world_generate", messages)
            └ iil-aifw → AIActionType(world_generate) → LiteLLM
        └ _parse_world_response() → WorldBuildResult
    └ WorldBuilderService.save_to_weltenhub(result)
        └ weltenfw.get_client().worlds.create(WorldCreateInput(...))
        └ → WeltenHub REST API → UUID zurück
    └ WorldBuilderService.link_to_project(project_id, world_id)
        └ ProjectWorldLink.get_or_create()
  └ redirect(„welten/“)
```

## Deployment

| Branch | Umgebung | Trigger |
|--------|----------|---------|
| `develop` | Staging (staging.writing.iil.pet) | push auf develop |
| `main` | — | kein automatischer Deploy |
| `main` + workflow_dispatch | Production (writing.iil.pet) | NUR explizit |

**Regel:** Änderungen immer über `develop` auf Staging testen — Production NUR auf explizite Anweisung.

## Migrationen

```
worlds:
  0001_initial              — World (Legacy)
  0002_projektlinks         — ProjectWorldLink, ProjectCharacterLink
  0003_location_scene_links — ProjectLocationLink, ProjectSceneLink
```
