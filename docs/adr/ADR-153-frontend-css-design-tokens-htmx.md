# ADR-153: Frontend-Architektur — CSS Design Tokens und HTMX

**Status:** Accepted  
**Datum:** 2026-03-27  
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

  /* Borders */
  --border:        #2d3148;
  --border-alt:    #2d3748;
  --border-form:   #475569;

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

**Utility-Klassen** ersetzen häufige Inline-Patterns:
```css
.fs-label  { font-size: .65rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; }
.fs-sm     { font-size: .8rem; }
.fs-xs     { font-size: .72rem; }
.btn-accent { background: var(--primary); color: #fff; border: none; border-radius: var(--radius-sm); }
.card-dark  { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); }
.text-muted { color: var(--text-muted); }
.text-faint { color: var(--text-faint); }
```

**Rollout-Reihenfolge (iterativ, kein Big Bang):**
1. `base.html` — Token-System einführen (einmalig, sofort wirksam)
2. `project_detail.html` — größte Datei, höchster Impact
3. Alle anderen Templates iterativ bei nächster Berührung

### Teil B: HTMX via CDN

HTMX wird per CDN eingebunden — kein pip, kein Build-Step:

```html
<!-- base.html, vor </head> -->
<script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.3/dist/htmx.min.js"
        crossorigin="anonymous"></script>
<script>
  document.addEventListener('htmx:configRequest', (e) => {
    e.detail.headers['X-CSRFToken'] = document.querySelector('[name=csrfmiddlewaretoken]')?.value
      || '{{ csrf_token }}';
  });
</script>
```

`django-htmx` in `requirements.txt` ergänzen:
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

**Quick Wins (Prio 1):**

| Feature | Vorher | Nachher |
|---------|--------|---------|
| Filter-Bar project_list | Full-Page-Reload | `hx-get` + `hx-target="#projects-grid"` |
| Generation-Status | `setInterval` polling | `hx-trigger="every 2s"` auf Status-Panel |
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
  kein Build-Step, sofort wirksam. Alle 40+ Vorkommen von `#0f1117`
  werden durch `var(--bg-page)` ersetzt — einmalige Änderung statt Grep-Replace.
- **HTMX via CDN** ist kein Architektur-Risiko: es ist eine Progressive-
  Enhancement-Library ohne Django-Kopplung. CDN-Einbindung ist legitimiert
  durch die geringe Bundle-Größe (~14kb gzip) und den fehlenden Build-Step.
- **Kein React, kein Vue:** Das Projekt ist server-rendered. HTMX ist
  die minimalste Erweiterung, die 80% der UX-Probleme löst.
- **SL-001 gilt für HTMX:** HTMX-Views sind reguläre Django-Views.
  Die Service-Layer-Regel gilt uneingeschränkt.

---

## Abgelehnte Alternativen

**Tailwind CSS Purge/Build-Pipeline einführen:** Zu viel Overhead für
ein Django-Projekt ohne JS-Build-Step. CSS Custom Properties lösen das
Problem ohne Tooling.

**React-Komponenten für interaktive Teile:** Widerspricht dem
server-rendered Ansatz und dem Ziel minimaler Komplexität.

**Alpine.js statt HTMX:** Alpine.js löst nur client-side Interaktivität,
nicht die Server-Roundtrip-Optimierung. HTMX adressiert beide Aspekte.

**django-tailwind:** Erfordert Node.js auf dem Server — zu viel Overhead
für den Benefit.

---

## Konsequenzen

- `base.html` erhält Token-System (einmalig, hoher Impact)
- `requirements.txt`: `django-htmx>=1.17` ergänzen
- `config/settings/base.py`: `django_htmx` in `INSTALLED_APPS` + Middleware
- Templates werden iterativ migriert — keine Big-Bang-Änderung
- Alle HTMX-Partials liegen in `templates/*/partials/_*.html`
- LLM-Coding-Regeln: HTMX-Views folgen SL-001 (Service Layer Pflicht)
- Drama-Dashboard (ADR-154) setzt HTMX für Lazy-Load voraus

---

**Referenzen:** `docs/adr/input/fe1_css_design_tokens.md`,  
`docs/adr/input/fe2_htmx.md`, platform-context SL-001
