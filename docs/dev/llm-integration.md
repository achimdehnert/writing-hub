# LLM-Integration

## Architektur-Prinzip

```
View/Service
    |
    v
iil-aifw (LLMRouter)     <-- Abstraktionsschicht
    |
    v
iil-promptfw             <-- Template-Rendering
    |
    v
LLM-Backend (OpenAI / Azure / iil-intern)
```

## LLMRouter einrichten

```python
from aifw import LLMRouter

router = LLMRouter()  # liest Konfiguration aus Settings/Env
```

Konfigurationsquellen (in Prioritaetsreihenfolge):
1. Django Settings (`AIFW_BASE_URL`, `AIFW_API_KEY`)
2. Umgebungsvariablen (`OPENAI_API_KEY`)
3. Package-Defaults

## Typischer Service-Aufbau

```python
from aifw import LLMRouter
from promptfw import PromptStack
import json

class MyService:
    def __init__(self):
        self.router = LLMRouter()
        self._stack = None

    @property
    def stack(self):
        if self._stack is None:
            try:
                from promptfw import PromptStack
                self._stack = PromptStack()
            except Exception:
                pass
        return self._stack

    def generate_something(self, context: str) -> dict:
        messages = self._build_messages(context)
        response = self.router.chat(
            messages=messages,
            action_code="my_action",
            temperature=0.7,
        )
        return self._parse_response(response.content)

    def _build_messages(self, context: str) -> list[dict]:
        if self.stack and self.stack.has_template("my_template"):
            return self.stack.render_to_messages("my_template", context=context)
        return [
            {"role": "system", "content": "System-Prompt..."},
            {"role": "user", "content": f"Kontext: {context}"},
        ]

    def _parse_response(self, content: str) -> dict:
        # JSON aus Response extrahieren
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content.strip())
        except json.JSONDecodeError:
            return {"raw": content}
```

## JSON-Parsing-Pattern

Da LLMs haeufig JSON in Markdown-Codeblöcken zurueckgeben:

```python
def _extract_json(content: str) -> dict | list:
    """Extrahiert JSON aus LLM-Response (mit oder ohne ```json Block)."""
    text = content.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return json.loads(text)
```

## Fehlerbehandlung

Immer mit Fallback:

```python
try:
    result = self.router.chat(messages=messages, action_code="...", ...)
    data = _extract_json(result.content)
except Exception as e:
    logger.warning("LLM-Fehler: %s", e)
    data = {}  # oder sinnvoller Default
```

## Temperatur-Empfehlungen

| Aufgabe | Temperatur |
|---------|------------|
| Sachliche Analyse (Lektorat) | 0.3 |
| Struktur-Generierung (Outline) | 0.5 |
| Charakter-Generierung | 0.7 |
| Kreatives Brainstorming | 0.8-0.9 |
| Freies Schreiben | 0.8 |
