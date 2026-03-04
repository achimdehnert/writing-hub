# Writing Hub — Datenmigrations-Anleitung (ADR-083)

Vollständige Setup-Reihenfolge nach Deployment von writing-hub.

## 1. Migrations ausführen

```bash
python manage.py migrate
```

## 2. Lookup-Daten seeden (writing-hub)

**Pflicht — muss vor erster Nutzung ausgeführt werden:**

```bash
# Quality Gate Entscheidungstypen (approve, review, revise, reject)
python manage.py seed_quality_gate_decisions

# Qualitätsdimensionen (style, genre, scene, serial_logic, pacing, dialogue)
python manage.py seed_quality_dimensions
```

## 3. Datenmigration aus bfagent

**In bfagent ausführen** (Produktionsdaten übertragen):

```bash
# Dry-run zuerst
python manage.py migrate_worlds_to_world_sst --dry-run
python manage.py migrate_characters_to_world_sst --dry-run

# Tatsächliche Migration
python manage.py migrate_worlds_to_world_sst
python manage.py migrate_characters_to_world_sst
```

### Einzelnes Projekt testen

```bash
python manage.py migrate_worlds_to_world_sst --project-id 42 --dry-run
python manage.py migrate_characters_to_world_sst --project-id 42 --dry-run
```

## 4. Verifikation

**In bfagent-Shell:**

```python
from apps.writing_hub.models_world import WorldCharacter, World
print(f'WorldCharacter: {WorldCharacter.objects.count()}')
print(f'World (SSoT): {World.objects.count()}')
```

**In writing-hub-Shell:**

```python
from apps.authoring.models import QualityDimension, GateDecisionType
print(f'Dimensionen: {QualityDimension.objects.filter(is_active=True).count()}')
print(f'Gate-Typen: {GateDecisionType.objects.count()}')
from apps.worlds.models import World, WorldCharacter
print(f'Welten: {World.objects.count()}')
print(f'Charaktere: {WorldCharacter.objects.count()}')
```

## 5. Rollback

Da `get_or_create` / `update_or_create` verwendet werden und Legacy-Daten
**nicht gelöscht** werden, ist kein Rollback notwendig. Die Legacy-Tabellen
(`characters`, `worlds`) in bfagent bleiben vollständig erhalten.

---

## API-Endpunkte (Phase 3)

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/health/` | GET | Health-Check (kein Auth) |
| `/api/v1/health/` | GET | API Health-Check |
| `/api/v1/worlds/` | GET | Welten des Users |
| `/api/v1/worlds/<id>/characters/` | GET | Charaktere einer Welt |
| `/api/v1/projects/<id>/outline/` | GET | Aktiver Outline |
| `/api/v1/idea-import/` | POST | Neuen Import starten |
| `/api/v1/authoring/projects/<id>/chapters/<ref>/write/` | POST | Kapitel async schreiben |
| `/api/v1/authoring/jobs/<job_id>/status/` | GET | Job-Status polling |
| `/api/v1/authoring/projects/<id>/chapters/<ref>/quality/` | GET/POST | Quality Score |

```bash
# Health-Check
curl https://writing.bfagent.iil.pet/health/
# {"status": "ok"}
```

---

## Seed-Reihenfolge (komplett)

```bash
python manage.py migrate
python manage.py seed_quality_gate_decisions
python manage.py seed_quality_dimensions
# Optional: Superuser anlegen
python manage.py createsuperuser
```
