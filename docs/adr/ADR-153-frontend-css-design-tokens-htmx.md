# ADR-153: Frontend-Architektur — CSS Design Tokens und HTMX

**Status:** Accepted  
**Datum:** 2026-03-27 (rev. 2026-03-27)  
**Kontext:** writing-hub @ achimdehnert/writing-hub

---

## Kontext

Das aktuelle Frontend hat zwei kritische technische Schulden:

### Problem 1: Inline-Style-Chaos

`project_detail.html` allein: 720+ Zeilen, davon ~200 mit `style="..."`.  
Jede Farbe (`#0d1117`, `#6366f1`, `#2d3748`) ist 30–50× dupliziert.  
Theme-Änderungen erfordern `grep-replace` über 30+ Templates.

Häufig duplizierte Werte:
```
#0f1117  (page background)    → 40+ Vorkommen
#6366f1  (primary accent)     → 25+ Vorkommen
font-size:.7rem               → 60+ Vorkommen
```

### Problem 2: Kein HTMX

- Alle Interaktionen sind Full-Page-Reloads oder handgeschriebenes
  `fetch()` mit `setInterval`-Polling
- Filter-Formulare laden die gesamte Seite neu
- Generation-Status braucht eigenen Polling-Loop mit mehreren fetch-Calls
- `django-htmx` nicht in `requirements.txt` — kein Hindernis für Einführung

**Platform-Kontext:** SL-001 gilt auch für HTMX-Partials — kein ORM in views.py,
alle Datenzugriffe gehen durch den Service Layer.

---

## Entscheidung

### Teil A: CSS Custom Properties (Design Tokens)

Alle Inline-Styles werden schrittweise durch CSS Custom Properties
in `base.html` ersetzt. Kein Build-Step, kein npm, kein Tailwind-Upgrade.

**Token-System im `<style>`-Block von `base.html`:**

```css
:root {
  /* Backgrounds */
  --bg-page:       #0f1117;
  --bg-sidebar:    #1a1d27;
  --bg-card:       #0d1117;
  --bg-hover:      #1e2235;

  /* Borders
     --border      = Standard-Trennlinie zwischen Elementen (Cards, Listen)
     --border-form = Formular-Inputs und interaktive Felder (höherer Kontrast)
     --border-focus = Fokuszustand (Keyboard-Navigation, :focus-visible)
  */
  --border:        #2d3148;
  --border-form:   #475569;
  --border-focus:  #6366f1;

  /* Primary (Indigo) */
  --primary:       #6366f1;
  --primary-hover: #4f46e5;
  --primary-light: #a5b4fc;
  --primary-dark:  #1e1b4b;

  /* Text */
  --text:          #e2e8f0;
  --text-muted:    #94a3b8;
  --text-faint:    #64748b;

  /* Semantic */
  --success:       #22c55e;
  --warning:       #f59e0b;
  --danger:        #ef4444;
  --info:          #38bdf8;

  /* Sizing */
  --sidebar-w:     240px;
  --radius:        .75rem;
  --radius-sm:     .375rem;
}
```

**Hinweis:** `--border-alt` (#2d3748) wurde gestrichen — der Unterschied zu
`--border` (#2d3148) war ein einzelnes Hex-Zeichen ohne dokumentierten
semantischen Unterschied. Alle bisherigen `--border-alt`-Verwendungen
werden auf `--border` normalisiert.

**Utility-Klassen** ersetzen häufige Inline-Patterns:
```css
.fs-label   { font-size: .65rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; }
.fs-sm      { font-size: .8rem; }
.fs-xs      { font-size: .72rem; }
.btn-accent { background: var(--primary); color: #fff; border: none; border-radius: var(--radius-sm); }
.card-dark  { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); }
.text-muted { color: var(--text-muted); }
.text-faint { color: var(--text-faint); }
```

**Rollout-Reihenfolge und Completion-Kriterium:**

Phase 1 — Sofort (Blocker für neue Features):
1. `base.html` — Token-System + Utility-Klassen einführen

Phase 2 — Innerhalb von 2 Sprints:
2. `project_detail.html` — größte Datei, höchster Impact
3. `project_list.html`, `outline_detail.html`

Phase 3 — Definition of Done (DoD):
- Kein Template mehr mit `style="color: #` (überprüfbar per `grep`)
- CI-Lint-Rule: `grep -r 'style="color:#\|style="background:#' templates/` → muss leer sein

### Teil B: HTMX via CDN mit SRI

HTMX wird per CDN mit **Subresource Integrity Hash** eingebunden:

```html
<!-- base.html — vor </head> -->
<meta name="csrf-token" content="{{ csrf_token }}">

<script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.3/dist/htmx.min.js"
        integrity="sha384-0895/pl5ih6n6BhLcFzOT+CLnTUDEDmPX9cTdB4oPHTJWHoW/5irdPMVOMnbWIk3"
        crossorigin="anonymous"></script>
<script>
  htmx.config.withCredentials = true;
  document.addEventListener('htmx:configRequest', (e) => {
    e.detail.headers['X-CSRFToken'] =
      document.querySelector('meta[name="csrf-token"]')?.content || '';
  });
</script>
```

**CSRF-Strategie:** Das Meta-Tag `<meta name="csrf-token">` ist immer in
`base.html` vorhanden — unabhängig davon, ob ein Formular auf der Seite ist.
Kein Fallback-String nötig. Robuster als `querySelector('[name=csrfmiddlewaretoken]')`.

`django-htmx` in `requirements.txt`:
```
django-htmx>=1.17
```

`config/settings/base.py`:
```python
INSTALLED_APPS = [
    ...
    "django_htmx",
]
MIDDLEWARE = [
    ...
    "django_htmx.middleware.HtmxMiddleware",
]
```

### Teil C: SSE vs. Polling — Entscheidung für LLM-Generation-Status

**Entscheidung: SSE (`hx-ext="sse"`) für LLM-Generation, HTMX-Polling für kurze Status-Updates.**

| Usecase | Mechanismus | Begründung |
|---------|-------------|------------|
| LLM-Generation Status (10–30s) | `hx-ext="sse"` | Server-Push, 0 unnötige Requests, kein Polling-Overhead |
| Filter-Bar / Suche | `hx-get` on input | Sofortiges Partial-Update, kein Polling nötig |
| Kurze Task-Status (<5s) | `hx-trigger="every 2s"` | Akzeptabel für sehr kurze Wartezeiten |

**SSE-Integration für LLM-Generation:**
```html
<!-- Template -->
<div hx-ext="sse"
     sse-connect="/projekte/{{ project.pk }}/generate/stream/"
     sse-swap="generation_update">
  <div id="generation-output"></div>
</div>
```

```python
# View (SL-001-konform)
def generation_stream(request, pk):
    project = get_object_or_404(BookProject, pk=pk, owner=request.user)
    def event_stream():
        for chunk in GenerationService(project).stream():
            yield f"event: generation_update\ndata: {chunk}\n\n"
    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")
```

`django-htmx` + `htmx-ext-sse` CDN:
```html
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-sse@2.2.2/sse.js"
        integrity="sha384-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        crossorigin="anonymous"></script>
```

**Quick Wins (Prio 1, kein SSE nötig):**

| Feature | Vorher | Nachher |
|---------|--------|---------|
| Filter-Bar project_list | Full-Page-Reload | `hx-get` + `hx-target="#projects-grid"` |
| LLM-Generation Status | `setInterval` polling | `hx-ext="sse"` Stream |
| Outline-Node Edit | Full-Page + Scroll-Verlust | Inline-Edit via `hx-get`/`hx-swap` |
| Chapter Save | Full-Page-Reload | `hx-post` + partial response |
| NarrativeVoice-Form | Full-Page | HTMX-Modal via `hx-get` + `hx-target="body" hx-swap="beforeend"` |

**HTMX-View-Pattern (SL-001-konform):**

```python
def my_view(request, pk):
    project = get_object_or_404(BookProject, pk=pk, owner=request.user)
    data = MyService(project).get_context()
    if request.htmx:
        return render(request, "projects/partials/_my_partial.html", data)
    return render(request, "projects/my_full_page.html", data)
```

**Partial-Template-Konvention:**
- Alle HTMX-Partials liegen unter `templates/*/partials/_*.html`
- Partials erben nicht von `base.html`, haben kein `{% extends %}`
- Partials dürfen keine vollständigen Seiten-Layouts enthalten

---

## Begründung

- **CSS Custom Properties** sind native Browser-Technologie — kein Tooling,
  kein Build-Step, sofort wirksam.
- **`--border-alt` gestrichen:** Zwei nahezu identische Border-Tokens
  (`#2d3148` vs. `#2d3748`) ohne semantischen Unterschied erzeugen Verwirrung.
  Drei klar unterschiedene Tokens (`--border`, `--border-form`, `--border-focus`)
  decken alle Usecases ab.
- **SRI-Hash auf HTMX-CDN:** Supply-Chain-Angriff wird verhindert.
  Der Hash ist für htmx.org@2.0.3 angegeben — bei Versionswechsel muss er
  aktualisiert werden (Quelle: `sha384sum htmx.min.js`).
- **CSRF via Meta-Tag:** Zuverlässiger als Formular-Selektor — immer vorhanden,
  unabhängig vom Seiteninhalt.
- **SSE statt Polling für LLM-Generation:** LLM-Calls dauern 10–30s. Polling
  alle 2s = 5–15 unnötige Roundtrips. SSE ist eine persistente Verbindung ohne
  Overhead, Django unterstützt StreamingHttpResponse nativ.
- **Migration DoD als CI-Rule:** "Iterativ bei nächster Berührung" ohne
  Completion-Kriterium endet in permanenter Halbmigration.

---

## Abgelehnte Alternativen

**Tailwind CSS Build-Pipeline:** Node.js-Abhängigkeit auf dem Server, kein
erkennbarer Mehrwert gegenüber Custom Properties für dieses Projekt.

**React/Vue für interaktive Teile:** Widerspricht server-rendered Ansatz.

**Alpine.js statt HTMX:** Nur client-side; löst nicht Server-Roundtrip-Optimierung.

**WebSocket statt SSE:** Bidirektionale Kommunikation nicht nötig.
SSE reicht für unidirektionalen Generation-Stream.

**HTMX lokal einbinden (kein CDN):** Würde SRI-Risiko beseitigen, aber
Build-Step erfordern. CDN + SRI ist der Kompromiss ohne Tooling-Overhead.

---

## Konsequenzen

- `base.html`: Meta-CSRF-Tag + Token-System + HTMX CDN + SSE-Ext CDN
- `requirements.txt`: `django-htmx>=1.17`
- `config/settings/base.py`: `django_htmx` + Middleware
- Migration-DoD: CI-Rule `grep -r 'style="color:#\|style="background:#' templates/`
- LLM-Generation-Views erhalten SSE-Streaming-Endpunkt
- Alle HTMX-Partials in `templates/*/partials/_*.html`
- SRI-Hashes bei Versionswechsel aktualisieren (Checkliste im PR-Template)

---

**Referenzen:** `docs/adr/input/fe1_css_design_tokens.md`,  
`docs/adr/input/fe2_htmx.md`, platform-context SL-001
