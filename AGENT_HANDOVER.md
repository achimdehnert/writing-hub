# Writing Hub — Agent Handover

> Letzte Aktualisierung: 2026-04-01
> Status: Production (writing.iil.pet)

## Aktueller Stand

Writing Hub ist die zentrale Autorenplattform der iil-Plattform. Die App ist produktiv und wird aktiv genutzt.

### Letzte Änderungen

- **2026-04-01**: Session-Ende Auto-Sync
- **PostgreSQL 15** statt 16 (Production-Daten sind PG15-initialisiert)

### Bekannte Issues

_Keine bekannten Issues._

### Gelöste Issues (2026-04-01)

- ✅ Dockerfile `HEALTHCHECK` entfernt — jetzt nur in `docker-compose.prod.yml` (ADR-022)
- ✅ `requirements-test.txt` erstellt mit `platform-context[testing]>=0.3.1`

## Offene Tasks

_Keine offenen Tasks dokumentiert._

## Architektur-Entscheidungen

Siehe `docs/adr/` für alle ADRs. Wichtig:

1. **SSoT für Welten** — WeltenHub ist die einzige Quelle für Welten/Charaktere/Orte
2. **iil-Packages** — Alle LLM-Calls über `iil-aifw`, Prompts über `iil-promptfw`
3. **4-Ebenen-Romanstruktur** — ADR-150

## Deployment-Hinweise

```bash
# Deploy via /ship workflow
# Oder manuell:
git push origin main
# → CI/CD baut Image → Deploy auf 88.198.191.108:/opt/writing-hub
```

## Wichtige Dateien

| Datei | Zweck |
|-------|-------|
| `config/settings/production.py` | Production-Settings |
| `config/settings/test.py` | Test-Settings |
| `docker-compose.prod.yml` | Production Compose |
| `.ship.conf` | Deploy-Konfiguration |
| `docs/ARCHITECTURE.md` | Architektur-Übersicht |
| `docs/adr/ADR-INDEX.md` | ADR-Index |

## Nächste Schritte (Vorschläge)

1. `HEALTHCHECK` aus Dockerfile entfernen (ist bereits in Compose)
2. `requirements-test.txt` mit `platform-context[testing]` erstellen
3. Outline Repo-Steckbrief in Outline Wiki erstellen (ADR-145)

## Kontext für Cascade

Bei Arbeiten an writing-hub:
- **Immer** `docs/ARCHITECTURE.md` lesen für SSoT-Verständnis
- **Nie** lokale World/Character-Models erstellen — nur Links zu WeltenHub
- **LLM-Calls** immer über `LLMRouter.completion(action_code, messages)`
- **Prompts** immer über `PromptStack.render_to_messages()`
