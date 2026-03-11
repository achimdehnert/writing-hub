# Systemübersicht (IT-Architektur)

## Platform-Kontext

Writing Hub ist Teil der **iil-Plattform** — einem Verbund von Django-Applikationen,
die über REST-APIs und gemeinsame PyPI-Packages kommunizieren.

```
┌────────────────────────────────────────────────┐
│                  iil-Plattform                     │
│                                                    │
│  ┌─────────────┐   ┌─────────────┐   ┌───────────┐  │
│  │ Writing Hub │   │ WeltenHub   │   │  DevHub   │  │
│  │ :8080        │   │ :8090        │   │ :8070     │  │
│  └─────────────┘   └─────────────┘   └───────────┘  │
│       │                    ↑                        │
│       └─────────────────┘                        │
│              REST API (iil-weltenfw)                 │
│                                                    │
│  ┌──────────────────────────────────────────┐  │
│  │     Shared iil PyPI Packages                  │  │
│  │  iil-aifw | iil-promptfw | iil-authoringfw     │  │
│  └──────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

## Tech-Stack

| Komponente | Technologie |
|------------|-------------|
| Backend | Django 4.2+ (Python 3.11) |
| Frontend | Django Templates + HTMX + Alpine.js |
| CSS | Tailwind CSS |
| API | Django REST Framework |
| Datenbank | PostgreSQL (Prod/Staging), SQLite (Lokal) |
| Cache/Queue | Redis + Celery |
| LLM | OpenAI GPT-4 via iil-aifw |
| WeltenHub-Client | iil-weltenfw |
| Containerisierung | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Reverse Proxy | Traefik |
| Doku | MkDocs Material |

## Infrastruktur

```
Internet
    |
    v
Traefik (Reverse Proxy + TLS)
    |
    +-- writing.iil.pet      -> Writing Hub (Django)
    +-- weltenhub.iil.pet    -> WeltenHub (Django)
    +-- devhub.iil.pet       -> DevHub (Django)

Jeder Service:
    Django Web
    Redis
    PostgreSQL
    Celery Worker
    Celery Beat
```

## Sicherheitsmodell

- Authentifizierung: Django Session Auth (Login erforderlich)
- API-Endpunkte: Token-basierte Authentifizierung (DRF TokenAuth)
- WeltenHub: Service-Token (`WELTENHUB_TOKEN`)
- LLM: API Keys nur in Umgebungsvariablen, nie im Code
- TLS: Automatisch via Traefik + Let's Encrypt

## Skalierung

- **Horizontal:** Mehrere Django-Web-Instanzen hinter Traefik
- **Async-Tasks:** Celery fuer LLM-Calls und Import-Verarbeitung
- **Cache:** Redis fuer Session und Task-Queue
- **DB:** PostgreSQL mit Connection Pooling
