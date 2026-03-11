# Tests

## Test-Stack

- **pytest** mit `pytest-django`
- **Coverage** via `pytest-cov`
- **Fixtures** fuer Testdaten
- **SQLite** fuer schnelle lokale Tests

## Tests ausfuehren

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=apps --cov-report=html

# Spezifische App
pytest apps/worlds/tests/

# Spezifischer Test
pytest apps/worlds/tests/test_services.py::TestWorldBuilderService::test_generate
```

## Test-Struktur

```
apps/
  worlds/
    tests/
      __init__.py
      test_models.py
      test_services.py
      test_views.py
```

## WeltenHub-Mocking

WeltenHub-Calls werden in Tests gemockt:

```python
from unittest.mock import patch, MagicMock

@patch("weltenfw.django.get_client")
def test_world_generation(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.worlds.create.return_value = MagicMock(
        id="550e8400-e29b-41d4-a716-446655440000",
        name="Testworld",
    )

    service = WorldBuilderService()
    result = service.generate_and_save(project=project, ...)

    assert result.world_name == "Testworld"
    mock_client.worlds.create.assert_called_once()
```

## LLM-Mocking

```python
@patch("aifw.LLMRouter.chat")
def test_idea_generation(mock_chat):
    mock_chat.return_value = MagicMock(
        content='{"title": "Testtitel", "logline": "Testlogline"}'
    )
    # ... Test-Code
```

## CI/CD-Integration

Tests laufen automatisch bei jedem Push via GitHub Actions.
Siehe `.github/workflows/ci-cd.yml`.

## Lint

```bash
# Ruff Lint
ruff check apps/

# Ruff Format Check
ruff format --check apps/

# Auto-Fix
ruff check --fix apps/
```
