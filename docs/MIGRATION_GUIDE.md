# Writing Hub — Datenmigrations-Anleitung

## 1. Migrations ausführen

```bash
python manage.py migrate
```

Aktuelle Migration-Struktur `worlds`:
- `0001_initial` — World (Legacy)
- `0002_projektlinks` — `ProjectWorldLink`, `ProjectCharacterLink`
- `0003_location_scene_links` — `ProjectLocationLink`, `ProjectSceneLink`

## 2. Lookup-Daten seeden

**Pflicht — muss vor erster Nutzung ausgeführt werden:**

```bash
python manage.py seed_all
# Orchestriert:
#   loaddata fixtures/initial_lookups.json   (idempotent)
#   loaddata fixtures/initial_quality.json   (idempotent)
#   setup_aifw_actions                       (idempotent)
```

Oder einzeln:

```bash
python manage.py seed_quality_gate_decisions
python manage.py seed_quality_dimensions
```

## 3. WeltenHub-Konfiguration

In `.env` müssen gesetzt sein:

```env
WELTENHUB_URL=https://weltenhub.iil.pet
WELTENHUB_TOKEN=<service-token>
```

`iil-weltenfw[django]` liest diese Variablen automatisch und stellt
`weltenfw.django.get_client()` bereit.

## 4. Verifikation

```python
# writing-hub Shell:
from apps.worlds.models import ProjectWorldLink, ProjectCharacterLink
from apps.worlds.models import ProjectLocationLink, ProjectSceneLink
print(f'World-Links:     {ProjectWorldLink.objects.count()}')
print(f'Char-Links:      {ProjectCharacterLink.objects.count()}')
print(f'Location-Links:  {ProjectLocationLink.objects.count()}')
print(f'Scene-Links:     {ProjectSceneLink.objects.count()}')

# WeltenHub-Verbindung testen:
from weltenfw.django import get_client
client = get_client()
print(client.worlds.list())
```

## 5. API-Endpunkte

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/health/` | GET | Health-Check |
| `/welten/` | GET | Welten-Übersicht (HTML) |
| `/welten/<pk>/` | GET | Welt-Detail mit Charakteren + Orten (HTML) |
| `/welten/generate/` | POST | Welt generieren (LLM → WeltenHub) |
| `/welten/<pk>/characters/generate/` | POST | Charaktere generieren |
| `/welten/<pk>/locations/generate/` | POST | Orte generieren |
| `/api/worlds/` | GET/POST | Welten REST API |
| `/api/worlds/<id>/characters/` | GET/POST | Charaktere REST API |
| `/ideen/` | GET | Ideen-Import Liste |
| `/ideen/studio/` | GET | Ideen-Studio Kreativagent |
| `/projects/import/` | GET/POST | Markdown-Import |
| `/autoren/<pk>/stil/` | GET | Style Lab |

## 6. Rollback

Alle Seeds verwenden `get_or_create` / `update_or_create` — vollständig idempotent.
Legacy-Daten werden nicht gelöscht.
