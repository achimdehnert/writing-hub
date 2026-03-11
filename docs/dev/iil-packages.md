# iil PyPI Packages

Writing Hub nutzt vier spezialisierte iil-Packages fuer KI- und WeltenHub-Integration.

## Package-Übersicht

| Package | Version | Zweck |
|---------|---------|-------|
| `iil-weltenfw` | `>=1.0` | WeltenHub REST-Client |
| `iil-aifw` | `>=1.0` | LLM-Router & Abstraktionsschicht |
| `iil-authoringfw` | `>=1.0` | Typisierte Authoring-Schemas |
| `iil-promptfw` | `>=1.0` | Strukturierte Prompt-Templates |

---

## iil-weltenfw

REST-Client fuer den WeltenHub. Bietet Zugriff auf Welten, Charaktere, Orte, Szenen.

### Django-Integration

```python
from weltenfw.django import get_client

client = get_client()  # liest WELTENHUB_URL + WELTENHUB_TOKEN aus settings
```

### Entitaeten-Zugriff

```python
# Welt laden
world = client.worlds.get(world_id)           # -> World-Objekt
worlds = client.worlds.list(owner=user_id)    # -> List[World]

# Charakter laden
char = client.characters.get(char_id)
chars = client.characters.list(world=world_id)  # Gefiltert nach Welt!

# Ort laden
loc = client.locations.get(loc_id)
locs = client.locations.list(world=world_id)

# Szene laden
scene = client.scenes.get(scene_id)
```

### Entitaeten erstellen

```python
from authoringfw.schemas import WorldCreateInput, CharacterCreateInput

# Welt erstellen
new_world = client.worlds.create(WorldCreateInput(
    name="Aethoria",
    description="Ein magisches Koenigreich...",
    ...
))

# Charakter erstellen
new_char = client.characters.create(CharacterCreateInput(
    world_id=world_id,
    name="Lyra",
    ...
))
```

### Wichtiger Hinweis: Filterung

Immer `list(world=world_id)` statt `iter_all()` verwenden:

```python
# RICHTIG - gefilterte API-Abfrage:
chars = client.characters.list(world=str(world_id))

# FALSCH - laedt alle Charaktere aller Welten:
all_chars = list(client.characters.iter_all())
```

---

## iil-aifw

LLM-Router mit Abstraktion ueber verschiedene Modelle (OpenAI, Azure, iil-intern).

### Grundnutzung

```python
from aifw import LLMRouter

router = LLMRouter()
response = router.chat(
    messages=[
        {"role": "system", "content": "Du bist ein Autor..."},
        {"role": "user", "content": "Generiere 5 Buchideen..."},
    ],
    action_code="idea_generate",  # fuer Logging & Routing
    temperature=0.8,
)
text = response.content
```

### Action Codes

Jeder LLM-Call hat einen `action_code` fuer Logging und Routing:

| Action Code | Verwendung |
|-------------|------------|
| `idea_extract` | Ideen aus Dokumenten extrahieren |
| `idea_brainstorm` | Buchideen brainstormen |
| `idea_refine` | Idee verfeinern |
| `idea_premise` | Premise generieren |
| `world_generate` | Welt generieren |
| `character_generate` | Charaktere generieren |
| `location_generate` | Orte generieren |
| `style_extract` | Stilregeln extrahieren |
| `chapter_write` | Kapitel schreiben |
| `outline_generate` | Outline generieren |
| `review_agent` | Review-Agenten |
| `lektorat_analyze` | Lektorat-Analyse |

---

## iil-promptfw

Strukturierte Prompt-Templates fuer konsistente LLM-Kommunikation.

### Grundnutzung

```python
from promptfw import PromptStack

stack = PromptStack()

# Template pruefen und rendern
if stack.has_template("character_generate"):
    messages = stack.render_to_messages(
        "character_generate",
        world_ctx=world_context,
        count=5,
        requirements="Protagonistin, weiblich",
    )
else:
    # Fallback: Inline-Prompt
    messages = [{"role": "user", "content": "..."}]
```

### Pattern: Template mit Fallback

Immer Template-Existenz pruefen und Fallback implementieren:

```python
try:
    from promptfw import PromptStack
    stack = PromptStack()
    if stack.has_template(template_name):
        return stack.render_to_messages(template_name, **kwargs)
except Exception:
    pass
# Fallback zu Inline-Prompt
return [{"role": "user", "content": inline_prompt}]
```

---

## iil-authoringfw

Typisierte Pydantic-Schemas fuer Authoring-Entitaeten.

### Verfuegbare Schemas

```python
from authoringfw.schemas import (
    WorldCreateInput,
    CharacterCreateInput,
    LocationCreateInput,
    SceneCreateInput,
)
```

### Verwendungsbeispiel

```python
from authoringfw.schemas import LocationCreateInput

location_input = LocationCreateInput(
    world_id=world_id,
    name="Silberwald",
    description="Ein mystischer Wald...",
    atmosphere="Geheimnisvoll, ruhig",
    significance="Hier beginnt die Reise",
)
new_location = client.locations.create(location_input)
```
