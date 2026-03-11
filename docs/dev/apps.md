# Apps & Modelle im Detail

## authors

### Modelle

#### `Author`
```
id          UUID (PK)
user        FK -> User
pen_name    CharField
bio         TextField
created_at  DateTimeField
```

#### `WritingStyle`
```
id                UUID (PK)
author            FK -> Author
name              CharField
description       TextField
do_list           JSONField (Liste von Strings)
dont_list         JSONField
taboo_list        JSONField
signature_moves   JSONField
created_at        DateTimeField
```

### Services

```python
# Stilregeln per KI extrahieren
from apps.authors.services import extract_style_rules
rules = extract_style_rules(source_text="Beispieltext...")
# -> dict mit do_list, dont_list, taboo_list, signature_moves

# Stil als Prompt-Kontext
from apps.authors.services import get_style_prompt_for_writing
prompt = get_style_prompt_for_writing(style)
```

---

## idea_import

### Modelle

#### `IdeaImportDraft`
Staging-Modell fuer KI-extrahierte Ideen aus hochgeladenen Dokumenten.
```
status: pending_review | committed | discarded
extracted_data: JSONField (characters, outline, premise, ...)
```

#### `CreativeSession`
```
owner       FK -> User
pheme       brainstorming | refining | done
thema       TextField
genre       CharField
tonalitaet  CharField
style       FK -> WritingStyle (optional)
```

#### `BookIdea`
```
session     FK -> CreativeSession
title       CharField
logline     TextField
rating      IntegerField (1-5)
refined     JSONField (Verfeinerungs-Details)
premise     TextField
```

---

## projects

### Kernmodelle

#### `BookProject`
```
id          UUID (PK)
author      FK -> Author
title       CharField
genre       CharField
description TextField
status      CharField
```

#### `OutlineNode`
```
project     FK -> BookProject
parent      FK -> self (nullable, Baum-Struktur)
title       CharField
summary     TextField
order       IntegerField
```

#### `ChapterContent`
```
node        FK -> OutlineNode
version     FK -> OutlineVersion
content     TextField
word_count  IntegerField
```

---

## worlds

### Link-Modelle (SSoT-Referenzen)

Alle Link-Modelle speichern nur UUIDs — die eigentlichen Daten liegen in WeltenHub.

#### `ProjectWorldLink`
```
project                FK -> BookProject
weltenhub_world_id     UUIDField (Index)
notes                  TextField
```

#### `ProjectCharacterLink`
```
project                    FK -> BookProject
weltenhub_character_id     UUIDField (Index)
role                       CharField (protagonist|antagonist|...)
notes                      TextField
```

#### `ProjectLocationLink`
```
project                    FK -> BookProject
weltenhub_location_id      UUIDField (Index)
notes                      TextField
```

#### `ProjectSceneLink`
```
project                FK -> BookProject
weltenhub_scene_id     UUIDField (Index)
outline_node           FK -> OutlineNode (optional)
notes                  TextField
```

### DB-Tabellen

| Modell | DB-Tabelle |
|--------|------------|
| ProjectWorldLink | `wh_project_world_links` |
| ProjectCharacterLink | `wh_project_character_links` |
| ProjectLocationLink | `wh_project_location_links` |
| ProjectSceneLink | `wh_project_scene_links` |
