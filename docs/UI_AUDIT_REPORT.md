# Writing Hub — UI Audit Report

**Datum:** 2026-04-18
**Branch:** `main` (HEAD: 86e036b + unstaged)
**Scope:** 7 editierte Templates, 8 Seiten getestet

---

## Geänderte Dateien

| Datei | Änderungen | Typ |
|-------|-----------|-----|
| `templates/base.html` | +33 / -3 | Global: Sidebar, Forms, Pagination, Mobile |
| `templates/projects/project_detail.html` | +143 / -120 | Buttons, Workflow-Links, Modals |
| `templates/projects/milestones.html` | +14 / -12 | Form-Kontrast, Button |
| `templates/projects/project_list.html` | +4 / -4 | Filter-Inputs |
| `templates/projects/project_list_partial.html` | +6 / -6 | Card-Title, Progress, Pagination |
| `templates/projects/template_list.html` | +3 / -3 | Hover, Badges, Input |
| `templates/projects/workflow.html` | +5 / -5 | Add-Item-Form, Phase-Glow |

**Summe:** 7 Dateien, +192 / -166 Zeilen

---

## Fixes (7 + Nachbesserungen)

| # | Fix | Beschreibung | Status |
|---|-----|-------------|--------|
| 1 | Base: Sidebar | Active-Link Indigo-Border + Icon-Farbe | ✅ |
| 2 | Base: Form Controls | Globale Dark-Theme-Styles für `.form-control`, `.form-select` | ✅ |
| 3 | Base: Pagination | Globale `.page-link` Dark-Theme-Styles | ✅ |
| 4 | Base: Mobile | Hamburger-Toggle, responsive Sidebar | ✅ |
| 5 | Base: Progress | `.progress` Track-Background `#1e2235` | ✅ |
| 6 | Project List | Card-Title-Farbe `#e2e8f0`, Progress min-width | ✅ |
| 7 | Project Detail | 16 Buttons → 4 Gruppen (Schreiben/Recherche/Qualität/Projekt) | ✅ |
| 8 | Project Detail | Alle `onclick=` → semantische `<a>` Tags (banned pattern) | ✅ |
| 9 | Project Detail | Modal-Forms: `bg-dark text-light` entfernt | ✅ |
| 10 | Workflow | Add-Item-Form auf allen Phasen, Active-Phase-Glow | ✅ |
| 11 | Milestones | Sichtbarer Titel, Label-Kontrast, prominenter Button | ✅ |
| 12 | Templates | Card-Hover-Effekt, Input-Kontrast, Branded Badges | ✅ |

---

## Test-Ergebnisse

### HTTP-Status (Playwright)

| Seite | URL | Status |
|-------|-----|--------|
| Project List | `/projekte/` | ✅ 200 |
| Project Detail | `/projekte/<uuid>/` | ✅ 200 |
| Workflow | `/projekte/<uuid>/workflow/` | ✅ 200 |
| Milestones | `/projekte/<uuid>/milestones/` | ✅ 200 |
| Templates | `/projekte/templates/` | ✅ 200 |
| Citations | `/projekte/<uuid>/citations/` | ✅ 200 |
| Chapter Writer | `/projekte/<uuid>/write/` | ✅ 200 |
| Login | `/accounts/login/` | ✅ 200 |

**Ergebnis: 8/8 Seiten HTTP 200**

### JS-Console-Errors

| Level | Count | Details |
|-------|-------|---------|
| Error | 0 | — |
| Warning | 0 | — |
| Network 404 | 1 | `favicon.ico` (pre-existing, kein UI-Problem) |

**Ergebnis: 0 JS-Errors**

### Link-Test (Project Detail — 40 Links)

| Kategorie | Count | Status |
|-----------|-------|--------|
| Quick-Action-Buttons | 14 | ✅ alle 200 |
| Workflow-Phase-Cards | 11 | ✅ alle 200 |
| Navigation (Sidebar) | 9 | ✅ alle 200 |
| Sonstige | 5 | ✅ alle 200 |
| Logout | 1 | ⚠️ 405 (erwartet — Django 5 POST-only) |

**Ergebnis: 39/40 Links OK (1× expected 405)**

### Template-Parsing

| Template | Status |
|----------|--------|
| `base.html` | ✅ |
| `projects/project_list.html` | ✅ |
| `projects/project_list_partial.html` | ✅ |
| `projects/project_detail.html` | ✅ |
| `projects/workflow.html` | ✅ |
| `projects/milestones.html` | ✅ |
| `projects/template_list.html` | ✅ |
| `projects/citations.html` | ✅ |
| `registration/login.html` | ✅ |

**Ergebnis: 9/9 Templates fehlerfrei**

### Banned Patterns (grep auf editierte Dateien)

| Pattern | Treffer in Scope |
|---------|-----------------|
| `onclick=` | 0 ✅ |
| `bg-dark text-light border-secondary` | 0 ✅ |

### Mobile (375px)

| Test | Status |
|------|--------|
| Hamburger-Button sichtbar | ✅ |
| Sidebar hidden by default | ✅ |
| Sidebar-Toggle funktioniert | ✅ |
| Content füllt volle Breite | ✅ |
| Cards stacken korrekt | ✅ |

---

## Nachbesserung 2026-04-20

| # | Fix | Beschreibung | Status |
|---|-----|-------------|--------|
| 13 | `bg-dark text-light border-secondary` | 31 Hits in 6 Templates entfernt (global CSS übernimmt) | ✅ |
| 14 | Favicon | SVG-Favicon erstellt + `{% static %}` Link in base.html | ✅ |

**Betroffene Dateien:**
- `templates/ideas/idea_upload.html` (3 Hits)
- `templates/outlines/outline_detail.html` (8 Hits)
- `templates/outlines/partials/node_row.html` (7 Hits)
- `templates/projects/drama_dashboard.html` (7 Hits)
- `templates/projects/versions.html` (2 Hits)
- `templates/series/series_form.html` (4 Hits)
- `templates/base.html` (Favicon-Link)
- `static/favicon.svg` (neu)

**`onclick=` Patterns:** Bereits in B3 plattformweit entfernt (0 Hits).

## Nachbesserung 2026-04-20 (B)

| # | Fix | Beschreibung | Status |
|---|-----|-------------|--------|
| 15 | Inline Event-Handler | 4× `onmouseover`/`onmouseout` → CSS `.card-hover-indigo` + `.paper-link` | ✅ |

**Betroffene Dateien:**
- `templates/base.html` (`.card-hover-indigo` CSS-Klasse hinzugefügt)
- `templates/projects/template_list.html` (1 Hit)
- `templates/projects/lektorat.html` (1 Hit)
- `templates/projects/peer_review.html` (1 Hit)
- `templates/projects/citations.html` (1 Hit in JS + `.paper-link` CSS)

**Ergebnis:** 0 inline Event-Handler (`onclick`, `onmouseover`, `onmouseout`, `onchange`, `onsubmit`, `onkeydown`) in allen Templates.

---

## Fazit

**COMPLETE ✅**

- 15 Fixes implementiert (7 geplant + 8 Nachbesserungen)
- 8/8 Seiten HTTP 200
- 0 JS-Errors
- 39/40 Links OK (1× expected)
- 9/9 Templates parsen
- 0 Banned Patterns (onclick, bg-dark text-light, inline handlers)
- Mobile-Support funktioniert
- Favicon vorhanden
