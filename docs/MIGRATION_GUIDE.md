# Writing Hub — Datenmigrations-Anleitung (ADR-083)

Dieses Dokument beschreibt die Schritte zur Datenmigration von `bfagent` nach `writing-hub`.

## Voraussetzungen

- bfagent läuft und ist erreichbar
- writing-hub deployed (Port 8095)
- PostgreSQL-Datenbanken bfagent_db und writing_hub_db sind verfügbar

## Schritt 1: Welten migrieren

In bfagent ausführen:

```bash
# Dry-run zuerst
python manage.py migrate_worlds_to_world_sst --dry-run

# Tatsächliche Migration
python manage.py migrate_worlds_to_world_sst
```

## Schritt 2: Charaktere migrieren

```bash
# Dry-run zuerst
python manage.py migrate_characters_to_world_sst --dry-run

# Tatsächliche Migration
python manage.py migrate_characters_to_world_sst
```

## Schritt 3: Einzelnes Projekt migrieren (Test)

```bash
python manage.py migrate_worlds_to_world_sst --project-id 42 --dry-run
python manage.py migrate_characters_to_world_sst --project-id 42 --dry-run
```

## Schritt 4: Verifikation

In bfagent-Shell:

```python
from apps.writing_hub.models_world import WorldCharacter, World
print(f'WorldCharacter: {WorldCharacter.objects.count()}')
print(f'World (SSoT): {World.objects.count()}')
```

## Rollback

Da `get_or_create` verwendet wird und Legacy-Daten nicht gelöscht werden,
ist kein Rollback notwendig. Die Legacy-Tabellen (`characters`, `worlds`)
bleiben vollständig erhalten.

## API-Schnittstelle bfagent → writing-hub

Nach dem Deployment von writing-hub ist der Health-Check erreichbar:

```bash
curl https://writing.bfagent.iil.pet/api/v1/health/
# {"status": "ok", "service": "writing-hub", "version": "phase-3"}
```

## Endpunkte (Phase 3)

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/v1/health/` | GET | Health-Check |
| `/api/v1/worlds/` | GET | Welten des Users |
| `/api/v1/worlds/<id>/characters/` | GET | Charaktere einer Welt |
| `/api/v1/projects/<id>/outline/` | GET | Aktiver Outline |
| `/api/v1/idea-import/` | POST | Neuen Import starten |
