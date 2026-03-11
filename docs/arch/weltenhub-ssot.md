# WeltenHub als Single Source of Truth (SSoT)

## Grundprinzip

> **WeltenHub ist die alleinige Wahrheitsquelle fuer Weltendaten.**
> Writing Hub speichert keine Kopien von Welten, Charakteren, Orten oder Szenen.
> Stattdessen werden nur UUID-Referenzen gespeichert.

## Datentrennung

| Datentyp | Gespeichert in | Zugriff via |
|----------|---------------|-------------|
| Welten (World) | WeltenHub | `iil-weltenfw` |
| Charaktere (Character) | WeltenHub | `iil-weltenfw` |
| Orte (Location) | WeltenHub | `iil-weltenfw` |
| Szenen (Scene) | WeltenHub | `iil-weltenfw` |
| Buchprojekte | Writing Hub | Django ORM |
| Kapitelinhalte | Writing Hub | Django ORM |
| Stilregeln | Writing Hub | Django ORM |
| Verknüpfungen | Writing Hub | Django ORM |

## Datenfluss: Welt generieren

```
[User klickt "Welt generieren"]
        |
        v
[WorldBuilderService.generate_and_save()]
        |
        +-- [LLMRouter.chat("world_generate")] -> LLM-API
        |         |
        |         v
        |   JSON-Response (Name, Beschreibung, ...)
        |
        +-- [authoringfw.WorldCreateInput] (Validierung)
        |
        +-- [weltenfw.client.worlds.create()] -> WeltenHub-API
        |         |
        |         v
        |   {id: "uuid-der-welt", ...}
        |
        +-- [ProjectWorldLink.objects.create(
        |       project=project,
        |       weltenhub_world_id=new_world.id
        |   )]
        |
        v
[Response: Link + WeltenHub-URL]
```

## Datenfluss: WeltenHub-Daten lesen

```python
from weltenfw.django import get_client
from apps.worlds.models import ProjectWorldLink

# Link laden
link = ProjectWorldLink.objects.get(project=project)

# Live-Daten aus WeltenHub
client = get_client()
world = client.worlds.get(link.weltenhub_world_id)
characters = client.characters.list(world=str(link.weltenhub_world_id))
locations = client.locations.list(world=str(link.weltenhub_world_id))
```

## Konsistenz-Modell

### Eventual Consistency

Da Writing Hub keine Kopien speichert, gibt es kein Synchronisierungs-Problem.
Jeder Lesezugriff liefert den aktuellen WeltenHub-Stand.

### Ausfall-Verhalten

Bei WeltenHub-Unavailability:
- Lese-Fehler werden im View gefangen und als leere Liste behandelt
- Link-Daten (UUIDs, Notes) sind weiterhin lesbar
- Generierung ist nicht möglich (explizite Fehlermeldung)

```python
try:
    characters = client.characters.list(world=str(world_id))
except Exception:
    characters = []  # Graceful Degradation
```

## WeltenHub-Konfiguration

```python
# settings/base.py
WELTENHUB_URL = env("WELTENHUB_URL", default="https://weltenhub.iil.pet")
WELTENHUB_TOKEN = env("WELTENHUB_TOKEN")
```

Der `weltenfw`-Client liest diese automatisch:
```python
from weltenfw.django import get_client  # kein explizites Setup noetig
```

## Entity-Lifecycle

```
GENERIERUNG:
  Writing Hub (KI) -> authoringfw-Schema -> WeltenHub (REST) -> UUID zurueck
  -> ProjectXxxLink(weltenhub_xxx_id=uuid) in Writing Hub

LESEN:
  ProjectXxxLink.weltenhub_xxx_id -> weltenfw.client.xxx.get(uuid)

LOESCHEN:
  ProjectXxxLink loeschen -> WeltenHub unveraendert (SSoT bleibt)

MODIFIZIEREN:
  Direkt in WeltenHub (weltenhub.iil.pet) -> Writing Hub sieht Aenderung sofort
```
