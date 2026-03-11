# Datenmodell

## Entity-Relationship-Übersicht

```
User
 └── Author
      ├── WritingStyle (Style DNA)
      └── BookProject
            ├── OutlineVersion
            │    └── OutlineNode (Baum)
            │         └── ChapterContent
            ├── ReviewSession
            │    └── ReviewFeedback
            ├── LektoratSession
            │    └── LektoratIssue
            ├── PublishingProfile
            └── WeltenHub-Links (UUID-Referenzen)
                  ├── ProjectWorldLink
                  ├── ProjectCharacterLink
                  ├── ProjectLocationLink
                  └── ProjectSceneLink

CreativeSession (Ideen-Studio)
 └── BookIdea
      └── -> BookProject (bei Anlage)

IdeaImportDraft (Import-Staging)
 └── -> BookProject (bei Commit)
```

## Wichtige Design-Entscheidungen

### UUID als Primary Key

Alle Hauptmodelle verwenden `UUIDField(primary_key=True, default=uuid.uuid4)`:
- Vermeidet sequentielle IDs in URLs (Security)
- Erleichtert Datenbank-Merges und Migrationen
- Konsistent mit WeltenHub-IDs

### WeltenHub-Links als separate Tabellen

Die vier Link-Modelle (`ProjectWorldLink`, etc.) sind bewusst separate Tabellen:
- Klare Trennung zwischen lokalem Zustand und externen Referenzen
- `unique_together` verhindert Duplikate
- Einfaches Aufraeumen bei WeltenHub-Disconnects

### JSONField fuer Listen

`WritingStyle` nutzt `JSONField` fuer `do_list`, `dont_list`, `taboo_list`, `signature_moves`:
- Flexibel erweiterbar ohne Migration
- Kompatibel mit SQLite (lokal) und PostgreSQL (Prod)
- Kein `django.contrib.postgres.fields.ArrayField` (SQLite-inkompatibel)

## Migrations-Reihenfolge

```
worlds 0001_initial
  |
worlds 0002_projektlinks         (ProjectWorldLink, ProjectCharacterLink)
  |     depends: projects 0013
worlds 0003_location_scene_links (ProjectLocationLink, ProjectSceneLink)
        depends: projects 0013
```

## Datenbank-Tabellen (Worlds-App)

| Tabelle | Inhalt |
|---------|--------|
| `wh_project_world_links` | Projekt <-> WeltenHub-Welt |
| `wh_project_character_links` | Projekt <-> WeltenHub-Charakter |
| `wh_project_location_links` | Projekt <-> WeltenHub-Ort |
| `wh_project_scene_links` | Projekt <-> WeltenHub-Szene |
