# Project Facts: writing-hub

> Auto-generiert von `platform/.github/scripts/push_project_facts.py`
> Letzte Aktualisierung: 2026-04-28 — bei Änderungen: `platform/gen-project-facts.yml` triggern

## Meta

- **Type**: `django`
- **GitHub**: `https://github.com/achimdehnert/writing-hub`
- **Branch**: `main` — push: `git push` (SSH-Key konfiguriert)

## Lokale Umgebung (Dev Desktop — adehnert)

- **Pfad**: `~/CascadeProjects/writing-hub` → `$GITHUB_DIR` = `~/CascadeProjects`
- **src_root**: `./` (root) — `manage.py` liegt dort
- **pythonpath**: `./`
- **Venv**: `~/CascadeProjects/writing-hub/.venv/bin/python`
- **MCP aktiv**: `mcp0_` = github · `mcp1_` = orchestrator

## Settings

- **Prod-Modul**: `config.settings.production`
- **Test-Modul**: `config.settings.test`
- **Testpfad**: `tests/`

## Stack

- **Django**: `5.x`
- **Python**: `3.12`
- **PostgreSQL**: `16`
- **HTMX installiert**: nein
- **HTMX-Detection**: `request.headers.get("HX-Request") == "true"`


## Apps

- `accounts`
- `accounts`
- `api`
- `api`
- `authoring`
- `authoring`
- `authors`
- `authors`
- `core`
- `core`
- `idea_import`
- `idea_import`
- `illustration`
- `illustration`
- `outlines`
- `outlines`
- `projects`
- `projects`
- `series`
- `series`
- `worlds`
- `worlds`

## Infrastruktur

- **Prod-URL**: `writing-hub.iil.pet`
- **Staging-URL**: `staging.writing-hub.iil.pet`
- **Port**: `8097`
- **Health-Endpoint**: `/livez/`
- **DB-Name**: `writing_hub`

## System (Hetzner Server)

- devuser hat **KEIN sudo-Passwort** → System-Pakete immer via SSH als root:
  ```bash
  ssh root@localhost "apt-get install -y <package>"
  ```
